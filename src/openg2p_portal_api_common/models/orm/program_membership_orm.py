from datetime import datetime
from typing import List, Optional

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, and_, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .program_registrant_info_orm import ProgramRegistrantInfoORM


class ProgramMembershipORM(BaseORMModel):
    __tablename__ = "g2p_program_membership"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column(Integer())
    program_id: Mapped[int] = mapped_column(ForeignKey("g2p_program.id"))
    state: Mapped[str] = mapped_column(String())
    create_date: Mapped[datetime] = mapped_column(DateTime())

    # program = relationship("ProgramORM", back_populates="membership")
    program_reg_info: Mapped[Optional[List["ProgramRegistrantInfoORM"]]] = relationship(
        back_populates="membership"
    )

    @classmethod
    async def get_membership_by_id(cls, program_id: int, partner_id: int):
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            stmt = select(cls).where(
                and_(cls.program_id == program_id, cls.partner_id == partner_id)
            )

            result = await session.execute(stmt)
        return result.scalar()
