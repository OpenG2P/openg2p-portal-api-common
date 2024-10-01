from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProgramForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    program_id: Optional[int]
    form_id: Optional[int] = Field(default=None, alias="id")
    json_schema: Optional[str] = Field(default=None, alias="schema")
    submission_data: Optional[dict] = {}
    program_name: Optional[str] = None
    program_description: Optional[str] = None


class ProgramRegistrantInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    program_registrant_info: Optional[dict] = {}
