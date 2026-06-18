import asyncio
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.database import async_session_maker
from app.models.gmail_account import GmailAccount
from app.models.email_message import EmailMessage
from app.models.email_reply import EmailReply
from app.models.campaign import CampaignLead
from app.utils.gmail_client import GmailClient
from app.utils.security import decrypt_token, encrypt_token
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def run_async(coro):
    return asyncio.run(coro)


def _parse_message_payload(msg):
    headers = {}
    if "payload" in msg and "headers" in msg["payload"]:
        for h in msg["payload"]["headers"]:
            headers[h["name"].lower()] = h["value"]

    body = ""
    if "payload" in msg:
        payload = msg["payload"]
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                    import base64
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    break
        elif "body" in payload and "data" in payload["body"]:
            import base64
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    return headers, body


def _classify_reply(body_text: str, subject: str) -> str:
    import re
    bl = body_text.lower()
    sl = subject.lower()
    if re.search(r"(returned mail|undelivered|delivery failure|mail delivery failed)", bl):
        return "bounce"
    if re.search(r"(out of office|auto-reply|automatic reply|vacation|away from)", bl):
        return "ooo"
    if re.search(r"(autoreply|auto-reply|auto reply)", sl):
        return "autoreply"
    if re.search(r"(unsubscribe|remove|opt.out|don.t email|no more)", bl):
        return "not_interested"
    if re.search(r"(interested|pricing|demo|quote|tell me more|schedule|call|meeting)", bl):
        return "interested"
    if re.search(r"^(re|fwd)", sl):
        return "reply"
    return "reply"


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def check_inbox(self, user_id: str, account_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(GmailAccount).where(
                    GmailAccount.id == UUID(account_id),
                    GmailAccount.user_id == UUID(user_id),
                    GmailAccount.is_active == True,
                )
            )
            account = result.scalar_one_or_none()
            if not account:
                raise ValueError(f"GmailAccount {account_id} not found or inactive")

            client = GmailClient(account)
            raw_messages = client.read_inbox(max_results=20)

            replies_processed = 0
            for raw in raw_messages:
                headers, body = _parse_message_payload(raw)
                in_reply_to = headers.get("in-reply-to") or headers.get("references", "")
                if not in_reply_to:
                    continue

                message_id = raw.get("id")
                subject = headers.get("subject", "")
                from_email = headers.get("from", "")
                classification = _classify_reply(body, subject)

                msg_result = await db.execute(
                    select(EmailMessage).where(
                        EmailMessage.message_id == message_id
                    )
                )
                existing_msg = msg_result.scalar_one_or_none()

                if not existing_msg:
                    email_msg = EmailMessage(
                        message_id=message_id,
                        gmail_account_id=account.id,
                        from_email=from_email,
                        to_email=account.email,
                        subject=subject,
                        body=body,
                        status="replied",
                        sent_at=datetime.now(timezone.utc),
                    )
                    db.add(email_msg)
                    await db.flush()
                    existing_msg = email_msg

                if existing_msg.status != "replied":
                    existing_msg.status = "replied"

                reply_result = await db.execute(
                    select(EmailReply).where(
                        EmailReply.email_message_id == existing_msg.id,
                    )
                )
                if not reply_result.scalar_one_or_none():
                    reply = EmailReply(
                        email_message_id=existing_msg.id,
                        gmail_account_id=account.id,
                        from_email=from_email,
                        subject=subject,
                        body_snippet=body[:500],
                        reply_type=classification,
                        is_positive=(classification == "interested"),
                        received_at=datetime.now(timezone.utc),
                    )
                    db.add(reply)

                cl_result = await db.execute(
                    select(CampaignLead).where(
                        CampaignLead.gmail_account_id == account.id,
                        CampaignLead.status == "sent",
                    ).order_by(CampaignLead.sent_at.desc()).limit(1)
                )
                campaign_lead = cl_result.scalar_one_or_none()
                if campaign_lead:
                    campaign_lead.status = "replied"
                    campaign_lead.replied_at = datetime.now(timezone.utc)

                replies_processed += 1

            await db.commit()
            return {"account_id": account_id, "replies_processed": replies_processed}

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def check_all_inboxes():
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(GmailAccount).where(GmailAccount.is_active == True)
            )
            accounts = list(result.scalars().all())

        results = []
        for account in accounts:
            try:
                res = check_inbox.delay(str(account.user_id), str(account.id))
                results.append({"account_id": str(account.id), "task_id": res.id})
            except Exception as e:
                results.append({"account_id": str(account.id), "error": str(e)})
        return {"checked": len(results), "results": results}

    return run_async(_run())


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def refresh_account_token(self, account_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(GmailAccount).where(GmailAccount.id == UUID(account_id))
            )
            account = result.scalar_one_or_none()
            if not account:
                raise ValueError(f"GmailAccount {account_id} not found")

            client = GmailClient(account)
            success = client.refresh_token()
            if success:
                account.access_token = encrypt_token(client._get_credentials().token)
                account.token_expiry = client._get_credentials().expiry
                await db.commit()
                return {"account_id": account_id, "refreshed": True}
            else:
                account.is_active = False
                await db.commit()
                return {"account_id": account_id, "refreshed": False, "error": "Token refresh failed"}

    try:
        return run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def refresh_all_tokens():
    async def _run():
        async with async_session_maker() as db:
            now = datetime.now(timezone.utc)
            expire_threshold = now + timedelta(hours=24)
            result = await db.execute(
                select(GmailAccount).where(
                    GmailAccount.is_active == True,
                    GmailAccount.token_expiry <= expire_threshold,
                )
            )
            accounts = list(result.scalars().all())

        results = []
        for account in accounts:
            try:
                res = refresh_account_token.delay(str(account.id))
                results.append({"account_id": str(account.id), "task_id": res.id})
            except Exception as e:
                results.append({"account_id": str(account.id), "error": str(e)})
        return {"refreshed": len(results), "results": results}

    return run_async(_run())


@celery_app.task(bind=True)
def update_account_health(self, account_id: str):
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(GmailAccount).where(GmailAccount.id == UUID(account_id))
            )
            account = result.scalar_one_or_none()
            if not account:
                raise ValueError(f"GmailAccount {account_id} not found")

            client = GmailClient(account)
            health = client.check_health()

            account.health_score = health.get("health_score", 100.0)
            if health.get("is_healthy"):
                account.inbox_rate = health.get("inbox_rate", account.inbox_rate)
                account.spam_rate = health.get("spam_rate", account.spam_rate)
            else:
                account.health_score = max(0, account.health_score - 10)

            await db.commit()
            return {"account_id": account_id, "health_score": account.health_score}

    try:
        return run_async(_run())
    except Exception as exc:
        return {"account_id": account_id, "error": str(exc)}


@celery_app.task
def update_all_health_scores():
    async def _run():
        async with async_session_maker() as db:
            result = await db.execute(
                select(GmailAccount).where(GmailAccount.is_active == True)
            )
            accounts = list(result.scalars().all())

        results = []
        for account in accounts:
            try:
                res = update_account_health.delay(str(account.id))
                results.append({"account_id": str(account.id), "task_id": res.id})
            except Exception as e:
                results.append({"account_id": str(account.id), "error": str(e)})
        return {"updated": len(results), "results": results}

    return run_async(_run())
