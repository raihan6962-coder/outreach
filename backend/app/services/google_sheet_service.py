from uuid import UUID
from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.sheet_source import SheetSource
from app.models.lead import Lead


class GoogleSheetService:
    @staticmethod
    async def fetch_pending_leads(
        db: AsyncSession, sheet_source: SheetSource, user_id: UUID
    ) -> int:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                sheet_source.webhook_url,
                json={"action": "get_pending"},
            )
            response.raise_for_status()
            data = response.json()
        leads_data = data.get("leads", data.get("data", []))
        count = 0
        for item in leads_data:
            lead = Lead(
                user_id=user_id,
                sheet_source_id=sheet_source.id,
                app_id=item.get("app_id"),
                developer=item.get("developer", ""),
                email=item.get("email", ""),
                app_name=item.get("app_name", ""),
                category=item.get("category", ""),
                installs=item.get("installs", 0),
                keyword=item.get("keyword", ""),
                website=item.get("website", ""),
            )
            db.add(lead)
            count += 1
        await db.commit()
        return count

    @staticmethod
    async def mark_lead_sent(sheet_source: SheetSource, app_id: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                sheet_source.webhook_url,
                json={"action": "mark_sent", "app_id": app_id},
            )
            response.raise_for_status()
            data = response.json()
        return data.get("success", False)

    @staticmethod
    async def test_connection(sheet_source: SheetSource) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    sheet_source.webhook_url,
                    json={"action": "get_pending"},
                )
                response.raise_for_status()
                data = response.json()
                leads = data.get("leads", data.get("data", []))
                return {
                    "success": True,
                    "message": "Connection successful",
                    "lead_count": len(leads),
                }
            except httpx.HTTPStatusError as e:
                return {
                    "success": False,
                    "message": f"HTTP {e.response.status_code}: {e.response.text}",
                    "lead_count": 0,
                }
            except httpx.RequestError as e:
                return {
                    "success": False,
                    "message": f"Connection failed: {str(e)}",
                    "lead_count": 0,
                }
