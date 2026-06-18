from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google_auth_oauthlib.flow import Flow
from app.config import settings
from app.utils.security import encrypt_token, decrypt_token
from app.models.gmail import GmailAccount


class GmailService:
    @staticmethod
    def _get_flow() -> Flow:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
                "openid",
                "email",
                "profile",
            ],
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        return flow

    @staticmethod
    def get_auth_url() -> str:
        flow = GmailService._get_flow()
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url

    @staticmethod
    async def handle_callback(
        db: AsyncSession, user_id: UUID, code: str
    ) -> GmailAccount:
        flow = GmailService._get_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        encrypted_refresh = encrypt_token(credentials.refresh_token)
        account = GmailAccount(
            user_id=user_id,
            email=credentials.id_token.get("email", ""),
            access_token=encrypt_token(credentials.token),
            refresh_token=encrypted_refresh,
            token_expiry=credentials.expiry,
            is_active=True,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def get_accounts(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(GmailAccount)
            .where(GmailAccount.user_id == user_id)
            .order_by(GmailAccount.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_account(db: AsyncSession, account_id: UUID) -> GmailAccount:
        result = await db.execute(
            select(GmailAccount).where(GmailAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("Gmail account not found")
        return account

    @staticmethod
    async def update_account(
        db: AsyncSession, account_id: UUID, data: dict
    ) -> GmailAccount:
        account = await GmailService.get_account(db, account_id)
        for field, value in data.items():
            if field in ("refresh_token", "access_token"):
                value = encrypt_token(value)
            setattr(account, field, value)
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def toggle_account(
        db: AsyncSession, account_id: UUID, is_active: bool
    ) -> GmailAccount:
        account = await GmailService.get_account(db, account_id)
        account.is_active = is_active
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def disconnect_account(db: AsyncSession, account_id: UUID) -> bool:
        account = await GmailService.get_account(db, account_id)
        account.is_active = False
        account.disconnected_at = db.func.now()
        await db.commit()
        return True

    @staticmethod
    async def refresh_account_token(db: AsyncSession, account_id: UUID) -> bool:
        account = await GmailService.get_account(db, account_id)
        refresh_token = decrypt_token(account.refresh_token)
        flow = GmailService._get_flow()
        flow.credentials.refresh_token = refresh_token
        flow.credentials.token_uri = "https://oauth2.googleapis.com/token"
        flow.credentials.refresh(
            requests.Request()
        )
        account.access_token = encrypt_token(flow.credentials.token)
        account.token_expiry = flow.credentials.expiry
        await db.commit()
        return True

    @staticmethod
    async def check_account_health(
        db: AsyncSession, account_id: UUID
    ) -> dict:
        account = await GmailService.get_account(db, account_id)
        if not account.is_active:
            return {"account_id": str(account_id), "healthy": False, "message": "Account is inactive"}
        from app.utils.gmail_client import GmailClient
        client = GmailClient(account)
        try:
            profile = client.get_profile()
            return {
                "account_id": str(account_id),
                "email": account.email,
                "healthy": True,
                "message": "Account is healthy",
                "daily_sent": account.daily_sent,
                "daily_limit": account.daily_limit,
                "hourly_sent": account.hourly_sent,
                "hourly_limit": account.hourly_limit,
            }
        except Exception as e:
            return {
                "account_id": str(account_id),
                "email": account.email,
                "healthy": False,
                "message": str(e),
            }

    @staticmethod
    async def get_active_accounts_for_campaign(
        db: AsyncSession, user_id: UUID, account_ids: list
    ) -> list:
        result = await db.execute(
            select(GmailAccount)
            .where(
                GmailAccount.user_id == user_id,
                GmailAccount.id.in_(account_ids),
                GmailAccount.is_active == True,
                GmailAccount.daily_sent < GmailAccount.daily_limit,
            )
            .order_by(GmailAccount.daily_sent.asc())
        )
        return list(result.scalars().all())
