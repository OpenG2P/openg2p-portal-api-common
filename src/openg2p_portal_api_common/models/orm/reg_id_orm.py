from datetime import datetime
from typing import List, Optional

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, ForeignKey, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RegIDORM(BaseORMModel):
    __tablename__ = "g2p_reg_id"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("res_partner.id"))
    id_type: Mapped[Optional[int]] = mapped_column()
    value: Mapped[str] = mapped_column()
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime())

    partner = relationship("PartnerORM", back_populates="reg_ids")

    @classmethod
    async def get_partner_by_reg_id(cls, id_type: int, value: str) -> List["RegIDORM"]:
        response = None
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = select(cls).filter(cls.id_type == id_type).filter(cls.value == value)
            result = await session.execute(stmt)

            response = list(result.scalars())
        return response

    @classmethod
    async def get_all_partner_ids(cls, id: int) -> List["RegIDORM"]:
        response = []
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = select(cls).filter(cls.partner_id == id)
            result = await session.execute(stmt)

            response = list(result.scalars())
        return response


class RegIDTypeORM(BaseORMModel):
    __tablename__ = "g2p_id_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    @classmethod
    async def get_id_type_name(cls, id_type: int):
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = select(cls).filter(cls.id == id_type)
            result = await session.execute(stmt)

            response = result.scalar()
        return response
