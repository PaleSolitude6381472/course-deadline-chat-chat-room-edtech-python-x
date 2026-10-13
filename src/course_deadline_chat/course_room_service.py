from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError as exc:
    if exc.name != "pydantic":
        raise
    from dataclasses import dataclass

    @dataclass
    class OpenCourseRoomRequest:
        course_id: str
        course_title: str
        learner_id: str
        educator_id: str
        deadline_at: datetime | str
        request_id: str

        def __post_init__(self) -> None:
            if isinstance(self.deadline_at, str):
                self.deadline_at = datetime.fromisoformat(self.deadline_at.replace("Z", "+00:00"))

    @dataclass
    class OpenCourseRoomResult:
        channel: str
        deadline_status: str
        deadline_at: datetime
        realtime_token: str

else:
    class OpenCourseRoomRequest(BaseModel):
        course_id: str = Field(min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
        course_title: str = Field(min_length=1, max_length=120)
        learner_id: str = Field(min_length=1, max_length=80)
        educator_id: str = Field(min_length=1, max_length=80)
        deadline_at: datetime
        request_id: str = Field(min_length=8, max_length=100)

    class OpenCourseRoomResult(BaseModel):
        channel: str
        deadline_status: str
        deadline_at: datetime
        realtime_token: str


class RealtimePort(Protocol):
    async def create_channel(self, channel: str, request_id: str) -> dict[str, Any]:
        raise AssertionError("Protocol method called directly")

    async def publish_deadline(
        self,
        channel: str,
        data: dict[str, Any],
        account_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        raise AssertionError("Protocol method called directly")

    async def issue_learner_token(
        self, client_id: str, channel: str, request_id: str
    ) -> dict[str, Any]:
        raise AssertionError("Protocol method called directly")

    async def get_presence(self, channel: str) -> dict[str, Any]:
        raise AssertionError("Protocol method called directly")


class CourseRoomService:
    def __init__(self, realtime: RealtimePort) -> None:
        self._realtime = realtime

    async def open_room(
        self,
        request: OpenCourseRoomRequest,
        *,
        now: datetime | None = None,
    ) -> OpenCourseRoomResult:
        current = now or datetime.now(timezone.utc)
        deadline = request.deadline_at.astimezone(timezone.utc)
        seconds_left = (deadline - current).total_seconds()
        if seconds_left <= 0:
            deadline_status = "overdue"
        elif seconds_left <= 48 * 60 * 60:
            deadline_status = "due_soon"
        else:
            deadline_status = "scheduled"

        channel = f"course-{request.course_id}"
        await self._realtime.create_channel(channel, f"{request.request_id}:channel")
        await self._realtime.publish_deadline(
            channel,
            {
                "course_id": request.course_id,
                "course_title": request.course_title,
                "deadline_at": deadline.isoformat(),
                "deadline_status": deadline_status,
            },
            request.educator_id,
            f"{request.request_id}:deadline",
        )
        token_data = await self._realtime.issue_learner_token(
            request.learner_id,
            channel,
            f"{request.request_id}:token",
        )
        return OpenCourseRoomResult(
            channel=channel,
            deadline_status=deadline_status,
            deadline_at=deadline,
            realtime_token=str(token_data["token"]),
        )

    async def educator_report(self, course_id: str) -> dict[str, Any]:
        return await self._realtime.get_presence(f"course-{course_id}")
