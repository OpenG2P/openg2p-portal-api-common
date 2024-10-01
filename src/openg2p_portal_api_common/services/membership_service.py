from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.orm.program_membership_orm import ProgramMembershipORM


class MembershipService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def check_and_create_mem(self, programid: int, partnerid: int) -> int:
        async_session_maker = async_sessionmaker(dbengine.get())
        async with async_session_maker() as session:
            membership = await ProgramMembershipORM.get_membership_by_id(
                programid, partnerid
            )

            if membership is None:
                membership = ProgramMembershipORM(
                    program_id=programid, partner_id=partnerid, state="draft"
                )

                try:
                    session.add(membership)
                    await session.commit()
                    await session.refresh(membership)
                except IntegrityError:
                    return "Could not add to registrant to program!!"

        return membership.id
