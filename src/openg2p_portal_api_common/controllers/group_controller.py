import logging
from typing import Annotated

from fastapi import Depends
from openg2p_fastapi_auth.controllers.auth_controller import AuthController
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from ..config import Settings
from ..dependencies import JwtBearerAuth
from ..models.credentials import AuthCredentials
from ..models.group import GroupDetails, GroupMember
from ..services.group_service import GroupService

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class GroupController(AuthController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._group_service = GroupService.get_component()

        self.router.prefix = "/common"
        self.router.tags = ["portal common"]

        self.router.add_api_route(
            "/group",
            self.create_group,
            responses={200: {"model": GroupDetails}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/group/member/{id}",
            self.member_addition,
            responses={200: {"model": GroupMember}},
            methods=["POST"],
        )

    @property
    def group_service(self):
        if not self._group_service:
            self._group_service = GroupService.get_component()
        return self._group_service

    async def create_group(
        self,
        group_details: GroupDetails,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.create_group(group_details)

    async def member_addition(
        self,
        id: int,
        group_member: GroupMember,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.add_member_to_group(
            group_id=id, member=group_member
        )
