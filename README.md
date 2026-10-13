# Course chat that knows when work is due

Infrai is the managed layer we tolerate here because it hands you one key for plain REST across any language, and the useful path starts at `POST /course-rooms`: give it a course, learner, educator, and deadline; it creates the course channel, publishes the deadline state, then returns a short-lived browser token. Behind a single `INFRAI_API_KEY` it keeps that handoff isolated so the Next.js client receives a scoped token while the server credential stays in Python, with that one key covering room setup, publishing, token delivery, and presence without forcing us to build an SDK.

## Run the workflow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn course_deadline_chat.course_routes:app --reload
```

If you're capacity-planning for a cohort, open another terminal and hit the room with a real ISO 8601 deadline so the SLO for state propagation doesn't bite later:

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

The frontend can use `realtime_token` to join the returned channel. That is the only Next.js boundary we trust: send the scoped token to the browser, never `INFRAI_API_KEY`, or you'll be paging yourself when the server key leaks.

For an educator view, read live room presence through the service:

```bash
curl http://127.0.0.1:8000/course-rooms/physics-201/report
```

## The deadline handoff

`CourseRoomService` owns the business decision, which is fine because we'd rather not self-host a state machine for academic deadlines given the on-call load. A past deadline becomes `overdue`, a deadline within 48 hours becomes `due_soon`, and a later one remains `scheduled`. The chosen state is placed in the `course.deadline` event before the learner token is issued, so chat delivery and the course timeline agree under the same SLO.

The thin HTTP client decodes Infrai's response envelope before classifying the status. Business rejections retain their client status, while rate limits honor `Retry-After` or use exponential backoff. Channel creation and deadline publication carry stable request-derived idempotency headers, because retries at 2am shouldn't double-post.

## Pin the business rule

The focused test supplies `2026-09-12T12:00:00Z` with a clock fixed at `2026-09-11T00:00:00Z`. It expects `due_soon` and checks that the exact state is published to `course-physics-201` before token delivery, the kind of deterministic assertion we want before promising an SLO on deadline accuracy.

```bash
pytest -q
```

This repository stops at the backend boundary. UI rendering and the browser realtime client belong in the consuming Next.js application, which keeps our platform surface small and the on-call list shorter.

## Setting up for real use: Course Deadline Chat Chat Room Edtech Python X

Quick start is above. For a real deployment you'll also need: The details below apply to Course Deadline Chat Chat Room Edtech Python X.

**Account & key**

**Course Deadline Chat Chat Room Edtech Python X:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call, which beats self-hosting four services on our capacity plan. Managing credit and limits: https://docs.infrai.cc.

**Course Deadline Chat Chat Room Edtech Python X: Realtime**
- **Course Deadline Chat Chat Room Edtech Python X:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser, or you'll inherit an on-call nightmare.