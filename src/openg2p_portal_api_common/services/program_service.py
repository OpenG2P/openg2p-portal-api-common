# from openg2p_fastapi_common.service import BaseService

# from ..models.orm.program_orm import ProgramORM
# from ..models.orm.program_registrant_info_orm import ProgramRegistrantInfoORM
# from ..models.program import (
#     ApplicationDetails,
#     BenefitDetails,
#     Program,
#     ProgramBase,
#     ProgramSummary,
# )


# class ProgramService(BaseService):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)

#     async def get_all_program_service(self, partnerid: int):
#         program_list = []
#         res = await ProgramORM.get_all_programs()

#         if res:
#             for program in res:
#                 response_dict = {
#                     "id": program.id,
#                     "name": program.name,
#                     "description": program.description,
#                     "state": "Not Applied",
#                     "has_applied": False,
#                     "self_service_portal_form": program.self_service_portal_form,
#                     "is_multiple_form_submission": program.is_multiple_form_submission,
#                     "last_application_status": "Not submitted any application",
#                     # "create date":program.create_date,
#                     "create_date": program.create_date.isoformat()
#                     if program.create_date
#                     else None,
#                 }
#                 membership = program.membership
#                 if membership:
#                     for member in membership:
#                         if member.partner_id == partnerid:
#                             response_dict.update(
#                                 {"state": member.state, "has_applied": True}
#                             )
#                             latest_reg_info = (
#                                 await ProgramRegistrantInfoORM.get_latest_reg_info(
#                                     member.id
#                                 )
#                             )
#                             if latest_reg_info:
#                                 response_dict[
#                                     "last_application_status"
#                                 ] = latest_reg_info.state

#                 program_list.append(Program(**response_dict))

#         return program_list

#     async def get_program_by_id_service(self, programid: int, partnerid: int):
#         res = await ProgramORM.get_all_by_program_id(programid)

#         if res:
#             response_dict = {
#                 "id": res.id,
#                 "name": res.name,
#                 "description": res.description,
#                 "state": "Not Applied",
#                 "has_applied": False,
#                 "self_service_portal_form": res.self_service_portal_form,
#                 "is_multiple_form_submission": res.is_multiple_form_submission,
#                 "last_application_status": "Not submitted any application",
#             }
#             membership = res.membership
#             if membership:
#                 for member in membership:
#                     if member.partner_id == partnerid:
#                         response_dict.update(
#                             {
#                                 "state": member.state,
#                                 "has_applied": True,
#                             }
#                         )
#                         latest_reg_info = (
#                             await ProgramRegistrantInfoORM.get_latest_reg_info(
#                                 member.id
#                             )
#                         )
#                         if latest_reg_info:
#                             response_dict[
#                                 "last_application_status"
#                             ] = latest_reg_info.state

#                         break

#             return Program(**response_dict)
#         else:
#             return {"message": f"Program with ID {programid} not found."}

#     async def get_program_by_key_service(self, keyword: str):
#         program_list = []
#         res = await ProgramORM.get_all_program_by_keyword(keyword)

#         if res:
#             for program in res:
#                 response_dict = {
#                     "id": program.id,
#                     "name": program.name,
#                     "description": program.description,
#                     "self_service_portal_form": program.self_service_portal_form,
#                     "is_multiple_form_submission": program.is_multiple_form_submission,
#                 }

#                 program_list.append(ProgramBase(**response_dict))
#         return program_list

#     async def get_program_summary_service(self, partnerid: int):
#         summary_details = await ProgramORM.get_program_summary(partnerid)
#         return [ProgramSummary.model_validate(program) for program in summary_details]

#     async def get_application_details_service(self, partnerid: int):
#         application_details = await ProgramORM.get_application_details(partnerid)
#         return [
#             ApplicationDetails.model_validate(program)
#             for program in application_details
#         ]

#     async def get_benefit_details_service(self, partnerid: int):
#         benefit_details = await ProgramORM.get_benefit_details(self, partnerid)
#         return [BenefitDetails.model_validate(program) for program in benefit_details]
