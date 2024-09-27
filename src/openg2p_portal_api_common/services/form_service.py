# import random
# from datetime import datetime

# from fastapi import HTTPException, status
# from openg2p_fastapi_common.context import dbengine
# from openg2p_fastapi_common.service import BaseService
# from sqlalchemy import select
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy.ext.asyncio import async_sessionmaker

# from ..models.form import ProgramForm
# # from ..models.orm.program_orm import ProgramORM
# from ..models.orm.program_registrant_info_orm import (
#     ProgramRegistrantInfoDraftORM,
#     ProgramRegistrantInfoORM,
# )
# from .membership_service import MembershipService
# from .partner_service import PartnerService


# class FormService(BaseService):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.membership_service = MembershipService.get_component()
#         self.partner_service = PartnerService.get_component()

#     async def get_program_form(self, program_id: int, registrant_id: int):
#         response_dict = {}

#         res = await ProgramORM.get_program_form(program_id)
#         if res:
#             response_dict = {
#                 "id": None,
#                 "program_id": res.id,
#                 "schema": None,
#                 "submission_data": None,
#                 "program_name": res.name,
#                 "program_description": res.description,
#             }

#             form = res.form
#             if form:
#                 response_dict.update(
#                     {
#                         "id": form.id,
#                         "schema": form.schema,
#                     }
#                 )
#             draft_submission_data = (
#                 await ProgramRegistrantInfoDraftORM.get_draft_reg_info_by_id(
#                     program_id, registrant_id
#                 )
#             )
#             if draft_submission_data:
#                 response_dict.update(
#                     {"submission_data": draft_submission_data.program_registrant_info}
#                 )

#             return ProgramForm(**response_dict)
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, detail="Program ID not Found"
#             )

#     async def create_form_draft(self, program_id: int, form_data, registrant_id: int):
#         async_session_maker = async_sessionmaker(dbengine.get())
#         async with async_session_maker() as session:
#             draft_form = await ProgramRegistrantInfoDraftORM.get_draft_reg_info_by_id(
#                 program_id, registrant_id
#             )

#             if draft_form is None:
#                 program_registrant_info = ProgramRegistrantInfoDraftORM(
#                     program_id=program_id,
#                     program_registrant_info=form_data.program_registrant_info,
#                     registrant_id=registrant_id,
#                 )

#                 try:
#                     session.add(program_registrant_info)

#                     await session.commit()
#                 except IntegrityError:
#                     return "Error: In creating the draft"

#             else:
#                 draft_form.program_registrant_info = form_data.program_registrant_info

#                 try:
#                     session.add(draft_form)
#                     await session.commit()
#                 except IntegrityError:
#                     return "Error: In updating the draft."

#         return "Successfully submitted the draft!!"

#     async def submit_application_form(
#         self, program_id: int, form_data, registrant_id: int
#     ):
#         async_session_maker = async_sessionmaker(dbengine.get())
#         async with async_session_maker() as session:
#             program = await session.get(
#                 ProgramORM, program_id
#             )  # Fetch the ProgramORM object
#             if not program:
#                 return "Error: Program not found."
#             # Check if multiple form submissions are allowed before checking for existing applications
#             if not program.is_multiple_form_submission:
#                 application = await session.execute(
#                     select(ProgramRegistrantInfoORM).filter(
#                         ProgramRegistrantInfoORM.program_id == program_id,
#                         ProgramRegistrantInfoORM.registrant_id == registrant_id,
#                     )
#                 )
#                 if application.scalars().first():
#                     return "Error: Multiple form submissions are not allowed for this program."

#             existing_application = await session.execute(
#                 select(ProgramRegistrantInfoORM).filter(
#                     ProgramRegistrantInfoORM.program_id == program_id,
#                     ProgramRegistrantInfoORM.registrant_id == registrant_id,
#                     ProgramRegistrantInfoORM.state.in_(
#                         ["active", "inprogress", "applied"]
#                     ),
#                 )
#             )
#             if existing_application.scalars().first():
#                 return "Error: There is already an active or in-progress application for this program."

#             try:
#                 program_membership_id = (
#                     await self.membership_service.check_and_create_mem(
#                         program_id, registrant_id
#                     )
#                 )
#             except ValueError as e:
#                 return str(e)
#             get_draft_reg_info = (
#                 await ProgramRegistrantInfoDraftORM.get_draft_reg_info_by_id(
#                     program_id, registrant_id
#                 )
#             )
#             application_id = self._compute_application_id()
#             create_date = datetime.now()

#             updated_partner_info = await self.partner_service.update_partner_info(
#                 registrant_id, form_data.program_registrant_info, session=session
#             )
#             cleaned_program_registrant_info = self.clean_program_registrant_info(
#                 form_data.program_registrant_info, updated_partner_info
#             )

#             program_registrant_info = ProgramRegistrantInfoORM(
#                 program_id=program_id,
#                 program_membership_id=program_membership_id,
#                 program_registrant_info=cleaned_program_registrant_info,
#                 state="active",
#                 registrant_id=registrant_id,
#                 application_id=application_id,
#                 create_date=create_date,
#             )

#             try:
#                 if get_draft_reg_info:
#                     session.add(program_registrant_info)
#                     await session.delete(get_draft_reg_info)
#                 else:
#                     session.add(program_registrant_info)

#                 await session.commit()
#             except IntegrityError:
#                 return "Error: Duplicate entry or integrity violation"

#         return (
#             f"Successfully applied into the program! Application ID: {application_id}"
#         )

#     def _compute_application_id(self):
#         d = datetime.today().strftime("%d")
#         m = datetime.today().strftime("%m")
#         y = datetime.today().strftime("%y")
#         random_number = str(random.randint(1, 100000))
#         return d + m + y + random_number.zfill(5)

#     def clean_program_registrant_info(
#         self, program_registrant_info, updated_partner_fields
#     ):
#         # Remove updated fields from program_registrant_info
#         if not updated_partner_fields:
#             return program_registrant_info
#         cleaned_info = {
#             key: value
#             for key, value in program_registrant_info.items()
#             if key not in updated_partner_fields
#         }
#         return cleaned_info
