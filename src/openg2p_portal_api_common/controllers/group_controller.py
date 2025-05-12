from typing import Annotated, Optional

from fastapi import Body, Depends
from openg2p_fastapi_common.errors.http_exceptions import UnauthorizedError
from openg2p_fastapi_auth.controllers.auth_controller import AuthController
from ..dependencies import JwtBearerAuth
from ..models.credentials import AuthCredentials

from ..models.group import GroupDetails, GroupMember
from ..services.group_services import GroupService


class GroupController(AuthController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._group_service = GroupService.get_component()

        self.router.prefix = "/portal"
        self.router.tags = ["portal"]

        self.router.add_api_route(
            "/group",
            self.create_group,
            responses={200: {"model": GroupDetails}},
            methods=["POST"],
        )

        self.router.add_api_route(
            "/group/{id}",
            self.get_group_by_id,
            responses={200: {"model": GroupDetails}},
            methods=["GET"],
        )
        self.router.add_api_route(
            "/group/{id}",
            self.update_group_by_id,
            responses={200: {"model": GroupDetails}},
            methods=["PUT"],
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
    ) -> GroupDetails:
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        return await self.group_service.create_group(group_details)

    async def update_group_by_id(
        self,
        id: int,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
        updated_group_details: Optional[GroupDetails] = Body(...),
    ) -> Optional[GroupDetails]:
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")
        return await self.group_service.update_group(updated_group_details, group_id=id)

    async def get_group_by_id(
        self,
        id: int,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ) -> GroupDetails:
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        group = await self.group_service.get_group_by_id(group_id=id)
        return group

    async def member_addition(
        self,
        id: int,
        group_member: GroupMember,
        auth: Annotated[AuthCredentials, Depends(JwtBearerAuth())],
    ) -> GroupMember:
        if not auth.partner_id:
            raise UnauthorizedError("Unauthorized. Partner Not Found in Registry.")

        group_meber = await self.group_service.add_member_to_group(
            group_id=id, group_member=group_member
        )
        return group_meber
