from openg2p_fastapi_common.models import BaseORMModel
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..orm.g2p_group_membership_orm import (
    g2p_group_membership_g2p_group_membership_kind_rel,
)


class G2PGroupMembershipKindORM(BaseORMModel):
    __tablename__ = "g2p_group_membership_kind"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    # Many-to-Many Relationship with Group Membership
    group_memberships = relationship(
        "G2PGroupMembershipORM",
        secondary=g2p_group_membership_g2p_group_membership_kind_rel,
        back_populates="group_membership_kind",
    )
