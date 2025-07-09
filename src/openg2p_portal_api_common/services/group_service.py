import logging
from datetime import date, datetime
from typing import List

import orjson
from fastapi.responses import JSONResponse
from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError
from openg2p_fastapi_common.service import BaseService
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..config import Settings
from ..models.group import GetGroup, Group, UpdateGroup
from ..models.group_membership import GroupMembershipKind
from ..models.orm.draft_record_orm import G2PDraftRecordORM
from ..models.orm.group_kind_orm import G2PGroupKindORM
from ..models.orm.group_membership_kind_orm import G2PGroupMembershipKindORM
from ..models.orm.group_membership_orm import G2PGroupMembershipORM
from ..models.orm.partner_orm import PartnerORM, PartnerPhoneNoORM
from ..models.orm.reg_id_orm import RegIDORM, RegIDTypeORM
from ..services.group_membership_service import (
    DirectGroupMembershipHandler,
    GroupMembershipService,
)
from ..services.individual_service import IndividualService
from ..utils.registrant_utils import parse_full_name

_config = Settings.get_config(strict=False)
_logger = logging.getLogger(_config.logging_default_logger_name)


class GroupService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parse_full_name = parse_full_name
        self.async_session_maker = async_sessionmaker(
            dbengine.get(), expire_on_commit=False
        )

    async def get_groups_by_individual_id(self, individual_id) -> List[GetGroup]:
        if _config.registrant_draft_mode_enabled:
            handler = DraftGroupHandler(self)
        else:
            handler = DirectGroupHandler(self)

        async with self.async_session_maker() as session:
            return await handler.get_groups_by_individual_id(session, individual_id)

    async def create_group(self, individual_id, data: Group) -> GetGroup:
        if _config.registrant_draft_mode_enabled:
            handler = DraftGroupHandler(self)
        else:
            handler = DirectGroupHandler(self)

        async with self.async_session_maker() as session:
            return await handler.create_group(session, individual_id, data)

    async def update_group(self, group_id: int, data: UpdateGroup) -> GetGroup:
        if _config.registrant_draft_mode_enabled:
            handler = DraftGroupHandler(self)
        else:
            handler = DirectGroupHandler(self)

        async with self.async_session_maker() as session:
            return await handler.update_group(session, group_id, data)


class DraftGroupHandler:
    def __init__(self, service: GroupService):
        self.service = service

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

    async def get_groups_by_individual_id(
        self, session: AsyncSession, individual_id: int
    ) -> List[GetGroup]:
        raise NotImplementedError(
            "'get_groups_by_individual_id' is not implemented yet."
        )

    async def create_group(
        self, session: AsyncSession, individual_id: int, data: Group
    ) -> GetGroup:
        try:
            partner_data = self._prepare_group_partner_data(data)

            draft_group = G2PDraftRecordORM(
                name=data.name,
                partner_data=orjson.dumps(partner_data).decode("utf-8"),
                is_group=True,
                state="draft",
                rejection_reason="",
            )
            session.add(draft_group)

            # TODO: Add current individual as group member
            await session.commit()

            _logger.info(f"Group draft created with ID: {draft_group.id}")

            # Prepare and return GetGroup response
            return GetGroup(
                id=draft_group.id,
                name=draft_group.name,
                email=data.email,
                address=data.address,
                reg_ids=data.reg_ids or [],
                kind=data.kind,
                membership_kind=data.membership_kind,
            )

        except Exception as e:
            await session.rollback()
            _logger.exception(
                f"Failed to create draft group for individual {individual_id}: {str(e)}"
            )
            raise InternalServerError(message="Could not create draft group") from e

    async def update_group(
        self, session: AsyncSession, group_id: int, data: Group
    ) -> GetGroup:
        try:
            draft_record = await session.get(G2PDraftRecordORM, group_id)
            if not draft_record:
                return JSONResponse(
                    status_code=404,
                    content={
                        "status": "error",
                        "error_code": 404,
                        "message": f"Draft record not found for group ID: {group_id}",
                    },
                )

            # Parse existing partner_data
            partner_data = orjson.loads(draft_record.partner_data)
            updated_fields = {}

            all_fields = draft_record.get_all_draft_orm_fields()

            for field in all_fields:
                value = getattr(data, field, None)
                if value is not None:
                    partner_data[field] = value
                    updated_fields[field] = value

            # Update reg_ids
            if data.reg_ids:
                formatted_reg_ids = []
                for idx, new_reg in enumerate(data.reg_ids):
                    reg_type = await RegIDTypeORM.get_id_type_by_name(new_reg.id_type)
                    if not reg_type:
                        raise ValueError(f"Invalid ID type: {new_reg.id_type}")
                    reg_entry = {
                        "id_type": reg_type.id,
                        "value": new_reg.value,
                        "expiry_date": new_reg.expiry_date or False,
                        "status": "",
                        "description": False,
                    }
                    formatted_reg_ids.append([0, f"virtual_reg_id_{idx}", reg_entry])

                partner_data["reg_ids"] = formatted_reg_ids
                updated_fields["reg_ids"] = formatted_reg_ids

            # Update phone_numbers
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
                updated_fields["phone_number_ids"] = formatted_phones

            if updated_fields:
                draft_record.partner_data = orjson.dumps(partner_data).decode("utf-8")
                _logger.info(
                    f"Draft group {group_id} updated with changes: {list(updated_fields.keys())}"
                )

            # TODO: update member and its membership kind
            await session.commit()

            return GetGroup(
                id=draft_record.id,
                name=partner_data.get("name"),
                phone=draft_record.phone,
                email=partner_data.get("email"),
                address=partner_data.get("address"),
                reg_ids=data.reg_ids or [],
                phone_numbers=data.phone_numbers or [],
                kind=data.kind,
                membership_kind=data.membership_kind,
            )

        except Exception as e:
            _logger.exception(f" Failed to update draft group {group_id}: {str(e)}")
            await session.rollback()
            raise InternalServerError(message="Could not update draft group") from e


class DirectGroupHandler:
    def __init__(self, service: GroupService):
        self.service = service

    async def get_groups_by_individual_id(
        self, session: AsyncSession, individual_id: int
    ) -> List[GetGroup]:
        try:
            # Fetch all group memberships for the individual
            membership_result = await session.execute(
                select(G2PGroupMembershipORM).where(
                    G2PGroupMembershipORM.individual == individual_id
                )
            )
            memberships = membership_result.scalars().all()

            groups: List[GetGroup] = []

            for membership in memberships:
                group_partner = await session.get(PartnerORM, membership.group)
                if not group_partner or not group_partner.is_group:
                    continue
                group = await self.get_group_by_group_id(session, group_partner.id)
                groups.append(group)

            return groups

        except Exception as e:
            _logger.exception(
                f"Failed to retrieve groups for individual {individual_id}: {str(e)}"
            )
            raise InternalServerError(
                detail="Could not retrieve group information"
            ) from e

    async def create_group(self, session, individual_id, data: Group) -> GetGroup:
        try:
            group_kind_id = await G2PGroupKindORM.get_group_kind_id_by_name(
                data.kind.value if data.kind else None
            )

            new_group = PartnerORM(
                name=data.name,
                email=data.email,
                address=data.address,
                kind=group_kind_id,
                company_id=1,
                is_registrant=True,
                is_group=True,
                registration_date=date.today(),
            )
            session.add(new_group)
            await session.flush()

            if data.reg_ids:
                await self._add_registration_ids(session, new_group.id, data.reg_ids)
            if data.phone_numbers:
                await self.add_phone_numbers(session, new_group.id, data.phone_numbers)

            await session.refresh(new_group)

            # Add current member to this group
            individual_record = await IndividualService().get_individual(individual_id)

            await DirectGroupMembershipHandler(
                GroupMembershipService()
            )._create_group_membership(
                session, new_group.id, individual_record.id, data.membership_kind
            )
            await session.commit()

            return await self.get_group_by_group_id(session, new_group.id)

        except Exception as e:
            _logger.error(
                f"Failed to create group for individual {individual_id}: {e}",
                exc_info=True,
            )
            await session.rollback()
            raise InternalServerError(message=f"Could not create a group: {e}") from e

    async def update_group(self, session, group_id: int, data: UpdateGroup) -> GetGroup:
        try:
            group = await session.get(PartnerORM, group_id)

            if not group or not group.is_group:
                return JSONResponse(
                    status_code=404,
                    content={
                        "status": "error",
                        "error_code": 404,
                        "message": "Group not found.",
                    },
                )

            # Update group kind if provided
            group_kind_id = None
            if data.kind:
                group_kind_id = await G2PGroupKindORM.get_group_kind_id_by_name(
                    data.kind.value
                )

            # Update group basic fields
            group.name = data.name or group.name
            group.email = data.email or group.email
            group.address = data.address or group.address
            group.kind = group_kind_id or group.kind
            group.registration_date = group.registration_date or date.today()

            await session.flush()

            # update or insert reg_ids
            if data.reg_ids:
                # Get existing reg_ids for the group
                existing_reg_ids_result = await session.execute(
                    select(RegIDORM).where(RegIDORM.partner_id == group_id)
                )
                existing_reg_ids = {
                    reg.id_type: reg for reg in existing_reg_ids_result.scalars().all()
                }

                to_add = []

                for new_reg in data.reg_ids:
                    reg_type = await RegIDTypeORM.get_id_type_by_name(new_reg.id_type)
                    if not reg_type:
                        raise ValueError(f"Invalid ID type: {new_reg.id_type}")
                    reg_type_id = reg_type.id

                    if reg_type_id in existing_reg_ids:
                        reg_obj = existing_reg_ids[reg_type_id]
                        reg_obj.value = new_reg.value
                        reg_obj.status = new_reg.status
                        reg_obj.expiry_date = new_reg.expiry_date
                    else:
                        to_add.append(new_reg)

                if to_add:
                    await self._add_registration_ids(session, group_id, to_add)

            if data.phone_numbers is not None:
                # Remove existing phone numbers
                await session.execute(
                    delete(PartnerPhoneNoORM).where(
                        PartnerPhoneNoORM.partner_id == group_id
                    )
                )

                await self.add_phone_numbers(session, group_id, data.phone_numbers)

            # TODO Handel member and membership update here
            await session.commit()
            await session.refresh(group)

            return await self.get_group_by_group_id(session, group_id)

        except Exception as e:
            _logger.error(f"Failed to update group {group_id}: {e}", exc_info=True)
            await session.rollback()
            raise InternalServerError(
                message=f"Could not update group {group_id}: {e}"
            ) from e

    async def _add_registration_ids(self, session, partner_id: int, reg_ids: List):
        for reg_id in reg_ids:
            reg_type = await RegIDTypeORM.get_id_type_by_name(reg_id.id_type)
            if not reg_type:
                raise ValueError(f"Invalid ID type: {reg_id.id}")

            session.add(
                RegIDORM(
                    partner_id=partner_id,
                    id_type=reg_type.id,  # Use the integer ID
                    value=reg_id.value,
                    status=reg_id.status,
                    expiry_date=reg_id.expiry_date,
                )
            )

    async def add_phone_numbers(self, session, partner_id: int, phone_numbers: List):
        for phone in phone_numbers:
            session.add(
                PartnerPhoneNoORM(
                    partner_id=partner_id,
                    phone_no=phone.phone_no,
                    date_collected=phone.date_collected,
                )
            )
        await session.flush()

    async def get_group_by_group_id(
        self,
        session: AsyncSession,
        group_id: int,
    ) -> GetGroup:
        group = await session.get(PartnerORM, group_id)

        if not group or not group.is_group:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "error_code": 404,
                    "message": "Group not found.",
                },
            )

        # Get group kind name
        group_kind_name = None
        if group.kind:
            group_kind = await session.get(G2PGroupKindORM, group.kind)
            group_kind_name = group_kind.name if group_kind else None

        # Get reg_ids
        reg_id_result = await session.execute(
            select(RegIDORM).where(RegIDORM.partner_id == group_id)
        )

        reg_ids = []
        for reg in reg_id_result.scalars():
            reg_type = await session.get(RegIDTypeORM, reg.id_type)
            reg_ids.append(
                {
                    "id_type": reg_type.name,
                    "value": reg.value,
                    "status": reg.status,
                    "expiry_date": reg.expiry_date,
                }
            )

        # Get phone numbers
        phone_result = await session.execute(
            select(PartnerPhoneNoORM).where(PartnerPhoneNoORM.partner_id == group_id)
        )
        phone_numbers = [
            {
                "phone_no": phone.phone_no,
                "date_collected": phone.date_collected,
            }
            for phone in phone_result.scalars()
        ]
        membership_kind_enums = await self.get_membership_kinds_for_group(
            session, group_id
        )
        # Return a valid GetGroup object
        return GetGroup(
            id=group.id,
            name=group.name,
            is_group=group.is_group,
            kind=group_kind_name,
            reg_ids=reg_ids,
            email=group.email,
            address=group.address,
            phone_numbers=phone_numbers,
            membership_kind=membership_kind_enums,
        )

    async def get_membership_kinds_for_group(
        self, session: AsyncSession, group_id: int
    ) -> List[GroupMembershipKind]:
        membership_result = await session.execute(
            select(G2PGroupMembershipORM).where(G2PGroupMembershipORM.group == group_id)
        )
        memberships = membership_result.scalars().all()

        membership_kind_names = set()

        for membership in memberships:
            await session.refresh(membership, ["group_membership_kind"])
            if membership.group_membership_kind:
                for kind in membership.group_membership_kind:
                    kind_record = await session.get(G2PGroupMembershipKindORM, kind.id)
                    if kind_record:
                        membership_kind_names.add(kind_record.name)

        # Convert to Enum safely
        membership_kind_enums = [
            GroupMembershipKind(kind)
            for kind in membership_kind_names
            if kind in GroupMembershipKind._value2member_map_
        ]

        return membership_kind_enums
