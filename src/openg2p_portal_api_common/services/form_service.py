from openg2p_fastapi_common.service import BaseService
from sqlalchemy import select
from ..models.orm.formio_builder_orm import FormORM
from openg2p_fastapi_common.context import dbengine
from sqlalchemy.ext.asyncio import async_sessionmaker
from ..errors.exception_handler import handle_exception


class FormService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.async_session_maker = async_sessionmaker(dbengine.get())

    async def list_all_form(self):
        async with self.async_session_maker() as session:
            try:
                stmt = select(FormORM)
                result = await session.execute(stmt)
                forms = result.scalars().all()
                return forms
            except Exception as e:
                handle_exception(e, "Error fetching forms")


     

       