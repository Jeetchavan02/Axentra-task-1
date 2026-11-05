from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Company, User


class AuthDAO:
    """Queries only. Committing is the service's job, so it controls the transaction."""

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        return await db.scalar(select(User).where(User.email == email))

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        return await db.get(User, user_id)

    @staticmethod
    async def create_company_with_user(
        db: AsyncSession, company_name: str, email: str, password_hash: str, full_name: str
    ) -> User:
        company = Company(name=company_name)
        db.add(company)
        await db.flush()  # Assigns company.id without committing.
        user = User(
            company_id=company.id, email=email, password_hash=password_hash, full_name=full_name
        )
        db.add(user)
        await db.flush()
        return user
