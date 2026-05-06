"""Group APIs for lightweight group chat and sharing."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_active_user
from app.core.db import get_db
from app.models.group import Group, GroupMember, GroupMessage
from app.models.user import User
from app.schemas.group import (
    GroupCardShareCreate,
    GroupCreate,
    GroupJoin,
    GroupMemberResponse,
    GroupMessageCreate,
    GroupMessageResponse,
    GroupResponse,
    GroupUpdate,
)
from app.services.groups import (
    active_member_count,
    build_today_status,
    create_group_message,
    generate_invite_code,
    get_active_membership,
    get_group_for_member,
    parse_metadata,
    require_admin_or_owner,
    require_member,
    save_daily_snapshot,
)


router = APIRouter()


def _group_response(group: Group, member: GroupMember, db: DBSession) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        invite_code=group.invite_code,
        visibility=group.visibility,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=active_member_count(group.id, db),
        my_role=member.role,
    )


def _message_response(row) -> GroupMessageResponse:
    message, username = row
    return GroupMessageResponse(
        id=message.id,
        group_id=message.group_id,
        user_id=message.user_id,
        username=username,
        message_type=message.message_type,
        content=message.content,
        metadata_json=parse_metadata(message.metadata_json),
        created_at=message.created_at,
        deleted_at=message.deleted_at,
    )


@router.get("", response_model=list[GroupResponse])
def list_groups(
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    rows = db.query(Group, GroupMember).join(
        GroupMember, GroupMember.group_id == Group.id
    ).filter(
        GroupMember.user_id == current_user.id,
        GroupMember.is_active == True,
    ).order_by(Group.updated_at.desc(), Group.id.desc()).all()
    return [_group_response(group, member, db) for group, member in rows]


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group name is required")

    group = Group(
        name=name,
        description=payload.description.strip() if payload.description else None,
        owner_id=current_user.id,
        invite_code=generate_invite_code(db),
        visibility=payload.visibility,
    )
    db.add(group)
    db.flush()
    member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role="owner",
        is_active=True,
    )
    db.add(member)
    create_group_message(group.id, current_user.id, "system", f"{current_user.username} 创建了小组。", None, db)
    db.commit()
    db.refresh(group)
    db.refresh(member)
    return _group_response(group, member, db)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    group, member = get_group_for_member(group_id, current_user.id, db)
    return _group_response(group, member, db)


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    payload: GroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    member = require_admin_or_owner(group_id, current_user.id, db)
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group name is required")
        group.name = name
    if payload.description is not None:
        group.description = payload.description.strip() or None
    if payload.visibility is not None:
        group.visibility = payload.visibility

    db.commit()
    db.refresh(group)
    return _group_response(group, member, db)


@router.post("/join", response_model=GroupResponse)
def join_group(
    payload: GroupJoin,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    group = db.query(Group).filter(Group.invite_code == payload.invite_code.strip().upper()).first()
    if group is None or group.visibility != "invite_code":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.user_id == current_user.id,
    ).first()
    should_announce = False
    if member is None:
        member = GroupMember(group_id=group.id, user_id=current_user.id, role="member", is_active=True)
        db.add(member)
        should_announce = True
    elif not member.is_active:
        member.is_active = True
        member.role = "member"
        should_announce = True

    if should_announce:
        create_group_message(group.id, current_user.id, "system", f"{current_user.username} 加入了小组。", None, db)
    db.commit()
    db.refresh(member)
    db.refresh(group)
    return _group_response(group, member, db)


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    group, member = get_group_for_member(group_id, current_user.id, db)
    if group.owner_id == current_user.id or member.role == "owner":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner cannot leave group in MVP")

    member.is_active = False
    create_group_message(group.id, current_user.id, "system", f"{current_user.username} 退出了小组。", None, db)
    db.commit()
    return None


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
def list_members(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    require_member(group_id, current_user.id, db)
    rows = db.query(GroupMember, User.username).join(
        User, User.id == GroupMember.user_id
    ).filter(
        GroupMember.group_id == group_id,
        GroupMember.is_active == True,
    ).order_by(
        GroupMember.role.asc(),
        GroupMember.joined_at.asc(),
    ).all()
    return [
        GroupMemberResponse(
            id=member.id,
            group_id=member.group_id,
            user_id=member.user_id,
            username=username,
            role=member.role,
            joined_at=member.joined_at,
            muted_until=member.muted_until,
            is_active=member.is_active,
        )
        for member, username in rows
    ]


@router.get("/{group_id}/messages", response_model=list[GroupMessageResponse])
def list_messages(
    group_id: int,
    before: Optional[int] = Query(None, description="Return messages with id lower than this value"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    require_member(group_id, current_user.id, db)
    query = db.query(GroupMessage, User.username).join(
        User, User.id == GroupMessage.user_id
    ).filter(
        GroupMessage.group_id == group_id,
        GroupMessage.deleted_at.is_(None),
    )
    if before is not None:
        query = query.filter(GroupMessage.id < before)

    rows = query.order_by(GroupMessage.id.desc()).limit(limit).all()
    return [_message_response(row) for row in reversed(rows)]


@router.post("/{group_id}/messages", response_model=GroupMessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    group_id: int,
    payload: GroupMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    require_member(group_id, current_user.id, db)
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content is required")

    message = create_group_message(group_id, current_user.id, "text", content, payload.metadata_json, db)
    db.commit()
    db.refresh(message)
    username = db.query(func.coalesce(User.username, "")).filter(User.id == current_user.id).scalar()
    return _message_response((message, username))


@router.post("/{group_id}/share-status", response_model=GroupMessageResponse, status_code=status.HTTP_201_CREATED)
def share_status(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    require_member(group_id, current_user.id, db)
    content, metadata = build_today_status(current_user.id, db)
    save_daily_snapshot(group_id, current_user.id, metadata, db)
    message = create_group_message(group_id, current_user.id, "status_share", content, metadata, db)
    db.commit()
    db.refresh(message)
    return _message_response((message, current_user.username))


@router.post("/{group_id}/share-card", response_model=GroupMessageResponse, status_code=status.HTTP_201_CREATED)
def share_card(
    group_id: int,
    payload: GroupCardShareCreate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    require_member(group_id, current_user.id, db)
    content = (payload.content or "分享了一张复盘卡片").strip()
    message = create_group_message(group_id, current_user.id, "card_share", content, payload.metadata_json, db)
    db.commit()
    db.refresh(message)
    return _message_response((message, current_user.username))
