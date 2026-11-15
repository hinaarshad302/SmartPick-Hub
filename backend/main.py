import os
import hashlib
import secrets
import html
from urllib.parse import urlsplit
from pathlib import Path
from datetime import datetime, timedelta, timezone

import requests
from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client

PROJECT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT / ".env", override=True)
def validate_https_url(value: str, setting_name: str, allow_path: bool = False) -> None:
    parsed = urlsplit(value)
    try:
        parsed.port
    except ValueError as exc:
        raise RuntimeError(f"{setting_name} contains an invalid port.") from exc

    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or (not allow_path and parsed.path not in ("", "/"))
    ):
        raise RuntimeError(
            f"{setting_name} must be a valid HTTPS "
            + ("website URL." if allow_path else "origin URL.")
        )


FRONTEND_URL = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
if FRONTEND_URL:
    validate_https_url(FRONTEND_URL, "FRONTEND_URL", allow_path=True)

FRONTEND_ORIGINS = [
    f"{urlsplit(FRONTEND_URL).scheme}://{urlsplit(FRONTEND_URL).netloc}"
] if FRONTEND_URL else []

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "").strip()
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")

if SUPABASE_URL:
    validate_https_url(SUPABASE_URL, "SUPABASE_URL")
if PUBLIC_API_URL:
    validate_https_url(PUBLIC_API_URL, "PUBLIC_API_URL")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError("Supabase configuration is missing.")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

app = FastAPI(
    title="SmartPick Hub API",
    description="Backend API for SmartPick Hub",
    version="1.0.0"
)



# Restrict browser newsletter requests to the SmartPick Hub preview.
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
class AssistantSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1200)


class NewsletterSignup(BaseModel):
    email: EmailStr = Field(max_length=254)


class ConfirmationRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class UnsubscribeRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)


@app.get("/")
def home():
    return {
        "message": "Welcome to SmartPick Hub API",
        "status": "running"
    }





@app.get("/out/{product_id}", include_in_schema=False)
def outbound_product_click(product_id: str):
    """Record a minimal product-click event, then redirect to its configured retailer."""
    if not product_id or len(product_id) > 120:
        raise HTTPException(status_code=404, detail="Product not found.")

    product = None

    # Prefer the central database record when one exists, so admin changes
    # and unpublished status are respected. The reviewed JSON catalogue is
    # the fallback for products not yet imported into Supabase.
    try:
        result = (
            supabase.table("products")
            .select("id,status,affiliate_url,product_url")
            .eq("id", product_id)
            .limit(1)
            .execute()
        )
        if result.data:
            product = result.data[0]
            if product.get("status") != "published":
                raise HTTPException(status_code=404, detail="Product not found.")
    except HTTPException:
        raise
    except Exception:
        product = None

    if product is None:
        catalogue_path = PROJECT / "products.json"
        try:
            import json
            catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
            product = next(
                (item for item in catalogue
                 if isinstance(item, dict)
                 and item.get("id") == product_id
                 and item.get("status") == "published"),
                None,
            )
        except (OSError, ValueError, TypeError):
            product = None

    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    affiliate_url = product.get("affiliate_url") or product.get("affiliateUrl") or ""
    retailer_url = product.get("product_url") or product.get("productUrl") or ""
    destination = affiliate_url or retailer_url
    parsed_destination = urlsplit(destination)

    try:
        parsed_destination.port
    except ValueError:
        raise HTTPException(status_code=404, detail="Product destination is invalid.")

    if (
        parsed_destination.scheme != "https"
        or not parsed_destination.hostname
        or parsed_destination.username
        or parsed_destination.password
    ):
        raise HTTPException(status_code=404, detail="Product destination is invalid.")

    # Do not collect IP addresses, user agents, account IDs, or referrers.
    # A failed analytics insert must never prevent a visitor from reaching
    # the retailer; the redirect remains useful if tracking is not configured.
    try:
        supabase.table("affiliate_click_events").insert({
            "product_id": product_id,
            "destination_type": "affiliate" if affiliate_url else "retailer",
        }).execute()
    except Exception:
        pass

    return RedirectResponse(url=destination, status_code=302)


@app.get("/health")
def health_check():
    try:
        supabase.table("newsletter_subscribers") \
            .select("id").limit(1).execute()

        return {
            "api": "working",
            "database": "connected",
            "status": "healthy"
        }
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed."
        )


@app.post("/assistant/search")
def assistant_search(request: AssistantSearchRequest):
    """Generate bilingual shopping guidance using Gemini; API credentials stay server-side."""
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

    if not gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="SmartPick AI is not configured yet. Add GEMINI_API_KEY to the backend environment."
        )

    query = request.query.strip()
    if len(query) < 2:
        raise HTTPException(status_code=422, detail="Please enter a longer question.")

    system_instruction = (
        "You are SmartPick AI, a helpful bilingual shopping and product-discovery "
        "assistant for Pakistan and international users. Understand English, Urdu, "
        "and Roman Urdu. Give clear, practical, neutral buying guidance. Ask a short "
        "follow-up when budget, country, or use case is essential. Do not invent live "
        "prices, discounts, stock, ratings, product specifications, reviews, or "
        "affiliate availability. If verified product data is not supplied, say so "
        "and explain what the user should verify with the seller. Do not claim that "
        "you searched live retailer listings. Keep answers structured and concise."
    )

    try:
        with genai.Client(api_key=gemini_api_key) as client:
            response = client.models.generate_content(
                model=gemini_model,
                contents=query,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.4,
                    "max_output_tokens": 1024,
                },
            )
        answer = response.text
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Gemini returned an empty answer.")
        return {"success": True, "answer": answer.strip()}
    except Exception:
        # Do not expose provider details, request metadata, or credentials to visitors.
        raise HTTPException(
            status_code=502,
            detail="SmartPick AI could not get a response right now. Please try again later."
        )


@app.post("/newsletter/signup")
def newsletter_signup(request: NewsletterSignup):

    if not RESEND_API_KEY or not RESEND_FROM_EMAIL or not PUBLIC_API_URL:
        raise HTTPException(
            status_code=503,
            detail="Newsletter email configuration is missing."
        )

    email = str(request.email).strip().lower()

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    raw_unsubscribe_token = secrets.token_urlsafe(32)
    unsubscribe_token_hash = hashlib.sha256(
        raw_unsubscribe_token.encode("utf-8")
    ).hexdigest()

    expiry = (
        datetime.now(timezone.utc) + timedelta(hours=24)
    ).isoformat()

    # Save or refresh the pending subscriber.
    try:
        existing = (
            supabase.table("newsletter_subscribers")
            .select("id,status")
            .eq("email", email)
            .limit(1)
            .execute()
        )

        if existing.data:
            subscriber = existing.data[0]

            if subscriber["status"] == "confirmed":
                return {
                    "success": True,
                    "message": "This address is already subscribed."
                }

            supabase.table("newsletter_subscribers").update({
                "status": "pending",
                "confirmation_token_hash": token_hash,
                "confirmation_expires_at": expiry,
                "unsubscribe_token_hash": unsubscribe_token_hash,
                "confirmed_at": None,
                "unsubscribed_at": None
            }).eq("email", email).execute()

        else:
            supabase.table("newsletter_subscribers").insert({
                "email": email,
                "status": "pending",
                "confirmation_token_hash": token_hash,
                "confirmation_expires_at": expiry,
                "unsubscribe_token_hash": unsubscribe_token_hash
            }).execute()

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process signup right now."
        )

    # Create the confirmation link.
    confirmation_url = (
        f"{PUBLIC_API_URL}/newsletter/confirm?token={raw_token}"
    )
    unsubscribe_url = (
        f"{PUBLIC_API_URL}/newsletter/unsubscribe?"
        f"token={raw_unsubscribe_token}"
    )

    safe_email = html.escape(email)
    safe_url = html.escape(confirmation_url, quote=True)
    safe_unsubscribe_url = html.escape(
        unsubscribe_url, quote=True
    )

    email_payload = {
        "from": RESEND_FROM_EMAIL,
        "to": [email],
        "subject": "Confirm your SmartPick Hub newsletter subscription",
        "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
                <h2>Welcome to SmartPick Hub!</h2>
                <p>Hello {safe_email},</p>
                <p>Please confirm your newsletter subscription by clicking below:</p>
                <p>
                    <a href="{safe_url}"
                       style="background:#1D493D;color:white;padding:12px 20px;
                              text-decoration:none;border-radius:6px;">
                        Confirm Subscription
                    </a>
                </p>
                <p>This link expires in 24 hours.</p>
                <p>After confirming, you can unsubscribe here: <a href="{safe_unsubscribe_url}">Unsubscribe</a>.</p>
                <p>If you did not request this subscription, you can ignore this email.</p>
                <p>SmartPick Hub Team</p>
            </div>
        """,
        "text": (
            "Welcome to SmartPick Hub!\n\n"
            "Confirm your newsletter subscription using this link:\n"
            f"{confirmation_url}\n\n"
            "This link expires in 24 hours.\n\n"
            "After confirming, unsubscribe here:\n"
            f"{unsubscribe_url}"
        )
    }

    # Send email through Resend.
    try:
        email_response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json=email_payload,
            timeout=20
        )

        if email_response.status_code not in (200, 201):
            raise HTTPException(
                status_code=502,
                detail="Confirmation email could not be sent. Please try again."
            )

    except requests.exceptions.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Email service is temporarily unavailable."
        )

    return {
        "success": True,
        "message": "Confirmation email sent. Please check your inbox and spam folder."
    }



@app.get("/newsletter/confirm", response_class=HTMLResponse)
def confirmation_page(token: str):
    # Email security scanners often open links automatically. A GET request
    # must display a confirmation page, not activate the subscription.
    if not token or len(token) > 200:
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation link."
        )

    safe_token = html.escape(token, quote=True)
    page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="robots" content="noindex, nofollow">
        <meta name="referrer" content="no-referrer">
        <meta name="theme-color" content="#102D27">
        <title>Confirm Subscription | SmartPick Hub</title>
        <style>
            * { box-sizing: border-box; }
            body {
                margin: 0; min-height: 100vh; padding: 24px;
                display: grid; place-items: center;
                background: #F7F5EF; color: #102D27;
                font-family: Arial, Helvetica, sans-serif;
            }
            .card {
                width: 100%; max-width: 540px; padding: 42px 30px;
                background: #fff; border: 1px solid #E9E5DA;
                border-radius: 18px; text-align: center;
                box-shadow: 0 12px 40px rgba(16,45,39,.08);
            }
            .brand { font-size: 24px; font-weight: 700; color: #1D493D; }
            h1 { font-size: 26px; line-height: 1.3; margin: 28px 0 14px; }
            p { color: #65736D; line-height: 1.8; }
            button {
                width: 100%; max-width: 300px; margin-top: 18px;
                padding: 15px 22px; border: 0; border-radius: 8px;
                background: #1D493D; color: #fff; font-size: 15px;
                font-weight: 700; cursor: pointer;
            }
            button:disabled { opacity: .6; cursor: wait; }
            #confirmation-message { min-height: 24px; font-size: 14px; }
            @media (max-width: 480px) { .card { padding: 32px 20px; } }
        </style>
    </head>
    <body>
        <main class="card">
            <div class="brand">SmartPick Hub</div>
            <h1>Confirm Your Newsletter Subscription</h1>
            <p>To complete your subscription, select the button below. Opening this page alone will not activate email updates.</p>
            <div id="confirmation-form" data-token="TOKEN_PLACEHOLDER">
                <button type="button" id="confirm-button">Confirm Subscription</button>
            </div>
            <p id="confirmation-message" role="status" aria-live="polite"></p>
        </main>
        <script>
        const confirmButton = document.getElementById("confirm-button");
        confirmButton.addEventListener("click", async () => {
            confirmButton.disabled = true;
            confirmButton.textContent = "Confirming...";
            const message = document.getElementById("confirmation-message");
            const token = document.getElementById("confirmation-form").dataset.token;

            try {
                const response = await fetch("/newsletter/confirm", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token })
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(data.detail || "We could not confirm your subscription.");
                }
                message.textContent = data.message || "Your subscription is confirmed.";
                document.querySelector("h1").textContent = "You're Successfully Subscribed!";
                confirmButton.remove();
            } catch (error) {
                message.textContent = error.message || "Please try again later.";
                confirmButton.disabled = false;
                confirmButton.textContent = "Confirm Subscription";
            }
        });
        </script>
    </body>
    </html>
    """

    page = page.replace("TOKEN_PLACEHOLDER", safe_token)
    return HTMLResponse(
        content=page,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer"
        }
    )


@app.post("/newsletter/confirm")
def confirm_newsletter(request: ConfirmationRequest):
    token = request.token.strip()

    if not token or len(token) > 200:
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation token."
        )

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    try:
        result = (
            supabase.table("newsletter_subscribers")
            .select("id,status,confirmation_expires_at")
            .eq("confirmation_token_hash", token_hash)
            .eq("status", "pending")
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="We could not verify your confirmation right now. Please try again later."
        )

    if not result.data:
        raise HTTPException(
            status_code=400,
            detail="This confirmation link is invalid or has already been used."
        )

    subscriber = result.data[0]
    expiry_value = subscriber.get("confirmation_expires_at")

    if not expiry_value:
        raise HTTPException(
            status_code=400,
            detail="This confirmation link is no longer valid. Please subscribe again."
        )

    try:
        expiry = datetime.fromisoformat(expiry_value.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="We could not verify this confirmation link. Please subscribe again."
        )

    if expiry <= datetime.now(timezone.utc):
        try:
            (
                supabase.table("newsletter_subscribers")
                .update({
                    "confirmation_token_hash": None,
                    "confirmation_expires_at": None
                })
                .eq("id", subscriber["id"])
                .eq("confirmation_token_hash", token_hash)
                .eq("status", "pending")
                .execute()
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=400,
            detail="This confirmation link has expired. Please subscribe again."
        )

    try:
        update_result = (
            supabase.table("newsletter_subscribers")
            .update({
                "status": "confirmed",
                "confirmed_at": datetime.now(timezone.utc).isoformat(),
                "confirmation_token_hash": None,
                "confirmation_expires_at": None
            })
            .eq("id", subscriber["id"])
            .eq("confirmation_token_hash", token_hash)
            .eq("status", "pending")
            .select("id")
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Your subscription could not be confirmed right now. Please try again later."
        )

    if not update_result.data:
        raise HTTPException(
            status_code=409,
            detail="This confirmation link has already been used."
        )

    return {
        "success": True,
        "message": "Thank you for confirming your SmartPick Hub newsletter subscription."
    }


@app.get("/newsletter/unsubscribe", response_class=HTMLResponse)
def unsubscribe_page(token: str):
    if not token or len(token) > 200:
        raise HTTPException(
            status_code=400,
            detail="Invalid unsubscribe link."
        )

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    try:
        result = (
            supabase.table("newsletter_subscribers")
            .select("id,status")
            .eq("unsubscribe_token_hash", token_hash)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to verify unsubscribe link right now."
        )

    if not result.data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already-used unsubscribe link."
        )

    subscriber = result.data[0]

    safe_token = html.escape(token, quote=True)

    if subscriber["status"] != "confirmed":
        page = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Subscription Status | SmartPick Hub</title>
        </head>
        <body style="margin:0;background:#F7F5EF;
                     font-family:Arial,sans-serif;color:#102D27;">
            <main style="max-width:520px;margin:70px auto;padding:24px;">
                <section style="background:white;padding:40px 28px;
                                border-radius:16px;text-align:center;
                                box-shadow:0 8px 30px #102D2712;">
                    <h1 style="color:#1D493D;">SmartPick Hub</h1>
                    <h2>Subscription Status</h2>
                    <p>Please confirm your newsletter subscription first.
                       This unsubscribe link is available after confirmation.</p>
                </section>
            </main>
        </body>
        </html>
        """
        return HTMLResponse(
            content=page,
            headers={
                "Cache-Control": "no-store, max-age=0",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer"
            }
        )

    page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="theme-color" content="#102D27">
        <title>Unsubscribe | SmartPick Hub</title>

        <style>
            * { box-sizing: border-box; }

            body {
                margin: 0;
                min-height: 100vh;
                padding: 30px 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #F7F5EF;
                color: #102D27;
                font-family: Arial, Helvetica, sans-serif;
            }

            .card {
                width: 100%;
                max-width: 540px;
                background: #FFFFFF;
                border: 1px solid #E9E5DA;
                border-radius: 18px;
                padding: 38px 30px;
                text-align: center;
                box-shadow: 0 12px 40px rgba(16,45,39,0.08);
            }

            .brand {
                color: #1D493D;
                font-size: 27px;
                font-weight: 700;
                letter-spacing: -0.7px;
                margin-bottom: 8px;
            }

            .tagline {
                color: #9A783D;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
                margin-bottom: 27px;
            }

            .gold-line {
                width: 55px;
                height: 3px;
                margin: 0 auto 27px;
                background: #D6AD55;
                border-radius: 5px;
            }

            h1 {
                font-size: 25px;
                line-height: 1.3;
                margin: 0 0 16px;
            }

            .description {
                color: #65736D;
                font-size: 15px;
                line-height: 1.8;
                margin: 0 auto 27px;
                max-width: 420px;
            }

            .unsubscribe-button {
                width: 100%;
                max-width: 300px;
                padding: 15px 22px;
                background: #1D493D;
                color: white;
                border: 1px solid #1D493D;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 700;
                cursor: pointer;
                transition: background 0.2s ease;
            }

            .unsubscribe-button:hover {
                background: #102D27;
            }

            .unsubscribe-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .message {
                margin-top: 20px;
                font-size: 14px;
                line-height: 1.6;
                color: #1D493D;
            }

            .footer {
                border-top: 1px solid #EEEAE1;
                margin-top: 30px;
                padding-top: 20px;
                color: #89938D;
                font-size: 12px;
                line-height: 1.8;
            }

            @media (max-width: 480px) {
                .card { padding: 30px 20px; }
                h1 { font-size: 22px; }
                .brand { font-size: 24px; }
            }
        </style>
    </head>

    <body>
        <main class="card">
            <header>
                <div class="brand">SmartPick Hub</div>
                <div class="tagline">SMARTER SHOPPING. BETTER CHOICES.</div>
            </header>

            <div class="gold-line"></div>

            <h1>Manage Your Subscription</h1>

            <p class="description">
                We're sorry to see you go. Would you like to unsubscribe
                from SmartPick Hub newsletter updates?
            </p>

            <div id="unsubscribe-form" data-token="TOKEN_PLACEHOLDER">
                <button
                    type="button"
                    class="unsubscribe-button"
                    id="unsubscribe-button">
                    Confirm Unsubscribe
                </button>
            </div>

            <p class="message" id="result-message" role="status"
               aria-live="polite"></p>

            <footer class="footer">
                You can subscribe again whenever you wish.<br>
                &copy; SmartPick Hub. All rights reserved.
            </footer>
        </main>

        <script>
        const button = document.getElementById("unsubscribe-button");

        button.addEventListener("click", async function () {
            button.disabled = true;
            button.textContent = "Processing...";

            const message = document.getElementById("result-message");
            const token = document.getElementById(
                "unsubscribe-form"
            ).dataset.token;

            try {
                const response = await fetch("/newsletter/unsubscribe", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({token: token})
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.detail || "Unsubscribe failed."
                    );
                }

                message.textContent =
                    data.message || "You have been unsubscribed successfully.";

                button.remove();

                document.querySelector("h1").textContent =
                    "Unsubscribed Successfully";

                document.querySelector(".description").textContent =
                    "You will no longer receive SmartPick Hub newsletter updates.";

            } catch (error) {
                message.textContent = error.message;
                button.disabled = false;
                button.textContent = "Confirm Unsubscribe";
            }
        });
        </script>
    </body>
    </html>
    """

    page = page.replace("TOKEN_PLACEHOLDER", safe_token)

    return HTMLResponse(
        content=page,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer"
        }
    )
@app.post("/newsletter/unsubscribe")
def unsubscribe_newsletter(request: UnsubscribeRequest):
    token = request.token.strip()

    if not token or len(token) > 200:
        raise HTTPException(
            status_code=400,
            detail="Invalid unsubscribe token."
        )

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    try:
        result = (
            supabase.table("newsletter_subscribers")
            .select("id,status")
            .eq("unsubscribe_token_hash", token_hash)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to process unsubscribe right now."
        )

    if not result.data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already-used unsubscribe link."
        )

    subscriber = result.data[0]

    if subscriber["status"] != "confirmed":
        raise HTTPException(
            status_code=409,
            detail="Only confirmed subscribers can unsubscribe."
        )

    try:
        update_result = (
            supabase.table("newsletter_subscribers")
            .update({
                "status": "unsubscribed",
                "unsubscribed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "unsubscribe_token_hash": None
            })
            .eq("id", subscriber["id"])
            .eq("status", "confirmed")
            .eq("unsubscribe_token_hash", token_hash)
            .select("id")
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to complete unsubscribe right now."
        )

    if not update_result.data:
        raise HTTPException(
            status_code=409,
            detail="This link has already been used."
        )

    return {
        "success": True,
        "message": "You have successfully unsubscribed from SmartPick Hub."
    }
