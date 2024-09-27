from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class FormORM(BaseORMModel):
    __tablename__ = "formio_builder"

    id: Mapped[int] = mapped_column(primary_key=True)
    schema: Mapped[str] = mapped_column(String())
    # program = relationship("ProgramORM", back_populates="form")
