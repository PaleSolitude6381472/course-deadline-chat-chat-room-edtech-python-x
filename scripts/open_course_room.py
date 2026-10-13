from __future__ import annotations

import argparse
import json

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Open a course chat room and publish its deadline")
    parser.add_argument("--service-url", default="http://127.0.0.1:8000")
    parser.add_argument("--course-id", default="physics-201")
    parser.add_argument("--deadline-at", required=True)
    args = parser.parse_args()

    response = httpx.request(
        method="POST",
        url=f"{args.service_url}/course-rooms",
        json={
            "course_id": args.course_id,
            "course_title": "Physics 201",
            "learner_id": "learner-42",
            "educator_id": "educator-7",
            "deadline_at": args.deadline_at,
            "request_id": f"open-{args.course_id}-learner-42",
        },
        timeout=10.0,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()

