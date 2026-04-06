
from typing import Dict, Set, Optional, List
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import json
import uuid
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class GroupConnectionManager:
    """
    Production-grade group chat connection manager.
    
    Features:
    - Real-time group messaging for multiple users
    - Connection pooling per group
    - Broadcast to group with delivery tracking
    - Typing indicators
    - Read receipts
    - Message reactions
    - Efficient memory usage with clean-up
    - Heartbeat to keep connections alive
    """
    
    def __init__(self):
        # Group connections: group_id -> {user_key -> connection_dict}
        self.group_connections: Dict[str, Dict[str, dict]] = defaultdict(dict)
        
        # Track which groups a user is connected to
        self.user_group_map: Dict[str, Set[str]] = defaultdict(set)
        
        # Heartbeat tasks per group
        self.group_heartbeats: Dict[str, asyncio.Task] = {}
        
        # Typing indicators
        self.typing_users: Dict[str, Set[str]] = defaultdict(set)
        
        # Online member count per group
        self.group_member_counts: Dict[str, int] = defaultdict(int)
    
    async def connect(
        self,
        websocket: WebSocket,
        group_id: str,
        user_id: str,
        user_name: str = None
    ) -> bool:
        """
        Connect a user to a group chat.
        
        Args:
            websocket: The WebSocket connection
            group_id: Group ID
            user_id: Unique user ID
            user_name: Display name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await websocket.accept()
            user_key = f"user:{user_id}"
            
            # Create connection object
            conn = {
                'websocket': websocket,
                'user_id': user_id,
                'user_name': user_name or str(user_id),
                'connected_at': datetime.utcnow(),
                'is_active': True,
                'message_count': 0,
                'last_message_at': datetime.utcnow()
            }
            
            # Store connection
            self.group_connections[group_id][user_key] = conn
            self.user_group_map[user_key].add(group_id)
            self.group_member_counts[group_id] += 1
            
            logger.info(
                f"✓ User {user_name} ({user_id}) joined group {group_id} "
                f"[Online: {self.group_member_counts[group_id]}]"
            )
            
            # Notify others that user joined
            await self._broadcast_to_group(
                group_id,
                {
                    "type": "member_joined",
                    "user_id": user_id,
                    "user_name": user_name or str(user_id),
                    "online_members": self.group_member_counts[group_id],
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_user=user_key
            )
            
            # Send join confirmation to connecting user
            await self._send_to_connection(conn, {
                "type": "join_confirmed",
                "group_id": group_id,
                "status": "connected",
                "online_members": self.group_member_counts[group_id],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Start heartbeat for group
            await self._ensure_group_heartbeat(group_id)
            return True
            
        except Exception as e:
            logger.error(f"Connection failed for user {user_id}: {str(e)}")
            return False
    
    async def disconnect(self, group_id: str, user_id: str) -> None:
        """Disconnect user from group"""
        try:
            user_key = f"user:{user_id}"
            
            if group_id in self.group_connections:
                if user_key in self.group_connections[group_id]:
                    conn = self.group_connections[group_id][user_key]
                    conn['is_active'] = False
                    user_name = conn.get('user_name', str(user_id))
                    
                    del self.group_connections[group_id][user_key]
                    self.group_member_counts[group_id] = max(
                        0, 
                        self.group_member_counts[group_id] - 1
                    )
                    
                    # Notify others
                    await self._broadcast_to_group(
                        group_id,
                        {
                            "type": "member_left",
                            "user_id": user_id,
                            "user_name": user_name,
                            "online_members": self.group_member_counts[group_id],
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                    
                    logger.info(f"User {user_id} left group {group_id}")
                    
                    # Clean up empty group
                    if not self.group_connections[group_id]:
                        del self.group_connections[group_id]
                        self.group_member_counts[group_id] = 0
                        if group_id in self.group_heartbeats:
                            self.group_heartbeats[group_id].cancel()
                            del self.group_heartbeats[group_id]
                    
                    # Clean up user tracking
                    if user_key in self.user_group_map:
                        self.user_group_map[user_key].discard(group_id)
                        
        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")
    
    async def send_group_message(
        self,
        group_id: str,
        sender_id: str,
        sender_name: str,
        text: str,
        message_id: str = None,
        content_type: str = "text",
        media_url: str = None
    ) -> Dict:
        """
        Send a message to a group.
        Broadcasts to all online members.
        
        Returns:
            Dict with status and delivery info
        """
        try:
            if not message_id:
                message_id = str(uuid.uuid4())
            
            message = {
                "type": "group_message",
                "message_id": message_id,
                "group_id": group_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "text": text,
                "content_type": content_type,
                "media_url": media_url,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to online members
            delivered_to = await self._broadcast_to_group(group_id, message)
            
            logger.info(
                f"Message {message_id} sent in group {group_id} "
                f"to {len(delivered_to)} online members"
            )
            
            return {
                "status": "sent",
                "message_id": message_id,
                "delivered_to": len(delivered_to),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send group message: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "message_id": message_id
            }
    
    async def _broadcast_to_group(
        self,
        group_id: str,
        message: dict,
        exclude_user: str = None
    ) -> List[str]:
        """
        Broadcast message to all online members in group.
        
        Returns:
            List of user keys who received the message
        """
        delivered = []
        
        try:
            if group_id not in self.group_connections:
                return delivered
            
            for user_key, conn in list(self.group_connections[group_id].items()):
                # Skip excluded user if specified
                if exclude_user and user_key == exclude_user:
                    continue
                
                # Send to user
                if await self._send_to_connection(conn, message):
                    delivered.append(user_key)
                else:
                    # Mark as inactive if send fails
                    conn['is_active'] = False
            
            return delivered
            
        except Exception as e:
            logger.error(f"Broadcast error in group {group_id}: {str(e)}")
            return delivered
    
    async def _send_to_connection(self, conn: dict, message: dict) -> bool:
        """Send JSON to a single connection"""
        try:
            if not conn['is_active']:
                return False
            
            await conn['websocket'].send_json(message)
            conn['last_message_at'] = datetime.utcnow()
            conn['message_count'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Send failed: {str(e)}")
            conn['is_active'] = False
            return False
    
    async def mark_typing(
        self,
        group_id: str,
        user_id: str,
        is_typing: bool
    ) -> None:
        """
        Broadcast typing indicator to group members.
        Shows "User is typing..." in real-time.
        """
        try:
            user_key = f"user:{user_id}"
            
            if is_typing:
                self.typing_users[group_id].add(user_key)
            else:
                self.typing_users[group_id].discard(user_key)
            
            # Get typing users in group
            typing_list = []
            if group_id in self.group_connections:
                for tk in self.typing_users[group_id]:
                    if tk in self.group_connections[group_id]:
                        conn = self.group_connections[group_id][tk]
                        typing_list.append({
                            "user_id": conn['user_id'],
                            "user_name": conn['user_name']
                        })
            
            # Broadcast typing status
            await self._broadcast_to_group(
                group_id,
                {
                    "type": "typing_indicator",
                    "group_id": group_id,
                    "typing_users": typing_list,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_user=user_key
            )
            
        except Exception as e:
            logger.error(f"Typing indicator error: {str(e)}")
    
    async def mark_message_read(
        self,
        group_id: str,
        message_id: str,
        user_id: str
    ) -> None:
        """Mark a message as read by a user"""
        try:
            # Broadcast read receipt to group
            await self._broadcast_to_group(
                group_id,
                {
                    "type": "message_read",
                    "message_id": message_id,
                    "read_by_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Mark read error: {str(e)}")
    
    async def pin_message(
        self,
        group_id: str,
        message_id: str,
        user_id: str
    ) -> bool:
        """Pin an important message in the group"""
        try:
            # Broadcast pin notification
            await self._broadcast_to_group(
                group_id,
                {
                    "type": "message_pinned",
                    "message_id": message_id,
                    "pinned_by": user_id,
                    "pinned_at": datetime.utcnow().isoformat()
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Pin message error: {str(e)}")
            return False
    
    async def delete_message(
        self,
        group_id: str,
        message_id: str,
        user_id: str
    ) -> bool:
        """Delete a message from the group"""
        try:
            # Broadcast deletion
            await self._broadcast_to_group(
                group_id,
                {
                    "type": "message_deleted",
                    "message_id": message_id,
                    "deleted_by": user_id,
                    "deleted_at": datetime.utcnow().isoformat()
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Delete message error: {str(e)}")
            return False
    
    async def add_reaction(
        self,
        group_id: str,
        message_id: str,
        user_id: str,
        emoji: str
    ) -> bool:
        """Add emoji reaction to a message"""
        try:
            # Broadcast reaction
            await self._broadcast_to_group(
                group_id,
                {
                    "type": "reaction_added",
                    "message_id": message_id,
                    "emoji": emoji,
                    "added_by": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"Add reaction error: {str(e)}")
            return False
    
    async def get_group_stats(self, group_id: str) -> Dict:
        """Get real-time stats for a group"""
        return {
            "group_id": group_id,
            "online_members": self.group_member_counts.get(group_id, 0),
            "typing_members": len(self.typing_users.get(group_id, set())),
            "connections": len(self.group_connections.get(group_id, {})),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _ensure_group_heartbeat(self, group_id: str) -> None:
        """Ensure heartbeat is running for group"""
        if group_id not in self.group_heartbeats:
            task = asyncio.create_task(self._group_heartbeat(group_id))
            self.group_heartbeats[group_id] = task
    
    async def _group_heartbeat(self, group_id: str) -> None:
        """Periodic heartbeat to keep group connections alive"""
        try:
            while (group_id in self.group_connections and 
                   self.group_connections[group_id]):
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
                # Send ping to all members
                message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self._broadcast_to_group(group_id, message)
                
        except Exception as e:
            logger.error(f"Heartbeat error for group {group_id}: {str(e)}")


# Global instance
group_manager = GroupConnectionManager()