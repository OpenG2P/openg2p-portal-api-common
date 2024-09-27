# from datetime import datetime
# from typing import Optional

# from pydantic import BaseModel, ConfigDict, Field, validator


# class ProgramMembership(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     partner_id: Optional[int] = None
#     program_id: Optional[int] = None
#     state: Optional[str] = None


# class ProgramBase(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     id: Optional[int]
#     name: Optional[str] = None
#     description: Optional[str] = None


# class Program(ProgramBase):
#     model_config = ConfigDict(from_attributes=True)

#     state: Optional[str] = None
#     has_applied: Optional[bool] = None
#     self_service_portal_form: Optional[int] = Field(default=None, exclude=True)
#     is_portal_form_mapped: Optional[bool] = False
#     is_multiple_form_submission: Optional[bool] = False
#     last_application_status: Optional[str] = None
#     is_reimbursement_program: Optional[bool] = None
#     active: Optional[bool] = None
#     create_date: Optional[datetime] = None

#     @validator("is_portal_form_mapped", pre=True, always=True)
#     def is_program_form_mapped(cls, v, values):
#         return bool(values.get("self_service_portal_form"))


# class ProgramSummary(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     program_name: Optional[str] = None
#     enrollment_status: Optional[str] = None
#     total_funds_awaited: Optional[float] = None
#     total_funds_received: Optional[float] = None


# class ApplicationDetails(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     program_name: Optional[str] = None
#     application_id: Optional[int] = None
#     date_applied: Optional[datetime] = None
#     application_status: Optional[str] = None


# class BenefitDetails(BaseModel):
#     model_config = ConfigDict(from_attributes=True)

#     program_name: Optional[str] = None
#     date_approved: Optional[datetime] = None
#     funds_awaited: Optional[float] = None
#     funds_received: Optional[float] = None
#     entitlement_reference_number: Optional[int] = None
#     # cycle_name: Optional[str]=None
