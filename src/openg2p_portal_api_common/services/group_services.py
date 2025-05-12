from typing import List, Optional

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.service import BaseService
from ..models.orm.reg_id_orm import RegIDORM, RegIDTypeORM
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..models.group import GroupDetails, GroupMember, GroupRegId
from ..models.orm.partner_orm import PartnerORM
from ..models.orm.g2p_group_kind_orm import G2PGroupKindORM
from ..models.orm.g2p_group_membership_orm import G2PGroupMembershipORM
from ..models.orm.g2p_group_membership_kind_orm import G2PGroupMembershipKindORM


class GroupService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.async_session_maker = async_sessionmaker(dbengine.get())

    async def create_group(self, group_details: GroupDetails) -> GroupDetails:
        async with self.async_session_maker() as session:
            new_group = PartnerORM(
                name=group_details.name,
                email=group_details.email,
                phone=group_details.phone,
                registration_date=group_details.registration_date,
                address=group_details.address,
                company_id=group_details.company_id,
                kind=group_details.kind,
                is_registrant=group_details.is_registrant,
                is_group=group_details.is_group,
            )
            session.add(new_group)
            await session.flush()

            # Add registration IDs to the group
            if group_details.reg_ids:
                for reg_id in group_details.reg_ids:
                    session.add(
                        RegIDORM(
                            partner_id=new_group.id,
                            id_type=reg_id.id_type,
                            value=reg_id.value,
                            expiry_date=reg_id.expiry_date,
                        )
                    )
            await session.commit()
            await session.refresh(new_group)

        return await self.get_group_by_id(new_group.id)

    async def update_group(
        self, update_details: GroupDetails, group_id: int
    ) -> Optional[GroupDetails]:
        async with self.async_session_maker() as session:
            group = await session.get(PartnerORM, group_id)
            if not group:
                raise ValueError(f"Group with ID {group_id} not found.")

            # Update group fields
            for field in [
                "name",
                "email",
                "phone",
                "kind",
                "registration_date",
                "address",
                "is_group",
            ]:
                setattr(group, field, getattr(update_details, field))

            # Remove and update registration IDs
            await session.execute(
                delete(RegIDORM).where(RegIDORM.partner_id == group_id)
            )
            if update_details.reg_ids:
                session.add_all(
                    [
                        RegIDORM(
                            partner_id=group.id,
                            id_type=reg_id.id_type,
                            value=reg_id.value,
                            expiry_date=reg_id.expiry_date,
                        )
                        for reg_id in update_details.reg_ids
                    ]
                )

            await session.commit()
            await session.refresh(group)

            return await self.get_group_by_id(group.id)

    async def get_group_by_id(self, group_id: int) -> Optional[GroupDetails]:
        async with self.async_session_maker() as session:
            group = await session.get(PartnerORM, group_id)
            if not group:
                return None

            reg_ids = await self.get_group_reg_ids(group_id, session)
            group_kind = await G2PGroupKindORM.get_group_kind_name(group.kind)
            return GroupDetails(
                id=group.id,
                name=group.name,
                email=group.email,
                phone=group.phone,
                registration_date=group.registration_date,
                address=group.address,
                kind=group.kind,
                group_kind=group_kind,
                is_registrant=group.is_registrant,
                is_group=group.is_group,
                reg_ids=reg_ids,
            )

    async def add_member_to_group(
        self, group_id: int, member: GroupMember
    ) -> Optional[GroupMember]:
        async with self.async_session_maker() as session:
            group = await session.get(PartnerORM, group_id)
            if not group:
                return None

            # Check if the member already exists
            existing_members = await self.get_group_members(group_id, session)
            for existing_member in existing_members:
                if existing_member.name == member.name:
                    return None

            # Add the member to the group
            new_member = PartnerORM(
                name=member.name,
                email=member.email,
                phone=member.phone,
                birthdate=member.birthdate,
                gender=member.gender,
                company_id=member.company_id,
                is_registrant=member.is_registrant,
                is_group=member.is_group,
            )
            session.add(new_member)
            await session.flush()

            # Add the member to the group membership
            group_membership = G2PGroupMembershipORM(
                group=group.id,
                individual=new_member.id,
            )
            session.add(group_membership)
            await session.flush()

            # Add membership kinds for this member
            if member.membership_kinds:
                kind_records = await session.execute(
                    select(G2PGroupMembershipKindORM).where(
                        G2PGroupMembershipKindORM.name.in_(member.membership_kinds)
                    )
                )
                kind_objects = kind_records.scalars().all()
                if kind_objects:
                    await session.run_sync(
                        lambda session: (
                            group_membership.group_membership_kind.extend(kind_objects)
                        )
                    )
            await session.commit()
            await session.refresh(new_member)

            return GroupMember(
                id=new_member.id,
                name=new_member.name,
                email=new_member.email,
                phone=new_member.phone,
                birthdate=new_member.birthdate,
                gender=new_member.gender,
                company_id=new_member.company_id,
                is_registrant=new_member.is_registrant,
                is_group=new_member.is_group,
                membership_kinds=await self.get_member_membership_kinds(new_member.id),
            )

    async def get_group_reg_ids(self, group_id: int, session) -> List[GroupRegId]:
        reg_ids = []
        reg_id_records = await session.execute(
            select(RegIDORM).where(RegIDORM.partner_id == group_id)
        )
        reg_id_records = reg_id_records.scalars().all()

        for record in reg_id_records:
            id_type_name = await RegIDTypeORM.get_id_type_name(record.id_type)

            reg_ids.append(
                GroupRegId(
                    id_type=record.id_type,
                    name=id_type_name.name,
                    value=record.value,
                    expiry_date=record.expiry_date,
                )
            )
        return reg_ids

    async def get_group_members(self, group_id: int, session) -> List[GroupMember]:
        group_members = []
        group_membership_records = await session.execute(
            select(G2PGroupMembershipORM).where(G2PGroupMembershipORM.group == group_id)
        )
        group_membership_records = group_membership_records.scalars().all()
        for membership in group_membership_records:
            individual_record = await session.get(PartnerORM, membership.individual)
            if individual_record:
                group_members.append(
                    GroupMember(
                        id=individual_record.id,
                        name=individual_record.name,
                        email=individual_record.email,
                        phone=individual_record.phone,
                        birthdate=individual_record.birthdate.isoformat(),
                        gender=individual_record.gender,
                        company_id=individual_record.company_id,
                        is_registrant=individual_record.is_registrant,
                        is_group=individual_record.is_group,
                    )
                )
        return group_members

    async def get_member_membership_kinds(self, member_id: int) -> list[str]:
        async with self.async_session_maker() as session:
            membership_record = await session.execute(
                select(G2PGroupMembershipORM).where(
                    G2PGroupMembershipORM.individual == member_id
                )
            )
            membership = membership_record.scalars().first()

            membership_kinds = []
            if membership:
                # Ensure group_membership_kind is loaded
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
