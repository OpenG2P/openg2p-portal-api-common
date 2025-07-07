from datetime import date
from typing import Optional

from .registrant import RegistrantBase


class Individual(RegistrantBase):
    given_name: Optional[str] = None
    addl_name: Optional[str] = None
    family_name: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[date] = None
    birth_place: Optional[str] = None
    is_group: bool = False


class UpdateIndividual(Individual):
    pass


class GetIndividual(Individual):
    id: int
