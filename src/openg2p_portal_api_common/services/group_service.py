import logging
from datetime import date
from typing import List, Optional

import orjson
from fastapi.responses import JSONResponse
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..models.group import GroupDetails, GroupMember
from ..models.orm.draft_record_orm import G2PDraftRecordORM
from ..models.orm.g2p_group_kind_orm import G2PGroupKindORM
from ..models.orm.g2p_group_membership_kind_orm import G2PGroupMembershipKindORM
from ..models.orm.g2p_group_membership_orm import G2PGroupMembershipORM
from ..models.orm.partner_orm import PartnerORM
from ..models.orm.reg_id_orm import RegIDORM

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class GroupService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.async_session_maker = async_sessionmaker(
            dbengine.get(), expire_on_commit=False
        )

    async def create_group(self, group_details: GroupDetails) -> int:
        if _config.registrant_draft_mode_enabled:
            handler = DraftGroupHandler(self)
        else:
            handler = DirectGroupHandler(self)

        async with self.async_session_maker() as session:
            return await handler.create_group(session, group_details)

    async def add_member_to_group(self, group_id: int, member: GroupMember) -> int:
        if _config.registrant_draft_mode_enabled:
            handler = DraftGroupHandler(self)
        else:
            handler = DirectGroupHandler(self)

        async with self.async_session_maker() as session:
            return await handler.add_member_to_group(session, group_id, member)

    def parse_full_name(
        self, full_name: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        parts = full_name.strip().split()
        given_name = addl_name = family_name = None
        if len(parts) == 1:
            given_name = parts[0]
        elif len(parts) == 2:
            given_name, family_name = parts
        elif len(parts) >= 3:
            given_name = parts[0]
            addl_name = " ".join(parts[1:-1])
            family_name = parts[-1]
        return given_name, addl_name, family_name


class DraftGroupHandler:
    def __init__(self, service: GroupService):
        self.service = service

    def prepare_member_partner_data(self, member: GroupMember) -> dict:
        given_name, addl_name, family_name = self.service.parse_full_name(member.name)
        return {
            "is_group": False,
            "name": member.name,
            "given_name": given_name,
            "addl_name": addl_name,
            "family_name": family_name,
            "email": member.email,
            "birthdate": member.birthdate,
            "birth_place": member.birth_place,
            "gender": member.gender,
        }

    def _prepare_group_partner_data(self, group_details: GroupDetails) -> dict:
        partner_data = {
            "is_group": True,
            "name": group_details.name,
            "email": group_details.email,
            "address": group_details.address,
        }
        if group_details.reg_ids:
            formatted_reg_ids = []
            for idx, reg in enumerate(group_details.reg_ids):
                reg_entry = {
                    "id_type": reg.id_type,
                    "value": reg.value,
                    "expiry_date": reg.expiry_date or False,
                    "status": False,
                    "description": False,
                }
                formatted_reg_ids.append([0, f"virtual_reg_id_{idx}", reg_entry])
            partner_data["reg_ids"] = formatted_reg_ids
        return partner_data

    async def create_group(self, session, group_details: GroupDetails) -> int:
        partner_data = self._prepare_group_partner_data(group_details)
        draft_group = G2PDraftRecordORM(
            name=group_details.name,
            phone=group_details.phone,
            partner_data=orjson.dumps(partner_data).decode("utf-8"),
            is_group=True,
            state="draft",
            rejection_reason="",
        )
        session.add(draft_group)
        await session.commit()
        _logger.info(f"Registrant created as draft: {draft_group.id}")
        return draft_group.id

    async def add_member_to_group(
        self, session, group_id: int, member: GroupMember
    ) -> int:
        draft_group = await session.get(G2PDraftRecordORM, group_id)
        if not draft_group:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": ["Draft group not found."]},
            )
        draft_member = await self._create_draft_member(session, member)
        if draft_group.group_member_ids_json is None:
            draft_group.group_member_ids_json = []
        draft_group.group_member_ids_json.append(draft_member.id)
        await session.commit()
        return draft_member.id

    async def _create_draft_member(
        self, session, member: GroupMember
    ) -> G2PDraftRecordORM:
        given_name, addl_name, family_name = self.service.parse_full_name(member.name)
        partner_data = self.prepare_member_partner_data(member)
        draft_member = G2PDraftRecordORM(
            name=member.name,
            phone=member.phone,
            given_name=given_name,
            addl_name=addl_name,
            family_name=family_name,
            gender=member.gender,
            partner_data=orjson.dumps(partner_data).decode("utf-8"),
            is_group=False,
            state="draft",
            rejection_reason="",
        )
        session.add(draft_member)
        await session.commit()
        return draft_member


class DirectGroupHandler:
    def __init__(self, service: GroupService):
        self.service = service

    async def create_group(self, session, group_details: GroupDetails) -> int:
        group_kind_id = await G2PGroupKindORM.get_group_kind_id_by_name(
            group_details.group_kind
        )
        new_group = PartnerORM(
            name=group_details.name,
            email=group_details.email,
            phone=group_details.phone,
            address=group_details.address,
            kind=group_kind_id,
            company_id=1,
            is_registrant=True,
            is_group=True,
            registration_date=date.today(),
        )
        session.add(new_group)
        await session.flush()
        if group_details.reg_ids:
            await self._add_registration_ids(
                session, new_group.id, group_details.reg_ids
            )
        await session.commit()
        await session.refresh(new_group)
        return new_group.id

    async def add_member_to_group(
        self, session, group_id: int, member: GroupMember
    ) -> int:
        group = await session.get(PartnerORM, group_id)
        if not group:
            return None
        validation_result = await self.validate_member_addition(
            group_id, member, session
        )
        if isinstance(validation_result, JSONResponse):
            return validation_result
        new_member = await self._create_member(session, member)
        await self._create_group_membership(
            session, group_id, new_member.id, member.membership_kinds
        )
        await session.commit()
        await session.refresh(new_member)
        return new_member.id

    async def _add_registration_ids(self, session, partner_id: int, reg_ids: List):
        for reg_id in reg_ids:
            session.add(
                RegIDORM(
                    partner_id=partner_id,
                    id_type=reg_id.id_type,
                    value=reg_id.value,
                    expiry_date=reg_id.expiry_date,
                )
            )

    async def _create_member(self, session, member: GroupMember) -> PartnerORM:
        given_name, addl_name, family_name = self.service.parse_full_name(member.name)
        new_member = PartnerORM(
            name=member.name,
            given_name=given_name,
            addl_name=addl_name,
            family_name=family_name,
            email=member.email,
            phone=member.phone,
            birthdate=member.birthdate,
            birth_place=member.birth_place,
            gender=member.gender,
            company_id=1,
            is_registrant=True,
            is_group=False,
            registration_date=date.today(),
        )
        session.add(new_member)
        await session.flush()
        return new_member

    async def _create_group_membership(
        self,
        session,
        group_id: int,
        member_id: int,
        membership_kinds: Optional[List[str]],
    ):
        group_membership = G2PGroupMembershipORM(group=group_id, individual=member_id)
        session.add(group_membership)
        await session.flush()
        if membership_kinds:
            kind_records = await session.execute(
                select(G2PGroupMembershipKindORM).where(
                    G2PGroupMembershipKindORM.name.in_(membership_kinds)
                )
            )
            kind_objects = kind_records.scalars().all()
            if kind_objects:
                await session.run_sync(
                    lambda sync_sess: group_membership.group_membership_kind.extend(
                        kind_objects
                    )
                )

    async def get_group_members(self, group_id: int, session) -> List[GroupMember]:
        group_members = []
        membership_records = await session.execute(
            select(G2PGroupMembershipORM).where(G2PGroupMembershipORM.group == group_id)
        )
        for membership in membership_records.scalars().all():
            individual_record = await session.get(PartnerORM, membership.individual)
            if individual_record:
                group_members.append(individual_record)
        return group_members

    async def get_member_membership_kinds(self, member_id: int) -> List[str]:
        async with self.service.async_session_maker() as session:
            membership_record = await session.execute(
                select(G2PGroupMembershipORM).where(
                    G2PGroupMembershipORM.individual == member_id
                )
            )
            membership = membership_record.scalars().first()
            membership_kinds = []
            if membership:
                await session.refresh(membership, ["group_membership_kind"])
                if membership.group_membership_kind:
                    kind_ids = [kind.id for kind in membership.group_membership_kind]
                    if kind_ids:
                        kind_records = await session.execute(
                            select(G2PGroupMembershipKindORM).where(
                                G2PGroupMembershipKindORM.id.in_(kind_ids)
                            )
                        )
                        membership_kinds = [
                            kind.name for kind in kind_records.scalars()
                        ]
            return membership_kinds

    async def validate_member_addition(
        self, group_id: int, member: GroupMember, session
    ) -> Optional[JSONResponse]:
        existing_members = await self.get_group_members(group_id, session)
        for existing_member in existing_members:
            if existing_member.name == member.name:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": [
                            "A member with this name already exists in the group."
                        ],
                    },
                )
        if member.membership_kinds and "Head" in member.membership_kinds:
            for existing_member in existing_members:
                existing_kinds = await self.get_member_membership_kinds(
                    existing_member.id
                )
                if "Head" in existing_kinds:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "message": [
                                "Head role is already assigned to another member. "
                                "Please remove the 'head' role from the existing member before assigning it to a new member."
                            ],
                        },
                    )
        return None
