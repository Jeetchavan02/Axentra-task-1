"""Add common software vendors to the company of a registered user.

Usage, from backend/:
    PYTHONPATH=src uv run python scripts/seed_vendors.py you@example.com

Safe to run again: vendors the company already has are left unchanged.
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database import SessionFactory, engine
from modules.V1.AuthManager.models import User
from modules.V1.VendorManager.models import Vendor

VENDORS = {
    "Slack": "https://slack.com/",
    "Figma": "https://www.figma.com/",
    "GitHub": "https://github.com/",
    "Notion": "https://www.notion.so/",
    "Zoom": "https://zoom.us/",
    "Google Workspace": "https://workspace.google.com/",
    "Microsoft 365": "https://www.microsoft.com/microsoft-365/",
    "Atlassian": "https://www.atlassian.com/",
    "Canva": "https://www.canva.com/",
    "Dropbox": "https://www.dropbox.com/",
}


async def seed(email: str) -> int:
    async with SessionFactory() as db:
        company_id = await db.scalar(select(User.company_id).where(User.email == email.lower()))
        if company_id is None:
            raise SystemExit(f"No registered user with email {email}")
        rows = [
            {"company_id": company_id, "name": name, "website": website}
            for name, website in VENDORS.items()
        ]
        result = await db.execute(
            insert(Vendor)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["company_id", "name"])
            .returning(Vendor.id)
        )
        added = len(result.all())
        await db.commit()
    await engine.dispose()
    return added


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(f"Added {asyncio.run(seed(sys.argv[1]))} vendors")
