import asyncio
from server.main import (
    get_user_profile,
    get_submission_history,
    find_problems,
    get_upcoming_contests,
    get_practice_recommendation,
)

async def main():
    print("=== get_user_profile ===")
    print(await get_user_profile("minamotoyuki"))

    print("\n=== get_submission_history ===")
    print(await get_submission_history("minamotoyuki", count=5))

    print("\n=== find_problems ===")
    print(await find_problems(min_rating=1600, max_rating=1800, tags="dp"))

    print("\n=== get_upcoming_contests ===")
    print(await get_upcoming_contests())

    print("\n=== get_practice_recommendation ===")
    print(await get_practice_recommendation("minamotoyuki"))  # ganti handle CF kamu

asyncio.run(main())