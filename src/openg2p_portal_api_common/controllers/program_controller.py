# from typing import Annotated, List

# from fastapi import Depends
# from fastapi.responses import JSONResponse
# from openg2p_fastapi_common.controller import BaseController
# from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

# from ..config import Settings
# from ..dependencies import JwtBearerAuth
# from ..models.credentials import AuthCredentials
# from ..models.program import ApplicationDetails, BenefitDetails, Program, ProgramSummary
# from ..services.program_service import ProgramService

# _config = Settings.get_config()


# class ProgramController(BaseController):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self._program_service = ProgramService.get_component()

#         # self.router.prefix += "/program"
#         self.router.tags += ["portal"]

#         self.router.add_api_route(
#             "/program",
#             self.get_programs,
#             response_class=JSONResponse,
#             responses={200: {"model": List[Program]}},
#             methods=["GET"],
#         )

#         self.router.add_api_route(
#             "/program/{programid}",
#             self.get_program_by_id,
#             responses={200: {"model": Program}},
#             methods=["GET"],
#         )

#         self.router.add_api_route(
#             "/programdetails",
#             self.get_program_summary,
#             responses={200: {"model": List[ProgramSummary]}},
#             methods=["GET"],
#         )

#         self.router.add_api_route(
#             "/applicationdetails",
#             self.get_application_details,
#             responses={200: {"model": List[ApplicationDetails]}},
#             methods=["GET"],
#         )

#         self.router.add_api_route(
#             "/benefitdetails",
#             self.get_benefit_details,
#             responses={200: {"model": List[BenefitDetails]}},
#             methods=["GET"],
#         )

#     @property
#     def program_service(self):
#         if not self._program_service:
#             self._program_service = ProgramService.get_component()
#         return self._program_service

#     async def get_programs(
#         self, auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())]
#     ):
#         """
#         Retrieves a list of all programs. Requires authentication.

#         Args:

#             auth (AuthCredentials): Authentication credentials, obtained via JWT Bearer Auth.

#         Returns:

#             List[Program]: A list of program objects.
#         """
#         if not auth.partner_id:
#             raise UnauthorizedError(
#                 message="Unauthorized. Partner Not Found in Registry."
#             )
#         return await self.program_service.get_all_program_service(auth.partner_id)

#     async def get_program_by_id(
#         self, programid: int, auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())]
#     ):
#         """
#         Retrieves a specific program by its ID. Requires authentication.

#         Args:

#             programid (int): The ID of the program to retrieve.

#             auth (AuthCredentials): Authentication credentials, obtained via JWT Bearer Auth.

#         Returns:

#             Program: The requested program object.
#         """
#         if not auth.partner_id:
#             raise UnauthorizedError(
#                 message="Unauthorized. Partner Not Found in Registry."
#             )

#         return await self.program_service.get_program_by_id_service(
#             programid, auth.partner_id
#         )

#     async def get_program_summary(
#         self, auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())]
#     ):
#         """
#         Retrieves a summary of programs. Requires authentication.

#         Args:

#             auth (AuthCredentials): Authentication credentials, obtained via JWT Bearer Auth.

#         Returns:

#             List[ProgramSummary]:

#             A list of program summary objects. Retrieves program summaries, filtering by partner_id, grouping by program name and enrollment status, and calculating total funds awaited and received.
#         """
#         if not auth.partner_id:
#             raise UnauthorizedError(
#                 message="Unauthorized. Partner Not Found in Registry."
#             )
#         return await self.program_service.get_program_summary_service(auth.partner_id)

#     async def get_application_details(
#         self, auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())]
#     ):
#         """
#         Retrieves details of applications. Requires authentication.

#         Args:

#             auth (AuthCredentials): Authentication credentials, obtained via JWT Bearer Auth.

#         Returns:

#             List[ApplicationDetails]:

#             A list of application detail objects. Focuses on program name, application ID, date applied, and application status for each application linked to the partner_id.
#         """
#         if not auth.partner_id:
#             raise UnauthorizedError(
#                 message="Unauthorized. Partner Not Found in Registry."
#             )
#         return await self.program_service.get_application_details_service(
#             auth.partner_id
#         )

#     async def get_benefit_details(
#         self, auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())]
#     ):
#         """
#         Retrieves details of benefits associated with programs. Requires authentication.

#         Args:

#             auth (AuthCredentials): Authentication credentials, obtained via JWT Bearer Auth.

#         Returns:

#             List[BenefitDetails]:

#             A list of benefit detail objects. Fetches details like program name, enrollment status, funds awaited and received, and entitlement reference numbers for specified partner_id.
#         """
#         if not auth.partner_id:
#             raise UnauthorizedError(
#                 message="Unauthorized. Partner Not Found in Registry."
#             )
#         return await self.program_service.get_benefit_details_service(auth.partner_id)
