from datetime import datetime

from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy import Column, DateTime, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Define many-to-many association table
g2p_group_membership_g2p_group_membership_kind_rel = Table(
    "g2p_group_membership_g2p_group_membership_kind_rel",
    BaseORMModel.metadata,
    Column(
        "g2p_group_membership_id",
        ForeignKey("g2p_group_membership.id"),
        primary_key=True,
    ),
    Column(
        "g2p_group_membership_kind_id",
        ForeignKey("g2p_group_membership_kind.id"),
        primary_key=True,
    ),
)


class G2PGroupMembershipORM(BaseORMModel):
    __tablename__ = "g2p_group_membership"

    id: Mapped[int] = mapped_column(primary_key=True)
    group: Mapped[int] = mapped_column(ForeignKey("res_partner.id"))
    individual: Mapped[int] = mapped_column(ForeignKey("res_partner.id"))
    create_date: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    group_partner = relationship(
        "PartnerORM", foreign_keys=[group], back_populates="group_memberships"
    )

    individual_partner = relationship(
        "PartnerORM",
        foreign_keys=[individual],
        back_populates="individual_group_memberships",
    )

    # Many-to-Many Relationship with Membership Kind
    group_membership_kind = relationship(
        "G2PGroupMembershipKindORM",
        secondary=g2p_group_membership_g2p_group_membership_kind_rel,
        back_populates="group_memberships",
    )
