from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pipeline import PipelineStage, LeadPipeline


class PipelineService:
    @staticmethod
    async def get_stages(db: AsyncSession, user_id: UUID) -> list:
        result = await db.execute(
            select(PipelineStage)
            .where(PipelineStage.user_id == user_id)
            .order_by(PipelineStage.order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_stage(
        db: AsyncSession, user_id: UUID, name: str, color: str
    ) -> PipelineStage:
        stages_result = await db.execute(
            select(PipelineStage)
            .where(PipelineStage.user_id == user_id)
            .order_by(PipelineStage.order.desc())
            .limit(1)
        )
        last_stage = stages_result.scalar_one_or_none()
        next_order = (last_stage.order + 1) if last_stage else 0

        stage = PipelineStage(
            user_id=user_id,
            name=name,
            color=color,
            order=next_order,
        )
        db.add(stage)
        await db.commit()
        await db.refresh(stage)
        return stage

    @staticmethod
    async def update_stage(
        db: AsyncSession, stage_id: UUID, data: dict
    ) -> PipelineStage:
        result = await db.execute(
            select(PipelineStage).where(PipelineStage.id == stage_id)
        )
        stage = result.scalar_one_or_none()
        if not stage:
            raise ValueError("Pipeline stage not found")
        for field, value in data.items():
            if hasattr(stage, field):
                setattr(stage, field, value)
        await db.commit()
        await db.refresh(stage)
        return stage

    @staticmethod
    async def delete_stage(db: AsyncSession, stage_id: UUID) -> bool:
        result = await db.execute(
            select(PipelineStage).where(PipelineStage.id == stage_id)
        )
        stage = result.scalar_one_or_none()
        if not stage:
            raise ValueError("Pipeline stage not found")
        await db.delete(stage)
        await db.commit()
        return True

    @staticmethod
    async def move_lead(
        db: AsyncSession, lead_id: UUID, stage_id: UUID
    ) -> LeadPipeline:
        result = await db.execute(
            select(LeadPipeline).where(LeadPipeline.lead_id == lead_id)
        )
        lead_pipeline = result.scalar_one_or_none()
        if lead_pipeline:
            lead_pipeline.stage_id = stage_id
        else:
            lead_pipeline = LeadPipeline(
                lead_id=lead_id,
                stage_id=stage_id,
            )
            db.add(lead_pipeline)
        await db.commit()
        await db.refresh(lead_pipeline)
        return lead_pipeline

    @staticmethod
    async def get_lead_stage(
        db: AsyncSession, lead_id: UUID
    ) -> PipelineStage:
        result = await db.execute(
            select(PipelineStage)
            .join(LeadPipeline, PipelineStage.id == LeadPipeline.stage_id)
            .where(LeadPipeline.lead_id == lead_id)
        )
        stage = result.scalar_one_or_none()
        if not stage:
            raise ValueError("Lead not in any pipeline stage")
        return stage

    @staticmethod
    async def get_leads_by_stage(db: AsyncSession, stage_id: UUID) -> list:
        result = await db.execute(
            select(LeadPipeline).where(LeadPipeline.stage_id == stage_id)
        )
        return list(result.scalars().all())
