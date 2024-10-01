from datetime import datetime
from typing import Any, Dict

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, and_, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ProgramRegistrantInfoORM(BaseORMModel):
    __tablename__ = "g2p_program_registrant_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("g2p_program.id"))
    program_registrant_info: Mapped[Dict[str, Any]] = mapped_column(JSON(), default={})
    state: Mapped[str] = mapped_column(String())
    program_membership_id: Mapped[int] = mapped_column(
        ForeignKey("g2p_program_membership.id")
    )
    registrant_id: Mapped[int] = mapped_column(Integer())
    create_date: Mapped[datetime] = mapped_column(DateTime())
    application_id: Mapped[str] = mapped_column()

    membership = relationship("ProgramMembershipORM", back_populates="program_reg_info")

    @classmethod
    async def get_latest_reg_info(cls, program_membership_id: int):
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = (
                select(cls)
                .filter(cls.program_membership_id == program_membership_id)
                .order_by(cls.create_date.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar()


class ProgramRegistrantInfoDraftORM(BaseORMModel):
    __tablename__ = "g2p_program_registrant_info_draft"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("g2p_program.id"))
    registrant_id: Mapped[int] = mapped_column(Integer())
    program_registrant_info: Mapped[Dict[str, Any]] = mapped_column(JSON(), default={})

    @classmethod
    async def get_draft_reg_info_by_id(cls, program_id: int, registrant_id: int):
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = select(cls).where(
                and_(cls.program_id == program_id, cls.registrant_id == registrant_id)
            )
            result = await session.execute(stmt)
        return result.scalar()
