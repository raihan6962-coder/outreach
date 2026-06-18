from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.lead import Lead
from app.models.email_validation import EmailValidation
from app.utils.email_validator import (
    validate_email_syntax,
    check_mx_record,
    check_disposable,
    check_role_based,
    check_typos,
    check_smtp_connect,
)


class EmailValidationService:
    @staticmethod
    async def validate_lead_email(db: AsyncSession, lead: Lead) -> dict:
        email = lead.email
        syntax_valid, syntax_error = validate_email_syntax(email)
        mx_valid, mx_error = await check_mx_record(email)
        disposable = await check_disposable(email)
        role_based = await check_role_based(email)
        typo_suggestion = await check_typos(email)
        smtp_valid, smtp_error = await check_smtp_connect(email)

        is_valid = (
            syntax_valid
            and mx_valid
            and not disposable
            and not role_based
            and smtp_valid
        )
        score = sum(
            [
                syntax_valid,
                mx_valid,
                not disposable,
                not role_based,
                smtp_valid,
            ]
        ) * 20

        result = await db.execute(
            select(EmailValidation).where(EmailValidation.lead_id == lead.id)
        )
        validation = result.scalar_one_or_none()
        if validation:
            validation.is_valid = is_valid
            validation.score = score
            validation.syntax_valid = syntax_valid
            validation.mx_valid = mx_valid
            validation.disposable = disposable
            validation.role_based = role_based
            validation.typo_suggestion = typo_suggestion
            validation.smtp_valid = smtp_valid
            validation.syntax_error = syntax_error
            validation.mx_error = mx_error
            validation.smtp_error = smtp_error
        else:
            validation = EmailValidation(
                lead_id=lead.id,
                is_valid=is_valid,
                score=score,
                syntax_valid=syntax_valid,
                mx_valid=mx_valid,
                disposable=disposable,
                role_based=role_based,
                typo_suggestion=typo_suggestion,
                smtp_valid=smtp_valid,
                syntax_error=syntax_error,
                mx_error=mx_error,
                smtp_error=smtp_error,
            )
            db.add(validation)
        await db.commit()
        await db.refresh(validation)
        return {
            "email": email,
            "is_valid": is_valid,
            "score": score,
            "syntax_valid": syntax_valid,
            "mx_valid": mx_valid,
            "disposable": disposable,
            "role_based": role_based,
            "typo_suggestion": typo_suggestion,
            "smtp_valid": smtp_valid,
            "syntax_error": syntax_error,
            "mx_error": mx_error,
            "smtp_error": smtp_error,
        }

    @staticmethod
    async def validate_bulk(db: AsyncSession, lead_ids: list) -> dict:
        results = {"validated": 0, "failed": 0, "details": []}
        for lead_id in lead_ids:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                results["failed"] += 1
                results["details"].append({"lead_id": str(lead_id), "error": "Lead not found"})
                continue
            try:
                validation_result = await EmailValidationService.validate_lead_email(db, lead)
                results["validated"] += 1
                results["details"].append(validation_result)
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"lead_id": str(lead_id), "error": str(e)})
        return results

    @staticmethod
    async def get_validation_status(db: AsyncSession, lead_id: UUID) -> dict:
        result = await db.execute(
            select(EmailValidation).where(EmailValidation.lead_id == lead_id)
        )
        validation = result.scalar_one_or_none()
        if not validation:
            return {"lead_id": str(lead_id), "validated": False}
        return {
            "lead_id": str(lead_id),
            "validated": True,
            "is_valid": validation.is_valid,
            "score": validation.score,
            "syntax_valid": validation.syntax_valid,
            "mx_valid": validation.mx_valid,
            "disposable": validation.disposable,
            "role_based": validation.role_based,
            "smtp_valid": validation.smtp_valid,
        }

    @staticmethod
    async def is_valid_email(db: AsyncSession, email: str) -> bool:
        result = await db.execute(
            select(EmailValidation)
            .join(Lead, EmailValidation.lead_id == Lead.id)
            .where(Lead.email == email)
            .order_by(EmailValidation.created_at.desc())
            .limit(1)
        )
        validation = result.scalar_one_or_none()
        if validation:
            return validation.is_valid
        syntax_valid, _ = validate_email_syntax(email)
        mx_valid, _ = await check_mx_record(email)
        disposable = await check_disposable(email)
        role_based = await check_role_based(email)
        smtp_valid, _ = await check_smtp_connect(email)
        return syntax_valid and mx_valid and not disposable and not role_based and smtp_valid
