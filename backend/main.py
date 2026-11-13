import os
import hashlib
import secrets
import html
from pathlib import Path
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client

PROJECT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT / ".env", override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "").rstrip("/")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError("Supabase configuration is missing.")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

app = FastAPI(
    title="SmartPick Hub API",
    description="Backend API for SmartPick Hub",
    version="1.0.0"
)


class NewsletterSignup(BaseModel):
    email: EmailStr


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

    if not RESEND_API_KEY or not PUBLIC_API_URL:
        raise HTTPException(
            status_code=503,
            detail="Newsletter email configuration is missing."
        )

    email = str(request.email).strip().lower()

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
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
                "unsubscribe_token_hash": None,
                "confirmed_at": None,
                "unsubscribed_at": None
            }).eq("email", email).execute()

        else:
            supabase.table("newsletter_subscribers").insert({
                "email": email,
                "status": "pending",
                "confirmation_token_hash": token_hash,
                "confirmation_expires_at": expiry
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

    safe_email = html.escape(email)
    safe_url = html.escape(confirmation_url, quote=True)

    email_payload = {
        "from": "SmartPick Hub <onboarding@resend.dev>",
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
                <p>If you did not request this subscription, you can ignore this email.</p>
                <p>SmartPick Hub Team</p>
            </div>
        """,
        "text": (
            "Welcome to SmartPick Hub!\n\n"
            "Confirm your newsletter subscription using this link:\n"
            f"{confirmation_url}\n\n"
            "This link expires in 24 hours."
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


@app.get("/newsletter/confirm")
def confirm_newsletter(token: str):

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    try:
        result = (
            supabase.table("newsletter_subscribers")
            .select(
                "id,email,status,confirmation_expires_at"
            )
            .eq("confirmation_token_hash", token_hash)
            .limit(1)
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to verify confirmation right now."
        )

    if not result.data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already-used confirmation link."
        )

    subscriber = result.data[0]
    expiry_value = subscriber["confirmation_expires_at"]

    if not expiry_value:
        raise HTTPException(
            status_code=400,
            detail="Confirmation link is invalid."
        )

    try:
        expiry = datetime.fromisoformat(
            expiry_value.replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Confirmation link is invalid."
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

        raise HTTPException(
            status_code=400,
            detail="Confirmation link has expired. Please sign up again."
        )

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
        raise HTTPException(
            status_code=503,
            detail="Unable to confirm subscription right now."
        )

    if not update_result.data:
        raise HTTPException(
            status_code=409,
            detail="This confirmation link has already been used or is invalid."
        )

    return {
        "success": True,
        "message": "Your newsletter subscription is confirmed."
    }
