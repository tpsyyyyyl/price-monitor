"""Фоновий планувальник: щоденний скрейп усіх товарів о 6 ранку.

Стартує з FastAPI lifespan. Кожен запуск бере свіжу сесію БД і закриває її.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import SessionLocal
from .scraper.runner import run_all

logger = logging.getLogger("price_monitor.scheduler")

_scheduler = BackgroundScheduler()


def _scheduled_run() -> None:
    db = SessionLocal()
    try:
        summary = run_all(db)
        logger.info("Запланований скрейп завершено: %s", summary)
    finally:
        db.close()


def start_scheduler() -> None:
    if _scheduler.running:
        return
    _scheduler.add_job(
        _scheduled_run,
        CronTrigger(hour=6),
        id="daily_scrape",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Планувальник запущено (щоденний скрейп о 06:00).")


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Планувальник зупинено.")
