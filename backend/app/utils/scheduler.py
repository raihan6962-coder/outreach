from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore


class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            timezone="UTC",
        )

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def add_campaign_job(self, campaign_id: str, func, trigger="interval", **trigger_args):
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=f"campaign_{campaign_id}",
            name=f"Campaign {campaign_id}",
            replace_existing=True,
            **trigger_args,
        )

    def remove_campaign_job(self, campaign_id: str):
        job_id = f"campaign_{campaign_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    def get_job(self, campaign_id: str):
        return self.scheduler.get_job(f"campaign_{campaign_id}")
