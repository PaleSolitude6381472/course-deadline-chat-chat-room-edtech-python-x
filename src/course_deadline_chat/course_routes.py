from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException

from .course_room_service import CourseRoomService, OpenCourseRoomRequest, OpenCourseRoomResult
from .infrai_realtime import InfraiError, InfraiRealtime


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set INFRAI_API_KEY before starting the service")
    realtime = InfraiRealtime(api_key)
    app.state.rooms = CourseRoomService(realtime)
    yield
    await realtime.close()


app = FastAPI(title="Course deadline chat", lifespan=lifespan)


def client_error(error: InfraiError) -> HTTPException:
    status = error.status_code if 400 <= error.status_code < 500 else 502
    return HTTPException(status_code=status, detail={"code": error.code, "message": str(error)})


@app.post("/course-rooms", response_model=OpenCourseRoomResult)
async def open_course_room(request: OpenCourseRoomRequest) -> OpenCourseRoomResult:
    try:
        return await app.state.rooms.open_room(request)
    except InfraiError as error:
        raise client_error(error) from error


@app.get("/course-rooms/{course_id}/report")
async def course_room_report(course_id: str) -> dict[str, object]:
    try:
        return await app.state.rooms.educator_report(course_id)
    except InfraiError as error:
        raise client_error(error) from error

