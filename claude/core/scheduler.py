"""core/scheduler.py – APScheduler-based background update manager."""
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

_scheduler = None
_lock = threading.Lock()


def _do_update():
    """Actual update job: scrape → store → re-score → re-index."""
    from core.scraper import run_all_scrapers
    from core.database import upsert_resource, get_all_resources, update_impact_score, log_scrape
    from core.impact_scorer import score_resource
    from core import embeddings as emb

    logger.info("Auto-update started")
    try:
        new_items = run_all_scrapers()
        added = 0
        for item in new_items:
            if upsert_resource(item):
                added += 1

        # Re-score all
        resources = get_all_resources()
        for r in resources:
            score = score_resource(r)
            update_impact_score(r["id"], score)

        # Rebuild semantic index
        resources = get_all_resources()
        emb.build_index(resources)

        log_scrape("all_sources", "success", added,
                   f"Added {added} new resources from {len(new_items)} scraped")
        logger.info(f"Auto-update complete: +{added} new resources")
    except Exception as e:
        from core.database import log_scrape
        log_scrape("all_sources", "error", 0, str(e))
        logger.error(f"Auto-update failed: {e}")


def start_scheduler(interval_hours: int = 6):
    """Start background scheduler if not already running."""
    global _scheduler
    with _lock:
        if _scheduler is not None:
            return
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger

            _scheduler = BackgroundScheduler(
                job_defaults={"coalesce": True, "max_instances": 1}
            )
            _scheduler.add_job(
                _do_update,
                trigger=IntervalTrigger(hours=interval_hours),
                id="auto_update",
                name="SDG Resource Auto-Update",
                replace_existing=True,
            )
            _scheduler.start()
            logger.info(f"Scheduler started (every {interval_hours}h)")
        except Exception as e:
            logger.error(f"Scheduler start failed: {e}")


def stop_scheduler():
    global _scheduler
    with _lock:
        if _scheduler and _scheduler.running:
            _scheduler.shutdown(wait=False)
            _scheduler = None


def trigger_manual_update():
    """Trigger an immediate update in a background thread."""
    t = threading.Thread(target=_do_update, daemon=True)
    t.start()
    return t


def get_scheduler_status() -> dict:
    global _scheduler
    if _scheduler is None:
        return {"running": False, "jobs": []}
    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else "N/A",
        })
    return {"running": _scheduler.running, "jobs": jobs}
