from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GroupMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int]
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    birthdate: Optional[date]
    gender: Optional[str]
    company_id: Optional[int]
    is_registrant: bool = True
    is_group: bool = False
    membership_kinds: Optional[List[str]] = Field(default_factory=list)


class GroupRegId(BaseModel):
    id_type: Optional[int]
    name: Optional[str]
    value: Optional[str]
    expiry_date: Optional[date]


class GroupDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int]
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    registration_date: Optional[date]
    address: Optional[str]
    company_id: Optional[int] = Field(default=1)
    is_registrant: bool = True
    is_group: bool = True
    reg_ids: Optional[List[GroupRegId]] = Field(default_factory=list)
    kind: Optional[int]
    group_kind: Optional[str]
    # members: Optional[List[GroupMember]] = Field(default_factory=list)
