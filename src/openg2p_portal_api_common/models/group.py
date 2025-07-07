from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict

from .group_membership import GroupMember
from .registrant import RegistrantBase


class GroupType(Enum):
    FAMILY = "Family"
    HOUSEHOLD = "Household"


class Group(RegistrantBase):
    model_config = ConfigDict(from_attributes=True)

    name: str
    is_group: bool = True
    kind: Optional[GroupType] = None
    members: Optional[List[GroupMember]]


class GroupRequest(RegistrantBase):
    name: str
    kind: Optional[GroupType] = None
    members: Optional[List[GroupMember]]
