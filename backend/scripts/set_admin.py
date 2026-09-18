import argparse
import asyncio
import uuid

from sqlalchemy import select

from app.db.models import Account
from app.db.session import session_factory


async def set_admin(account_id: uuid.UUID, enabled: bool) -> None:
    async with session_factory() as db:
        account = await db.scalar(select(Account).where(Account.id == account_id))
        if account is None or account.status == "deleted":
            raise SystemExit("Account not found or deleted.")
        if account.account_type != "registered":
            raise SystemExit("Administrator role requires a registered account.")
        account.is_admin = enabled
        await db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Grant or revoke RoadTalk administrator authorization locally."
    )
    parser.add_argument("account_id", type=uuid.UUID)
    parser.add_argument("--revoke", action="store_true")
    args = parser.parse_args()
    asyncio.run(set_admin(args.account_id, not args.revoke))
    print("administrator role revoked" if args.revoke else "administrator role granted")


if __name__ == "__main__":
    main()
