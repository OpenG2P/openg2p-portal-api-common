from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy.orm import Mapped, mapped_column


class EntitlementORM(BaseORMModel):
    __tablename__ = "g2p_entitlement"

    id: Mapped[int] = mapped_column(primary_key=True)
    partner_id: Mapped[int] = mapped_column()
    cycle_id: Mapped[int] = mapped_column()
    state: Mapped[str] = mapped_column()
    initial_amount: Mapped[int] = mapped_column()
    ern: Mapped[int] = mapped_column()
    date_approved: Mapped[datetime] = mapped_column()
