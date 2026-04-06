from tortoise import fields
from tortoise.models import Model
from datetime import datetime
import uuid


class GroupChat(Model):
    id = fields.IntField(pk=True)
    
    # Unique identifier for the group
    group_id = fields.CharField(
        max_length=100, 
        unique=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Group metadata
    name = fields.CharField(max_length=255, index=True)
    description = fields.TextField(null=True)
    
    # Group settings
    is_public = fields.BooleanField(default=True)  # Anyone can discover and join
    max_members = fields.IntField(default=5000)
    allow_new_members_to_see_history = fields.BooleanField(default=True)
    
    # Creator info
    creator_id = fields.CharField(max_length=100, index=True)
    creator_name = fields.CharField(max_length=255, null=True)
    
    # Icon/Avatar
    icon_url = fields.CharField(max_length=500, null=True)
    
    # Status
    is_active = fields.BooleanField(default=True, index=True)
    is_archived = fields.BooleanField(default=False)
    
    # Statistics
    member_count = fields.IntField(default=0)
    message_count = fields.IntField(default=0)
    last_message_at = fields.DatetimeField(null=True)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    archived_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "group_chats"
        indexes = [
            ["creator_id"],
            ["is_public", "is_active"],
            ["created_at"],
        ]
    
    def __str__(self):
        return f"{self.name} (Members: {self.member_count})"


class GroupMember(Model):
    """
    Represents membership in a group.
    Tracks who is in the group and their role/permissions.
    """
    id = fields.IntField(pk=True)
    
    # Foreign key to group
    group = fields.ForeignKeyField(
        "models.GroupChat", 
        related_name="members",
        on_delete="CASCADE"
    )
    
    # User info
    user_id = fields.CharField(max_length=100, index=True)
    user_name = fields.CharField(max_length=255)
    user_avatar = fields.CharField(max_length=500, null=True)
    
    # Role and permissions
    role = fields.CharField(
        max_length=20,
        default="member",  # "admin", "moderator", "member"
        index=True
    )
    
    # Permission flags
    can_send_messages = fields.BooleanField(default=True)
    can_delete_own_messages = fields.BooleanField(default=True)
    can_delete_others_messages = fields.BooleanField(default=False)
    can_pin_messages = fields.BooleanField(default=False)
    can_invite_members = fields.BooleanField(default=False)
    can_change_group_settings = fields.BooleanField(default=False)
    can_remove_members = fields.BooleanField(default=False)
    
    # Status
    is_active = fields.BooleanField(default=True, index=True)
    is_muted = fields.BooleanField(default=False)
    is_blocked = fields.BooleanField(default=False)
    
    # Read status
    last_read_message_id = fields.CharField(max_length=100, null=True)
    last_read_at = fields.DatetimeField(null=True)
    unread_count = fields.IntField(default=0)
    
    # Timestamps
    joined_at = fields.DatetimeField(auto_now_add=True, index=True)
    left_at = fields.DatetimeField(null=True)
    
    class Meta:
        table = "group_members"
        unique_together = [["group", "user_id"]]
        indexes = [
            ["group", "is_active"],
            ["user_id"],
            ["role"],
        ]
    
    # def __str__(self):
    #     return f"{self.user_name} ({self.role}) in {self.group.name}"
    def __str__(self):
    # safest: only use ids/primitive fields
        return f"{self.user_name} ({self.role}) in group {getattr(self, 'group_id', '?')}"


class GroupMessage(Model):
    """
    Represents a single message in a group chat.
    Supports text, media, reactions, and more.
    """
    id = fields.IntField(pk=True)
    
    # Message identity
    message_id = fields.CharField(
        max_length=100, 
        unique=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key to group
    group = fields.ForeignKeyField(
        "models.GroupChat", 
        related_name="messages",
        on_delete="CASCADE"
    )
    
    # Sender info
    sender_id = fields.CharField(max_length=100, index=True)
    sender_name = fields.CharField(max_length=255)
    sender_avatar = fields.CharField(max_length=500, null=True)
    
    # Message content
    text = fields.TextField()
    
    # Rich content support
    content_type = fields.CharField(
        max_length=20,
        default="text",  # "text", "image", "video", "audio", "file"
        index=True
    )
    media_url = fields.CharField(max_length=500, null=True)
    media_metadata = fields.JSONField(default={})
    
    # Message reactions (emoji)
    reactions = fields.JSONField(default={})
    
    # Editing and deletion
    edited_count = fields.IntField(default=0)
    edited_at = fields.DatetimeField(null=True)
    is_deleted = fields.BooleanField(default=False, index=True)
    deleted_at = fields.DatetimeField(null=True)
    deleted_by_id = fields.CharField(max_length=100, null=True)
    
    # Pinning
    is_pinned = fields.BooleanField(default=False, index=True)
    pinned_at = fields.DatetimeField(null=True)
    pinned_by_id = fields.CharField(max_length=100, null=True)
    
    # Reply to another message
    replied_to_message_id = fields.CharField(max_length=100, null=True)
    reply_count = fields.IntField(default=0)
    
    # Read receipts
    read_by_count = fields.IntField(default=0)
    read_by_userids = fields.JSONField(default={})
    
    # Metadata
    is_important = fields.BooleanField(default=False)
    tags = fields.JSONField(default=[])
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "group_messages"
        indexes = [
            ["group", "created_at"],
            ["sender_id"],
            ["is_deleted"],
            ["is_pinned"],
        ]
    
    def __str__(self):
        preview = self.text[:50] if self.text else "[Media]"
        return f"{self.sender_name}: {preview}"


class GroupInvitation(Model):
    """
    Represents an invitation to join a group.
    Used for access control on private groups.
    """
    id = fields.IntField(pk=True)
    
    # Invitation identity
    invitation_id = fields.CharField(
        max_length=100, 
        unique=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key to group
    group = fields.ForeignKeyField(
        "models.GroupChat", 
        related_name="invitations",
        on_delete="CASCADE"
    )
    
    # Invitee info
    invitee_id = fields.CharField(max_length=100, index=True)
    invitee_name = fields.CharField(max_length=255, null=True)
    invitee_email = fields.CharField(max_length=255, null=True)
    
    # Inviter info
    inviter_id = fields.CharField(max_length=100)
    inviter_name = fields.CharField(max_length=255, null=True)
    
    # Status
    status = fields.CharField(
        max_length=20,
        default="pending",  # "pending", "accepted", "declined", "revoked"
        index=True
    )
    
    # Custom message
    invitation_message = fields.TextField(null=True)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    responded_at = fields.DatetimeField(null=True)
    expires_at = fields.DatetimeField(index=True)
    
    class Meta:
        table = "group_invitations"
        indexes = [
            ["group", "status"],
            ["invitee_id"],
            ["status"],
        ]
    
    def __str__(self):
        return f"Invite {self.invitee_name} to {self.group.name} ({self.status})"


class GroupActivity(Model):
    """
    Audit log for group activities.
    Tracks who did what and when in the group.
    """
    id = fields.IntField(pk=True)
    
    # Activity identity
    activity_id = fields.CharField(
        max_length=100, 
        unique=True, 
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key to group
    group = fields.ForeignKeyField(
        "models.GroupChat", 
        related_name="activities",
        on_delete="CASCADE"
    )
    
    # Actor info
    actor_id = fields.CharField(max_length=100, index=True)
    actor_name = fields.CharField(max_length=255, null=True)
    
    # Action
    action = fields.CharField(
        max_length=50,
        index=True  # "member_joined", "member_left", "member_removed", etc
    )
    action_details = fields.JSONField(default={})
    
    # Target (if applicable)
    target_user_id = fields.CharField(max_length=100, null=True)
    target_message_id = fields.CharField(max_length=100, null=True)
    
    # Timestamps
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    
    class Meta:
        table = "group_activities"
        indexes = [
            ["group", "created_at"],
            ["action"],
        ]
    
    def __str__(self):
        return f"{self.action} by {self.actor_name}"