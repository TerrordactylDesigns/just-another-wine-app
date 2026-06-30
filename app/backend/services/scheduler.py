from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from database import SessionLocal
from services import alert_engine

scheduler = AsyncIOScheduler()


def _get_db() -> Session:
    return SessionLocal()


def job_wine_windows():
    db = _get_db()
    try:
        alert_engine.evaluate_wine_windows(db)
    finally:
        db.close()


def job_camera_health():
    db = _get_db()
    try:
        alert_engine.evaluate_camera_health(db)
    finally:
        db.close()


def job_sensor_offline():
    db = _get_db()
    try:
        alert_engine.evaluate_sensor_offline(db)
    finally:
        db.close()


def job_system_health():
    db = _get_db()
    try:
        alert_engine.evaluate_system_health(db)
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(job_wine_windows, "cron", hour=0, minute=5, id="wine_windows")
    scheduler.add_job(job_camera_health, "interval", minutes=5, id="camera_health")
    scheduler.add_job(job_sensor_offline, "interval", minutes=5, id="sensor_offline")
    scheduler.add_job(job_system_health, "interval", minutes=15, id="system_health")
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown()
