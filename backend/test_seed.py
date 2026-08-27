import asyncio
from app.db.database import AsyncSessionLocal, init_db
from app.api.v1.stats import seed_sample_emails

async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        try:
            res = await seed_sample_emails(session)
            print("Seed succeeded:", res)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
