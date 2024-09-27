# from fastapi import Query
# from openg2p_fastapi_common.controller import BaseController

# from ..config import Settings
# from ..models.program import ProgramBase
# from ..services.program_service import ProgramService

# _config = Settings.get_config()


# class DiscoveryController(BaseController):
#     """
#     DiscoveryController handles program discovery-related operations.
#     It includes endpoints for searching and retrieving programs based on specific criteria.
#     """

#     def __init__(self, **kwargs):
#         """
#         Initializes the DiscoveryController with necessary components and configurations.
#         """
#         super().__init__(**kwargs)
#         self._program_service = ProgramService.get_component()

#         self.router.tags += ["portal"]

#         self.router.add_api_route(
#             "/discovery",
#             self.get_program_by_keyword,
#             responses={200: {"model": ProgramBase}},
#             methods=["GET"],
#         )

#     @property
#     def program_service(self):
#         """
#         Provides access to the program service component.
#         """
#         if not self._program_service:
#             self._program_service = ProgramService.get_component()
#         return self._program_service

#     async def get_program_by_keyword(
#         self,
#         keyword: str = Query(..., description="keyword to search"),
#         page: int = Query(None, description="page number for pagination"),
#         pagesize: int = Query(None, description="number of records in a page"),
#     ):
#         """
#         Retrieves programs by a search keyword. Supports pagination.

#         Args:

#             keyword (str): The keyword to search for in program names.

#             page (int, optional): The page number for paginated results.

#             pagesize (int, optional): The number of records to return per page.

#         Returns:

#             A list of programs that match the search criteria.
#         """
#         return await self.program_service.get_program_by_key_service(keyword)
