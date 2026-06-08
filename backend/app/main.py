import os
from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_session, init_database
from .models import Item as ItemModel, Notification as NotificationModel
from .notifications import (
    close_notifications,
    connect_notifications,
    publish_notification,
    subscribe_notifications,
)
from .schemas import Item, ItemCreate, Notification, NotificationCreate


def get_cors_origins() -> list[str]:
    origins = os.getenv("CORS_ORIGINS")

    if origins is None:
        return ["http://127.0.0.1:5173", "http://localhost:5173"]

    return [origin.strip() for origin in origins.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    await connect_notifications()

    try:
        yield
    finally:
        await close_notifications()


app = FastAPI(title="Server Side Events Learning API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items", response_model=list[Item])
def list_items(
    session: Annotated[Session, Depends(get_session)],
) -> list[ItemModel]:
    statement = select(ItemModel).order_by(ItemModel.id.desc())
    return list(session.scalars(statement))


@app.post("/items", response_model=Item, status_code=201)
def create_item(
    item: ItemCreate,
    session: Annotated[Session, Depends(get_session)],
) -> ItemModel:
    db_item = ItemModel(title=item.title)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.get("/notifications")
def get_notifications(
    session: Annotated[Session, Depends(get_session)],
) -> list[Notification]:
    statement = select(NotificationModel).order_by(NotificationModel.id.desc())
    return list(session.scalars(statement))


@app.get("/notifications/stream", response_class=EventSourceResponse)
async def stream_notifications() -> AsyncIterator[ServerSentEvent]:
    async for notification in subscribe_notifications():
        yield ServerSentEvent(raw_data=notification)


@app.post("/notifications", response_model=Notification, status_code=201)
async def create_notification(
    notification: NotificationCreate,
    session: Annotated[Session, Depends(get_session)],
) -> NotificationModel:
    db_notification = NotificationModel(message=notification.message)
    session.add(db_notification)
    session.commit()
    session.refresh(db_notification)

    event = Notification.model_validate(db_notification)
    await publish_notification(event)

    return db_notification
