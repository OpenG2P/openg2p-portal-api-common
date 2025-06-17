from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class FormORM(BaseORMModel):
    __tablename__ = "formio_builder"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String())
    state: Mapped[str] = mapped_column(String())
    active: Mapped[bool] = mapped_column(Boolean())
    version: Mapped[int] = mapped_column(Integer())
    schema: Mapped[str] = mapped_column(String())
