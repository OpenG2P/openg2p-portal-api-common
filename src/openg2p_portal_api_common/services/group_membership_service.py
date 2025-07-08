import logging
from datetime import date, datetime
from typing import List, Optional

import orjson
from fastapi.responses import JSONResponse
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..config import Settings
from ..models.group import Group
from ..models.group_membership import GetGroupMember, GroupMember, GroupMembershipKind
from ..models.individual import Individual
from ..models.orm.draft_record_orm import G2PDraftRecordORM
from ..models.orm.group_membership_kind_orm import G2PGroupMembershipKindORM
from ..models.orm.group_membership_orm import G2PGroupMembershipORM
from ..models.orm.partner_orm import PartnerORM, PartnerPhoneNoORM
from ..models.orm.reg_id_orm import RegIDORM, RegIDTypeORM
from ..models.registrant import PhoneNumber, RegistrantID
from ..utils.registrant_utils import get_full_name, parse_full_name

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class GroupMembershipService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parse_full_name = parse_full_name
        self.async_session_maker = async_sessionmaker(
            dbengine.get(), expire_on_commit=False
        )

    async def add_member_to_group(
        self, group_id: int, data: GroupMember
    ) -> GetGroupMember:
        if _config.registrant_draft_mode_enabled:
            handler = DraftGroupMembershipHandler(self)
        else:
            handler = DirectGroupMembershipHandler(self)

        async with self.async_session_maker() as session:
            return await handler.add_member_to_group(session, group_id, data)

    async def get_all_group_members(
        self, group_id: int, data: GroupMember
    ) -> list[GetGroupMember]:
        pass

    async def validate_member_addition(
        self, group_id: int, data: GroupMember, session
    ) -> Optional[JSONResponse]:
        existing_members = await self.get_group_members(group_id, session)
        for existing_member in existing_members:
            if existing_member.name == data.name:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": [
                            "A member with this name already exists in the group."
                        ],
                    },
                )
        if data.membership_kind and "Head" in data.membership_kind:
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
        async with self.async_session_maker() as session:
            membership_record = await session.execute(
                select(G2PGroupMembershipORM).where(
                    G2PGroupMembershipORM.individual == member_id
                )
            )
            membership = membership_record.scalars().first()
            membership_kind = []
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
                        membership_kind = [kind.name for kind in kind_records.scalars()]
            return membership_kind


class DraftGroupMembershipHandler:
    def __init__(self, service: GroupMembershipService):
        self.service = service

    def prepare_member_partner_data(self, member: GroupMember) -> dict:
        individual = member.individual
        return {
            "is_group": False,
            "name": get_full_name(
                individual.given_name, individual.addl_name, individual.family_name
            ),
            "given_name": individual.given_name,
            "addl_name": individual.addl_name,
            "family_name": individual.family_name,
            "email": individual.email,
            "birthdate": individual.birthdate,
            "birth_place": individual.birth_place,
            "gender": individual.gender,
        }

    def _prepare_group_partner_data(self, data: Group) -> dict:
        partner_data = {
            "is_group": True,
            "name": data.name,
            "email": data.email,
            "address": data.address,
        }

        if data.reg_ids:
            formatted_reg_ids = []
            for idx, reg in enumerate(data.reg_ids):
                reg_entry = {
                    "id_type": reg.id_type,
                    "value": reg.value,
                    "expiry_date": reg.expiry_date or False,
                    "status": False,
                    "description": False,
                }
                formatted_reg_ids.append([0, f"virtual_reg_id_{idx}", reg_entry])
            partner_data["reg_ids"] = formatted_reg_ids

        if data.phone_numbers:
            formatted_phones = []
            for idx, phone in enumerate(data.phone_numbers):
                phone_entry = {
                    "phone_no": phone.phone_no,
                    "country_id": False,
                    "date_collected": datetime.now().strftime("%Y-%m-%d"),
                    "disabled": False,
                }
                formatted_phones.append([0, f"virtual_phone_id_{idx}", phone_entry])
            partner_data["phone_number_ids"] = formatted_phones

        return partner_data

    async def add_member_to_group(
        self, session, group_id: int, data: GroupMember
    ) -> GetGroupMember:
        draft_group = await session.get(G2PDraftRecordORM, group_id)
        if not draft_group:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "error_code": 404,
                    "message": f"Draft group not found with ID: {group_id}",
                },
            )

        draft_member = await self._create_draft_member(session, data)

        draft_group.group_member_ids_json = draft_group.group_member_ids_json or []
        draft_group.group_member_ids_json.append(draft_member.id)

        await session.commit()

        individual_data = Individual(
            id=draft_member.id,
            name=draft_member.name,
            given_name=draft_member.given_name,
            addl_name=draft_member.addl_name,
            family_name=draft_member.family_name,
            email=draft_member.email,
            birthdate=draft_member.birthdate,
            birth_place=draft_member.birth_place,
            gender=draft_member.gender,
            is_group=draft_member.is_group,
        )

        return GetGroupMember(
            individual=individual_data,
            membership_kind=data.membership_kind or [],
        )

    async def _create_draft_member(
        self, session, data: GroupMember
    ) -> G2PDraftRecordORM:
        partner_data = self.prepare_member_partner_data(data)
        individual = data.individual

        draft_member = G2PDraftRecordORM(
            name=get_full_name(
                individual.given_name,
                individual.addl_name,
                individual.family_name,
            ),
            given_name=individual.given_name,
            addl_name=individual.addl_name,
            family_name=individual.family_name,
            gender=individual.gender,
            email=individual.email,
            birthdate=individual.birthdate,
            birth_place=individual.birth_place,
            is_group=False,
            partner_data=orjson.dumps(partner_data).decode("utf-8"),
            state="draft",
            rejection_reason="",
        )

        session.add(draft_member)
        await session.flush()
        return draft_member


class DirectGroupMembershipHandler:
    def __init__(self, service: GroupMembershipService):
        self.service = service

    async def add_member_to_group(
        self, session, group_id: int, data: GroupMember
    ) -> GetGroupMember:
        group = await session.get(PartnerORM, group_id)
        if not group:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "error_code": 404,
                    "message": f"Group not found with ID: {group_id}",
                },
            )

        validation_result = await self.service.validate_member_addition(
            group_id, data, session
        )
        if isinstance(validation_result, JSONResponse):
            return validation_result

        new_member = await self._create_member(session, data)
        await self._create_group_membership(
            session, group_id, new_member.id, data.membership_kind
        )

        # Add registration IDs and phone numbers to new member
        reg_id_list = await self._add_registration_ids(
            session, new_member.id, data.individual.reg_ids or []
        )
        phone_list = await self._add_phone_numbers(
            session, new_member.id, data.individual.phone_numbers or []
        )

        await session.commit()
        await session.refresh(new_member)

        individual_data = Individual(
            id=new_member.id,
            name=new_member.name,
            given_name=new_member.given_name,
            addl_name=new_member.addl_name,
            family_name=new_member.family_name,
            email=new_member.email,
            address=new_member.address,
            birthdate=new_member.birthdate,
            birth_place=new_member.birth_place,
            gender=new_member.gender,
            is_group=new_member.is_group,
            reg_ids=reg_id_list,
            phone_numbers=phone_list,
        )

        return GetGroupMember(
            individual=individual_data,
            membership_kind=data.membership_kind or [],
        )

    async def _create_member(self, session, data: GroupMember) -> PartnerORM:
        new_member = PartnerORM(
            name=get_full_name(
                data.individual.given_name,
                data.individual.addl_name,
                data.individual.family_name,
            ),
            given_name=data.individual.given_name,
            addl_name=data.individual.addl_name,
            family_name=data.individual.family_name,
            email=data.individual.email,
            birthdate=data.individual.birthdate,
            birth_place=data.individual.birth_place,
            gender=data.individual.gender,
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
        membership_kind: List[GroupMembershipKind],
    ):
        group_membership = G2PGroupMembershipORM(group=group_id, individual=member_id)
        session.add(group_membership)
        await session.flush()

        if membership_kind:
            # Convert enums to strings
            kind_names = [kind.value for kind in membership_kind]

            kind_records = await session.execute(
                select(G2PGroupMembershipKindORM).where(
                    G2PGroupMembershipKindORM.name.in_(kind_names)
                )
            )
            kind_objects = kind_records.scalars().all()

            if kind_objects:
                await session.run_sync(
                    lambda sync_sess: group_membership.group_membership_kind.extend(
                        kind_objects
                    )
                )

    async def _add_registration_ids(
        self, session, partner_id: int, reg_ids: List
    ) -> List[RegistrantID]:
        added_reg_ids = []

        for reg_id in reg_ids:
            reg_type = await RegIDTypeORM.get_id_type_by_name(reg_id.id_type)
            if not reg_type:
                raise ValueError(f"Invalid ID type: {reg_id.id_type}")

            reg_record = RegIDORM(
                partner_id=partner_id,
                id_type=reg_type.id,
                value=reg_id.value,
                status=reg_id.status,
                expiry_date=reg_id.expiry_date,
            )
            session.add(reg_record)
            added_reg_ids.append(
                RegistrantID(
                    id_type=reg_id.id_type,
                    value=reg_id.value,
                    status=reg_id.status,
                    expiry_date=reg_id.expiry_date,
                )
            )

        await session.flush()
        return added_reg_ids

    async def _add_phone_numbers(
        self, session, partner_id: int, phone_numbers: List
    ) -> List[PhoneNumber]:
        added_phones = []

        for phone in phone_numbers:
            phone_record = PartnerPhoneNoORM(
                partner_id=partner_id,
                phone_no=phone.phone_no,
                date_collected=phone.date_collected,
            )
            session.add(phone_record)
            added_phones.append(
                PhoneNumber(
                    phone_no=phone.phone_no,
                    date_collected=phone.date_collected,
                )
            )

        await session.flush()
        return added_phones
