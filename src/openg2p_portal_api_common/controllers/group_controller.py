import logging
from typing import Annotated

from fastapi import Depends
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from ..config import Settings
from ..dependencies import JwtBearerAuth
from ..models.credentials import AuthCredentials
from ..models.group import Group
from ..models.group_membership import GroupMember
from ..services.group_service import GroupService

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class GroupController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._group_service = GroupService.get_component()

        self.router.tags += ["group"]

        self.router.add_api_route(
            "/group",
            self.get_group,
            responses={200: {"model": Group}},
            methods=["GET"],
        )
        self.router.add_api_route(
            "/group",
            self.create_group,
            responses={200: {"model": Group}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/group",
            self.update_group,
            responses={200: {"model": Group}},
            methods=["PUT"],
        )
        self.router.add_api_route(
            "/group/member",
            self.add_member_into_group,
            responses={200: {"model": GroupMember}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/group/members",
            self.get_all_group_members,
            responses={200: {"model": GroupMember}},
            methods=["GET"],
        )

    @property
    def group_service(self):
        if not self._group_service:
            self._group_service = GroupService.get_component()
        return self._group_service

    async def get_group(
        self,
        group_details: Group,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.get_group(group_details)

    async def create_group(
        self,
        group_details: Group,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.create_group(group_details)

    async def update_group(
        self,
        group_details: Group,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.update_group(group_details)

    async def add_member_into_group(
        self,
        group_member: GroupMember,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.add_member_to_group(
            group_id=id, member=group_member
        )

    async def get_all_group_members(
        self,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.add_member_to_group(
            group_id=id, member=group_member
        )
