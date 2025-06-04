from sqlalchemy import select
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, relationship


class G2PGroupKindORM(BaseORMModel):
    __tablename__ = "g2p_group_kind"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    partners = relationship("PartnerORM", back_populates="group_kind")

    @classmethod
    async def get_group_kind_name(cls, kind_id: int):
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            group_kind_record = await session.get(cls, kind_id)
            return group_kind_record.name if group_kind_record else None

    @classmethod
    async def get_group_kind_id_by_name(cls, kind_name: str):
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            group_kind_record = await session.execute(
                select(cls).where(cls.name == kind_name)
            )
            group_kind = group_kind_record.scalars().first()
            return group_kind.id if group_kind else None
