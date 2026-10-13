import asyncio
from datetime import datetime, timezone
from typing import Any

from course_deadline_chat.course_room_service import CourseRoomService, OpenCourseRoomRequest


class RecordingRealtime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    async def create_channel(self, channel: str, request_id: str) -> dict[str, Any]:
        self.calls.append(("create", {"channel": channel, "request_id": request_id}))
        return {"channel": channel}

    async def publish_deadline(
        self,
        channel: str,
        data: dict[str, Any],
        account_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        self.calls.append(("publish", {"channel": channel, "data": data, "account_id": account_id}))
        return {"published": True}

    async def issue_learner_token(
        self, client_id: str, channel: str, request_id: str
    ) -> dict[str, Any]:
        self.calls.append(
            ("token", {"client_id": client_id, "channel": channel, "request_id": request_id})
        )
        return {"token": "browser-token"}

    async def get_presence(self, channel: str) -> dict[str, Any]:
        return {"channel": channel, "members": []}


def test_deadline_within_48_hours_is_published_as_due_soon() -> None:
    asyncio.run(check_deadline_handoff())


async def check_deadline_handoff() -> None:
    realtime = RecordingRealtime()
    service = CourseRoomService(realtime)
    request = OpenCourseRoomRequest(
        course_id="physics-201",
        course_title="Physics 201",
        learner_id="learner-42",
        educator_id="educator-7",
        deadline_at="2026-09-12T12:00:00Z",
        request_id="request-1234",
    )

    result = await service.open_room(
        request,
        now=datetime(2026, 9, 11, 0, 0, tzinfo=timezone.utc),
    )

    assert result.deadline_status == "due_soon"
    assert result.channel == "course-physics-201"
    assert realtime.calls[1] == (
        "publish",
        {
            "channel": "course-physics-201",
            "data": {
                "course_id": "physics-201",
                "course_title": "Physics 201",
                "deadline_at": "2026-09-12T12:00:00+00:00",
                "deadline_status": "due_soon",
            },
            "account_id": "educator-7",
        },
    )
    assert realtime.calls[2][0] == "token"
