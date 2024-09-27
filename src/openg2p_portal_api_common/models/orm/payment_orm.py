# from openg2p_fastapi_common.models import BaseORMModel
# from sqlalchemy import ForeignKey
# from sqlalchemy.orm import Mapped, mapped_column


# class PaymentORM(BaseORMModel):
#     __tablename__ = "g2p_payment"

#     id: Mapped[int] = mapped_column(primary_key=True)
#     entitlement_id: Mapped[int] = mapped_column(ForeignKey("g2p_entitlement.id"))
#     status: Mapped[str] = mapped_column()
#     amount_paid: Mapped[int] = mapped_column()
