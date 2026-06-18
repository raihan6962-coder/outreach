from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas import SpamTestCreate, SpamTestResponse
from app.services.spam_analyzer_service import SpamAnalyzerService

router = APIRouter()


@router.post("/analyze", response_model=SpamTestResponse, status_code=status.HTTP_201_CREATED)
async def analyze_spam(
    data: SpamTestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    spam_test = await SpamAnalyzerService.save_test(
        db,
        current_user.id,
        {
            "subject": data.subject,
            "body": data.body_html,
            "sender_email": data.from_name or current_user.email,
            "gmail_account_id": str(data.gmail_account_id),
        },
    )
    return SpamTestResponse(
        id=spam_test.id,
        user_id=spam_test.user_id,
        gmail_account_id=spam_test.gmail_account_id,
        subject=spam_test.subject,
        spam_score=spam_test.spam_score,
        spam_level="high" if spam_test.spam_score > 50 else "medium" if spam_test.spam_score > 20 else "low",
        recommendations=spam_test.recommendations or [],
        test_details={"deliverability_score": spam_test.deliverability_score},
        is_completed=True,
        created_at=spam_test.created_at,
        completed_at=spam_test.created_at,
    )


@router.get("/history", response_model=list[SpamTestResponse])
async def get_spam_test_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tests = await SpamAnalyzerService.get_history(db, current_user.id)
    return [
        SpamTestResponse(
            id=t.id,
            user_id=t.user_id,
            gmail_account_id=t.gmail_account_id,
            subject=t.subject,
            spam_score=t.spam_score,
            spam_level="high" if t.spam_score > 50 else "medium" if t.spam_score > 20 else "low",
            recommendations=t.recommendations or [],
            test_details={"deliverability_score": t.deliverability_score},
            is_completed=True,
            created_at=t.created_at,
            completed_at=t.created_at,
        )
        for t in tests
    ]
