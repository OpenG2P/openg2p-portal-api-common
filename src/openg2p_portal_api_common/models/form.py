from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Form(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    form_id: Optional[int] = Field(default=None, alias="id")
    title: Optional[str] = Field(defualt=None)
    state: Optional[str] = Field(defualt="DRAFT")
    active: Optional[bool] = Field(defualt=True)
    version: Optional[int] = Field(defualt=True)
    json_schema: Optional[str] = Field(default=None, alias="schema")
