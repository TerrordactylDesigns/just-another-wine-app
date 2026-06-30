import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
import models
from routers import (
    cellars, zones, wines, summary, wishlist, alerts, sensors, cameras
)
from routers.inventory import inventory_router, purchases_router, consumed_router
from routers import images as images_router_module
from services.scheduler import start_scheduler, stop_scheduler
from services import stream_service
from seed import seed_sensor_types

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("just_another_wine_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_sensor_types()
    start_scheduler()
    logger.info("Just Another Wine App started")
    yield
    stop_scheduler()
    stream_service.stop_all()
    logger.info("Just Another Wine App stopped")


app = FastAPI(title="Just Another Wine App", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(cellars.router)
app.include_router(zones.router)
app.include_router(wines.router)
app.include_router(inventory_router)
app.include_router(purchases_router)
app.include_router(consumed_router)
app.include_router(wishlist.router)
app.include_router(summary.router)
app.include_router(sensors.router)
app.include_router(sensors.types_router)
app.include_router(cameras.router)
app.include_router(alerts.router)
app.include_router(alerts.rules_router)
app.include_router(images_router_module.router)

# Static frontend
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
