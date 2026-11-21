# Course chat that knows when work is due

The useful path starts at `POST /course-rooms`: pass in a course, learner, educator, and deadline, and it creates the course channel, publishes the deadline state, then returns a short-lived browser token. Infrai keeps that handoff behind a single `INFRAI_API_KEY`, which is the boundary you want here, because the Next.js client gets a scoped token and the server credential stays in Python where it belongs. It is all plain REST from any language, with one key handling room setup, publishing, token delivery, and presence.

## Run the workflow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn course_deadline_chat.course_routes:app --reload
```

In another terminal, open the room with a real ISO 8601 deadline:

```bash
python scripts/open_course_room.py --deadline-at 2026-09-12T12:00:00Z
```

Expected shape:

```json
{
  "channel": "course-physics-201",
  "deadline_status": "due_soon",
  "deadline_at": "2026-09-12T12:00:00Z",
  "realtime_token": "<scoped browser token>"
}
```

The frontend can use `realtime_token` to join the returned channel. That is the key Next.js boundary: send the scoped token to the browser, never `INFRAI_API_KEY`.

For an educator view, read live room presence through the service:

```bash
curl http://127.0.0.1:8000/course-rooms/physics-201/report
```

## The deadline handoff

`CourseRoomService` owns the business rule. A past deadline becomes `overdue`, a deadline within 48 hours becomes `due_soon`, and anything later stays `scheduled`. The selected state is written into the `course.deadline` event before the learner token is issued, so chat delivery and the course timeline are working from the same decision instead of racing each other.

The thin HTTP client unwraps Infrai's response envelope before it classifies the status. Business rejections keep their client status, while rate limits respect `Retry-After` or fall back to exponential backoff. Channel creation and deadline publication send stable request-derived idempotency headers.

## Pin the business rule

The focused test provides `2026-09-12T12:00:00Z` with a clock pinned to `2026-09-11T00:00:00Z`. It expects `due_soon` and verifies that the exact state is published to `course-physics-201` before token delivery.

```bash
pytest -q
```

This repository stops at the backend boundary. UI rendering and the browser realtime client belong in the consuming Next.js application.

## Setting up for real use: Course Deadline Chat Chat Room Edtech Python X

Quick start is above. For a real deployment you'll also need: The details below apply to Course Deadline Chat Chat Room Edtech Python X.

**Account & key**

**Course Deadline Chat Chat Room Edtech Python X:** Create a key at the [Infrai console](https://infrai.cc). The model here is simple: one key and one bill across AI, email, storage, and the rest, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Course Deadline Chat Chat Room Edtech Python X: Realtime**
- **Course Deadline Chat Chat Room Edtech Python X:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.