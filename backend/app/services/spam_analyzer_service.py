import re
from uuid import UUID
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.spam_test import SpamTest


class SpamAnalyzerService:
    SPAM_WORDS = [
        "free", "guarantee", "click here", "act now", "limited time",
        "congratulations", "you won", "winner", "cash", "bonus",
        "urgent", "immediate action", "order now", "don't delete",
        "exclusive offer", "amazing", "call now", "limited offer",
        "special promotion", "no cost", "no obligation", "risk-free",
        "double your", "earn money", "extra income", "financial freedom",
        "once in a lifetime", "satisfaction guaranteed", "stop snoring",
        "dear friend", "dear winner", "click below", "open now",
        "act today", "expires soon", "instant", "millions",
        "billion", "increase sales", "incredible deal",
    ]

    @staticmethod
    def analyze(subject: str, body: str, sender_email: str) -> dict:
        spam_word_count = SpamAnalyzerService._check_spam_words(subject + " " + body)
        caps_ratio = SpamAnalyzerService._check_caps_ratio(subject + " " + body)
        link_density = SpamAnalyzerService._check_link_density(body)
        html_ratio = SpamAnalyzerService._check_html_ratio(body)
        images_no_alt = SpamAnalyzerService._check_images(body)

        spam_score = min(
            spam_word_count * 10
            + (caps_ratio * 50 if caps_ratio > 0.3 else caps_ratio * 20)
            + (link_density * 30 if link_density > 0.3 else link_density * 10)
            + (html_ratio * 20 if html_ratio > 0.7 else 0)
            + (images_no_alt * 5),
            100,
        )
        deliverability_score = max(100 - spam_score, 0)

        results = {
            "spam_score": round(spam_score, 2),
            "deliverability_score": round(deliverability_score, 2),
            "spam_word_count": spam_word_count,
            "caps_ratio": round(caps_ratio, 4),
            "link_density": round(link_density, 4),
            "html_ratio": round(html_ratio, 4),
            "images_without_alt": images_no_alt,
        }
        results["recommendations"] = SpamAnalyzerService._generate_recommendations(
            results
        )
        return results

    @staticmethod
    def _check_spam_words(text: str) -> int:
        text_lower = text.lower()
        count = 0
        for word in SpamAnalyzerService.SPAM_WORDS:
            count += text_lower.count(word.lower())
        return count

    @staticmethod
    def _check_caps_ratio(text: str) -> float:
        if not text:
            return 0.0
        letters = [c for c in text if c.isalpha()]
        if not letters:
            return 0.0
        caps = sum(1 for c in letters if c.isupper())
        return caps / len(letters)

    @staticmethod
    def _check_link_density(body_html: str) -> float:
        if not body_html:
            return 0.0
        links = re.findall(r'<a\s[^>]*href="[^"]*"', body_html, re.IGNORECASE)
        text_length = len(re.sub(r"<[^>]+>", "", body_html))
        if text_length == 0:
            return 0.0
        return len(links) / (text_length / 100)

    @staticmethod
    def _check_html_ratio(html: str) -> float:
        if not html:
            return 0.0
        text_part = re.sub(r"<[^>]+>", "", html)
        if len(html) == 0:
            return 0.0
        return 1 - (len(text_part) / len(html))

    @staticmethod
    def _check_images(body_html: str) -> int:
        if not body_html:
            return 0
        images = re.findall(r"<img\s[^>]*>", body_html, re.IGNORECASE)
        count = 0
        for img in images:
            if 'alt=""' not in img and "alt=" not in img:
                count += 1
        return count

    @staticmethod
    def _generate_recommendations(results: dict) -> list:
        recommendations = []
        if results["spam_word_count"] > 3:
            recommendations.append(
                f"Reduce spam trigger words ({results['spam_word_count']} found)"
            )
        if results["caps_ratio"] > 0.3:
            recommendations.append(
                "Reduce uppercase text usage to avoid spam filters"
            )
        if results["link_density"] > 0.5:
            recommendations.append(
                "Reduce number of links in email body"
            )
        if results["html_ratio"] > 0.7:
            recommendations.append(
                "Reduce HTML-to-text ratio, add more plain text"
            )
        if results["images_without_alt"] > 2:
            recommendations.append(
                f"Add alt text to {results['images_without_alt']} images"
            )
        if results["spam_score"] > 50:
            recommendations.append(
                "High spam score detected, consider rewriting email content"
            )
        if not recommendations:
            recommendations.append("Email content looks clean")
        return recommendations

    @staticmethod
    async def get_history(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(SpamTest)
            .where(SpamTest.user_id == user_id)
            .order_by(SpamTest.created_at.desc())
            .limit(50)
        )
        return list(result.scalars().all())

    @staticmethod
    async def save_test(db: AsyncSession, user_id: UUID, data: dict) -> SpamTest:
        analysis = SpamAnalyzerService.analyze(
            data.get("subject", ""),
            data.get("body", ""),
            data.get("sender_email", ""),
        )
        spam_test = SpamTest(
            user_id=user_id,
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            sender_email=data.get("sender_email", ""),
            spam_score=analysis["spam_score"],
            deliverability_score=analysis["deliverability_score"],
            recommendations=analysis["recommendations"],
        )
        db.add(spam_test)
        await db.commit()
        await db.refresh(spam_test)
        return spam_test
