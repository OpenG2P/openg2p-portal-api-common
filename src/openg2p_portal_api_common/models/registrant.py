from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RegistrantID(BaseModel):
    model_config = ConfigDict()

    id_type: Optional[str] = None
    value: Optional[str] = None
    status: Optional[str] = None
    expiry_date: Optional[date] = None


class PhoneNumber(BaseModel):
    model_config = ConfigDict()

    phone_no: Optional[str] = None
    date_collected: Optional[date] = None


class RegistrantBase(BaseModel):
    ids: Optional[List[RegistrantID]] = None
    email: Optional[str] = None
    address: Optional[str] = None
    phone_numbers: Optional[List[PhoneNumber]] = None
