import os
import hashlib
import secrets
import html
from urllib.parse import urlsplit
from pathlib import Path
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from supabase import create_client

PROJECT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT / ".env", override=True)
FRONTEND_URL = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

if FRONTEND_URL:
    parsed_frontend_url = urlsplit(FRONTEND_URL)
    if (
        parsed_frontend_url.scheme != "https"
        or not parsed_frontend_url.netloc
        or parsed_frontend_url.query
        or parsed_frontend_url.fragment
    ):
        raise RuntimeError("FRONTEND_URL must be a valid HTTPS website origin.")

FRONTEND_ORIGINS = [
    f"{urlsplit(FRONTEND_URL).scheme}://{urlsplit(FRONTEND_URL).netloc}"
] if FRONTEND_URL else []

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "").strip()
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")

if PUBLIC_API_URL:
    parsed_api_url = urlsplit(PUBLIC_API_URL)
    if (
        parsed_api_url.scheme != "https"
        or not parsed_api_url.netloc
        or parsed_api_url.path not in ("", "/")
        or parsed_api_url.query
        or parsed_api_url.fragment
    ):
        raise RuntimeError("PUBLIC_API_URL must be a valid HTTPS website origin.")

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
class NewsletterSignup(BaseModel):
    email: EmailStr


class UnsubscribeRequest(BaseModel):
    token: str


@app.get("/")
def home():
    return {
        "message": "Welcome to SmartPick Hub API",
        "status": "running"
    }


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
def confirm_newsletter(token: str):

    def confirmation_page(title, message, success=False, status_code=200):
        if success:
            icon = "✓"
            label = "SUBSCRIPTION CONFIRMED"
            button_text = "Explore SmartPick Hub"
        else:
            icon = "!"
            label = "SUBSCRIPTION UPDATE"
            button_text = "Return to SmartPick Hub"

        safe_title = html.escape(title)
        safe_message = html.escape(message)
        safe_home = html.escape(FRONTEND_URL, quote=True) if FRONTEND_URL else ""
        button_html = (
            f'<a class="button" href="{safe_home}">{button_text}</a>'
            if safe_home else
            '<p class="footer">You can close this page. SmartPick Hub website link is not configured yet.</p>'
        )

        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow">
    <meta name="theme-color" content="#102D27">
    <title>{safe_title} | SmartPick Hub</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            background: #F7F5EF;
            color: #102D27;
            font-family: 'DM Sans', sans-serif;
        }}

        .card {{
            width: 100%;
            max-width: 560px;
            padding: 52px 42px;
            text-align: center;
            background: #FFFFFF;
            border: 1px solid #E7E8DF;
            border-radius: 18px;
            box-shadow: 0 18px 55px rgba(16,45,39,.08);
        }}

        .brand {{
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 3px;
            color: #102D27;
        }}

        .brand-line {{
            width: 42px;
            height: 3px;
            margin: 20px auto 30px;
            background: #C5A66A;
            border-radius: 5px;
        }}

        .icon {{
            width: 76px;
            height: 76px;
            margin: 0 auto 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: {"#E6F2EA" if success else "#F8EFE2"};
            color: {"#167044" if success else "#A36B21"};
            font-size: 38px;
            font-weight: 700;
        }}

        .label {{
            color: #8A7650;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
        }}

        h1 {{
            margin: 16px 0;
            font-family: 'Playfair Display', serif;
            font-size: clamp(28px, 5vw, 38px);
            line-height: 1.2;
            color: #102D27;
        }}

        .message {{
            max-width: 410px;
            margin: 0 auto;
            color: #63716A;
            font-size: 15px;
            line-height: 1.8;
        }}

        .button {{
            display: inline-block;
            margin-top: 32px;
            padding: 15px 27px;
            background: #102D27;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            transition: background .2s ease;
        }}

        .button:hover {{
            background: #244B40;
        }}

        .footer {{
            margin-top: 35px;
            padding-top: 22px;
            border-top: 1px solid #ECEDE7;
            color: #8A938E;
            font-size: 12px;
        }}

        @media (max-width: 500px) {{
            .card {{
                padding: 38px 22px;
            }}
        }}
    </style>
</head>

<body>
    <main class="card">
        <div class="brand">SMARTPICK HUB</div>
        <div class="brand-line"></div>

        <div class="icon" aria-hidden="true">{icon}</div>

        <div class="label">{label}</div>

        <h1>{safe_title}</h1>

        <p class="message">{safe_message}</p>

        {button_html}

        <div class="footer">
            © 2026 SmartPick Hub. All rights reserved.
        </div>
    </main>
</body>
</html>"""

        return HTMLResponse(
            content=page,
            status_code=status_code,
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer"
            }
        )

    # Validate token
    if not token or len(token) > 200:
        return confirmation_page(
            "Invalid Confirmation Link",
            "This confirmation link is not valid. Please sign up again to receive a new confirmation email.",
            status_code=400
        )

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    # Find subscriber
    try:
        result = (
            supabase.table("newsletter_subscribers")
            .select("id,email,status,confirmation_expires_at")
            .eq("confirmation_token_hash", token_hash)
            .limit(1)
            .execute()
        )
    except Exception:
        return confirmation_page(
            "Unable to Verify Your Link",
            "We could not verify your confirmation right now. Please try again later.",
            status_code=503
        )

    if not result.data:
        return confirmation_page(
            "Link Already Used or Invalid",
            "This confirmation link may already have been used or is no longer valid.",
            status_code=400
        )

    subscriber = result.data[0]
    expiry_value = subscriber["confirmation_expires_at"]

    if not expiry_value:
        return confirmation_page(
            "Invalid Confirmation Link",
            "This confirmation link is no longer valid. Please sign up again.",
            status_code=400
        )

    # Check expiration
    try:
        expiry = datetime.fromisoformat(
            expiry_value.replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        return confirmation_page(
            "Invalid Confirmation Link",
            "We could not verify this confirmation link. Please sign up again.",
            status_code=400
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
                .execute()
            )
        except Exception:
            pass

        return confirmation_page(
            "Confirmation Link Expired",
            "Your confirmation link has expired. Please sign up again to receive a new link.",
            status_code=400
        )

    # Confirm subscription in database
    try:
        update_result = (
            supabase.table("newsletter_subscribers")
            .update({
                "status": "confirmed",
                "confirmed_at": datetime.now(
                    timezone.utc
                ).isoformat(),
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
        return confirmation_page(
            "Confirmation Temporarily Unavailable",
            "Your subscription could not be confirmed right now. Please try again later.",
            status_code=503
        )

    if not update_result.data:
        return confirmation_page(
            "Link Already Used or Invalid",
            "This confirmation link has already been used or is no longer valid.",
            status_code=409
        )

    return confirmation_page(
        "You're Successfully Subscribed!",
        "Thank you for joining SmartPick Hub. Your email address has been confirmed. Stay tuned for useful buying guides, product comparisons and carefully selected shopping updates.",
        success=True
    )




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
