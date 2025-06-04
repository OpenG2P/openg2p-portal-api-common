from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RegistrantID(BaseModel):
    model_config = ConfigDict()

    id_type: Optional[str] = None
    value: Optional[str] = None
    expiry_date: Optional[date] = None


class BankDetails(BaseModel):
    model_config = ConfigDict()

    bank_name: Optional[str] = None
    acc_number: Optional[str] = None


class PhoneNumber(BaseModel):
    model_config = ConfigDict()

    phone_no: Optional[str] = None
    date_collected: Optional[date] = None


class Profile(BaseModel):
    ids: Optional[List[RegistrantID]] = None
    email: Optional[str] = None
    gender: Optional[str] = None
    # address: Optional[dict] = {}
    bank_ids: Optional[List[BankDetails]] = None
    addl_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    birthdate: Optional[date] = None
    phone_numbers: Optional[List[PhoneNumber]] = None
    birth_place: Optional[str] = None


class UpdateProfile(Profile):
    pass


class GetProfile(Profile):
    id: Optional[int] = None
