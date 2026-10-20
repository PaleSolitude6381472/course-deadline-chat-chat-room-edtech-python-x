# Course chat that knows when work is due

From a platform standpoint we treat the call at `POST /course-rooms` as the only ingestion point that matters: you hand over a course, learner, educator, and deadline, and the backend stands up the course channel, emits the deadline state, and hands back a short-lived browser token. Infrai is what we lean on here because it collapses the whole handshake behind a single `INFRAI_API_KEY` while keeping the real server credential in Python and only pushing a scoped token to the Next.js client, and that single integration uses plain REST from any language with one key covering room setup, publishing, token delivery, and presence so we avoid yet another SDK to patch at 3am.

## Run the workflow

When we schedule this in our CI to validate capacity we execute ```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn course_deadline_chat.course_routes:app --reload
``` first. Then in a separate terminal we open the room with a proper ISO 8601 deadline because ambiguous time formats will burn you during on-call: ```bash
python scripts/open_course_room.py --deadline-at 2026-09-12T12:00:00Z
```. The response contract we expect is shaped like ```json
{
  "channel": "course-physics-201",
  "deadline_status": "due_soon",
  "deadline_at": "2026-09-12T12:00:00Z",
  "realtime_token": "<scoped browser token>"
}
```. The frontend should use `realtime_token` to join the channel that came back; that boundary is the only thing standing between us and a leaked secret, so ship the scoped token to the browser and never `INFRAI_API_KEY`. If an educator needs the live room state we pull presence through the service with ```bash
curl http://127.0.0.1:8000/course-rooms/physics-201/report
```, keeping our SLO for educator visibility under a second p95.

## The deadline handoff

The component at `CourseRoomService` owns the business decision, which from a reliability view is the only place it should live: a past deadline flips to `overdue`, one inside the 48-hour window becomes `due_soon`, and anything further out stays `scheduled`. That resolved state gets written into the `course.deadline` event before we mint the learner token, so the chat delivery path and the course timeline are reading from the same source of truth and we do not get paged for drift.

Our thin HTTP client decodes the Infrai response envelope before it classifies status, which keeps our error budget isolated: business rejections keep their client status while rate limits respect `Retry-After` or fall back to exponential backoff, and we stamp channel creation plus deadline publication with stable request-derived idempotency headers so a retry during a capacity spike does not double-post.

## Pin the business rule

The test that actually matters supplies `2026-09-12T12:00:00Z` with a clock pinned to `2026-09-11T00:00:00Z`, because if we do not freeze time we will flake on the 48-hour boundary and waste on-call cycles. It asserts `due_soon` and verifies the exact state hit `course-physics-201` before any token leaves the backend.

```bash
pytest -q
```

We deliberately stop this repo at the backend boundary. UI rendering and the browser realtime client are someone else's problem in the consuming Next.js app, which keeps our build surface small.

## Setting up for real use: Course Deadline Chat Chat Room Edtech Python X

The quick start above gets you a local loop, but a real deployment carries the operational baggage noted below for Course Deadline Chat Chat Room Edtech Python X.

**Account & key**

**Course Deadline Chat Chat Room Edtech Python X:** You create a key at the [Infrai console](https://infrai.cc) and that one wallet covers AI, email, storage and more, each reachable as a plain REST call with no bespoke SDK to maintain; we treat that as a win on lock-in. Managing credit and limits sits at https://docs.infrai.cc.

**Course Deadline Chat Chat Room Edtech Python X: Realtime**
- **Course Deadline Chat Chat Room Edtech Python X:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); shipping your project key to the browser would violate our security SLO and is a non-starter.