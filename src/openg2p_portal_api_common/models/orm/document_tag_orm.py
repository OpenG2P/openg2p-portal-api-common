from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..orm.document_file_orm import g2p_document_tag_storage_file_rel


class DocumentTagORM(BaseORMModel):
    __tablename__ = "g2p_document_tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)

    documents = relationship(
        "DocumentFileORM",
        secondary=g2p_document_tag_storage_file_rel,
        back_populates="tags_ids",
    )
