from uuid import UUID
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.template import Template, TemplateFolder
from app.schemas.template import TemplateCreate, TemplateUpdate


class TemplateService:
    @staticmethod
    async def create_template(
        db: AsyncSession, user_id: UUID, data: TemplateCreate
    ) -> Template:
        template = Template(
            user_id=user_id,
            name=data.name,
            subject=data.subject,
            body_html=data.body_html,
            body_text=data.body_text,
            folder_id=data.folder_id,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def get_templates(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(Template)
            .where(Template.user_id == user_id)
            .order_by(Template.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_template(db: AsyncSession, template_id: UUID) -> Template:
        result = await db.execute(
            select(Template).where(Template.id == template_id)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise ValueError("Template not found")
        return template

    @staticmethod
    async def update_template(
        db: AsyncSession, template_id: UUID, data: TemplateUpdate
    ) -> Template:
        template = await TemplateService.get_template(db, template_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def delete_template(db: AsyncSession, template_id: UUID) -> bool:
        template = await TemplateService.get_template(db, template_id)
        await db.delete(template)
        await db.commit()
        return True

    @staticmethod
    async def duplicate_template(
        db: AsyncSession, template_id: UUID
    ) -> Template:
        original = await TemplateService.get_template(db, template_id)
        template = Template(
            user_id=original.user_id,
            name=f"{original.name} (Copy)",
            subject=original.subject,
            body_html=original.body_html,
            body_text=original.body_text,
            folder_id=original.folder_id,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    def render_template(template: Template, variables: dict) -> dict:
        def replace_vars(text: str) -> str:
            if not text:
                return text
            pattern = re.compile(r"\{\{(\w+)\}\}")
            def replacer(match):
                key = match.group(1)
                return str(variables.get(key, match.group(0)))
            return pattern.sub(replacer, text)

        return {
            "subject": replace_vars(template.subject),
            "body_html": replace_vars(template.body_html),
            "body_text": replace_vars(template.body_text),
        }

    @staticmethod
    async def preview_template(
        db: AsyncSession, template_id: UUID, variables: dict
    ) -> dict:
        template = await TemplateService.get_template(db, template_id)
        return TemplateService.render_template(template, variables)

    @staticmethod
    async def test_send(
        db: AsyncSession,
        user_id: UUID,
        template_id: UUID,
        test_email: str,
        variables: dict,
    ) -> bool:
        template = await TemplateService.get_template(db, template_id)
        rendered = TemplateService.render_template(template, variables)
        from app.utils.gmail_client import GmailClient
        result = await db.execute(
            select(GmailAccount)
            .where(GmailAccount.user_id == user_id, GmailAccount.is_active == True)
            .limit(1)
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError("No active Gmail account found")
        from app.models.gmail import GmailAccount
        client = GmailClient(account)
        try:
            client.send_email(
                to=test_email,
                subject=rendered["subject"],
                body_html=rendered["body_html"],
                body_text=rendered["body_text"],
            )
            return True
        except Exception:
            return False

    @staticmethod
    async def create_folder(
        db: AsyncSession, user_id: UUID, name: str
    ) -> TemplateFolder:
        folder = TemplateFolder(user_id=user_id, name=name)
        db.add(folder)
        await db.commit()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def get_folders(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(TemplateFolder)
            .where(TemplateFolder.user_id == user_id)
            .order_by(TemplateFolder.name)
        )
        return list(result.scalars().all())
