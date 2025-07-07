from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict

from .individual import Individual


class GroupMembershipKind(Enum):
    HEAD = "Head"


class GroupMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    individual: Individual = None
    kind: List[GroupMembershipKind] = []
    # create_date: datetime = None
    # write_date: datetime = None
