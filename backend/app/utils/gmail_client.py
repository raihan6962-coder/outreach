from typing import Optional, List
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

from app.utils.security import decrypt_token


class GmailClient:
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    def __init__(self, gmail_account):
        self.gmail_account = gmail_account
        self._service: Optional[Resource] = None

    def _get_credentials(self) -> Credentials:
        return Credentials(
            token=decrypt_token(self.gmail_account.access_token),
            refresh_token=decrypt_token(self.gmail_account.refresh_token),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,
            client_secret=None,
            scopes=self.SCOPES,
        )

    def _get_service(self) -> Resource:
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def send_email(self, to: str, subject: str, body_html: str, body_text: Optional[str] = None) -> dict:
        service = self._get_service()
        message = MIMEMultipart("alternative")
        message["To"] = to
        message["Subject"] = subject

        if body_text:
            message.attach(MIMEText(body_text, "plain"))

        message.attach(MIMEText(body_html, "html"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()

        return {
            "message_id": sent["id"],
            "thread_id": sent["threadId"],
        }

    def read_inbox(self, query: Optional[str] = None, max_results: int = 50) -> list:
        service = self._get_service()
        result = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )
        messages = result.get("messages", [])
        full_messages = []
        for msg in messages:
            full = (
                service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            )
            full_messages.append(full)
        return full_messages

    def get_message(self, message_id: str) -> dict:
        service = self._get_service()
        return service.users().messages().get(userId="me", id=message_id, format="full").execute()

    def get_thread(self, thread_id: str) -> list:
        service = self._get_service()
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        return thread.get("messages", [])

    def refresh_token(self) -> bool:
        try:
            creds = self._get_credentials()
            creds.refresh(Request())
            self.gmail_account.access_token = creds.token
            if creds.refresh_token:
                self.gmail_account.refresh_token = creds.refresh_token
            self.gmail_account.token_expiry = creds.expiry
            return True
        except RefreshError:
            return False

    def get_profile(self) -> dict:
        service = self._get_service()
        profile = service.users().getProfile(userId="me").execute()
        return profile

    def check_health(self) -> dict:
        try:
            profile = self.get_profile()
            is_healthy = True
        except Exception:
            is_healthy = False

        return {
            "is_healthy": is_healthy,
            "health_score": self.gmail_account.health_score,
            "inbox_rate": self.gmail_account.inbox_rate,
            "spam_rate": self.gmail_account.spam_rate,
        }
