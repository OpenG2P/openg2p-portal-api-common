import logging
from typing import Annotated

from fastapi import Depends
from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError

from ..config import Settings
from ..dependencies import JwtBearerAuth
from ..models.credentials import AuthCredentials
from ..models.group import GetGroup, Group, UpdateGroup
from ..models.group_membership import GetGroupMember, GroupMember
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
            self.get_groups,
            responses={200: {"model": list[GetGroup]}},
            methods=["GET"],
        )
        self.router.add_api_route(
            "/group",
            self.create_group,
            responses={200: {"model": GetGroup}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/group/{group_id}",
            self.update_group,
            responses={200: {"model": Group}},
            methods=["PUT"],
        )
        self.router.add_api_route(
            "/group/member/{group_id}",
            self.add_member_into_group,
            responses={200: {"model": GetGroupMember}},
            methods=["POST"],
        )
        self.router.add_api_route(
            "/group/members/{group_id}",
            self.get_all_group_members,
            methods=["GET"],
        )

    @property
    def group_service(self):
        if not self._group_service:
            self._group_service = GroupService.get_component()
        return self._group_service

    async def get_groups(
        self,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ) -> list[GetGroup]:
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.get_groups_by_individual_id(auth.partner_id)

    async def create_group(
        self,
        data: Group,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ) -> GetGroup:
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.create_group(auth.partner_id, data)

    async def update_group(
        self,
        group_id: int,
        data: UpdateGroup,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.update_group(group_id, data)

    async def add_member_into_group(
        self,
        data: GroupMember,
        group_id: int,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ) -> GetGroupMember:
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.add_member_to_group(group_id, data)

    async def get_all_group_members(
        self,
        group_id: int,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ):
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.get_all_group_members(group_id)
