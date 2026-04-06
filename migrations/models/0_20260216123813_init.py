from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `messagetemplate` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `channel` VARCHAR(50) NOT NULL,
    `name` VARCHAR(255) NOT NULL,
    `content` LONGTEXT NOT NULL,
    `is_approved` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `synclog` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `source` VARCHAR(50) NOT NULL,
    `status` VARCHAR(50) NOT NULL,
    `total_records` INT NOT NULL,
    `error_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `privacy` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `details` LONGTEXT NOT NULL,
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `terms` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `details` LONGTEXT NOT NULL,
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `platform_settings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `support_email` VARCHAR(255) NOT NULL,
    `admin_email` VARCHAR(255) NOT NULL,
    `allow_user_registration` BOOL NOT NULL DEFAULT 1,
    `allow_organization_registration` BOOL NOT NULL DEFAULT 1
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `from_type` VARCHAR(20) NOT NULL,
    `from_id` VARCHAR(100) NOT NULL,
    `from_name` VARCHAR(255),
    `to_type` VARCHAR(20) NOT NULL,
    `to_id` VARCHAR(100) NOT NULL,
    `text` LONGTEXT NOT NULL,
    `message_id` VARCHAR(100) NOT NULL UNIQUE,
    `is_read` BOOL NOT NULL DEFAULT 0,
    `is_delivered` BOOL NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    KEY `idx_chat_messag_from_ty_a15a11` (`from_type`, `from_id`, `to_type`, `to_id`, `created_at`),
    KEY `idx_chat_messag_to_type_feb35b` (`to_type`, `to_id`, `is_read`)
) CHARACTER SET utf8mb4 COMMENT='Store all chat messages persistently';
CREATE TABLE IF NOT EXISTS `chat_sessions` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user1_type` VARCHAR(20) NOT NULL,
    `user1_id` VARCHAR(100) NOT NULL,
    `user2_type` VARCHAR(20) NOT NULL,
    `user2_id` VARCHAR(100) NOT NULL,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `last_message_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `ended_at` DATETIME(6),
    UNIQUE KEY `uid_chat_sessio_user1_t_3052cf` (`user1_type`, `user1_id`, `user2_type`, `user2_id`),
    KEY `idx_chat_sessio_user1_t_cec0a1` (`user1_type`, `user1_id`, `is_active`),
    KEY `idx_chat_sessio_user2_t_d3945e` (`user2_type`, `user2_id`, `is_active`)
) CHARACTER SET utf8mb4 COMMENT='Track active chat sessions between users';
CREATE TABLE IF NOT EXISTS `offline_notifications` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `to_type` VARCHAR(20) NOT NULL,
    `to_id` VARCHAR(100) NOT NULL,
    `notification_id` VARCHAR(100) NOT NULL UNIQUE,
    `title` VARCHAR(255) NOT NULL,
    `body` LONGTEXT NOT NULL,
    `data` JSON NOT NULL,
    `urgency` VARCHAR(20) NOT NULL DEFAULT 'normal',
    `is_delivered` BOOL NOT NULL DEFAULT 0,
    `delivered_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `expires_at` DATETIME(6) NOT NULL,
    KEY `idx_offline_not_to_type_43dfcf` (`to_type`, `to_id`, `is_delivered`),
    KEY `idx_offline_not_expires_cee831` (`expires_at`)
) CHARACTER SET utf8mb4 COMMENT='Store notifications for offline users';
CREATE TABLE IF NOT EXISTS `group_chats` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `group_id` VARCHAR(100) NOT NULL UNIQUE,
    `name` VARCHAR(255) NOT NULL,
    `description` LONGTEXT,
    `is_public` BOOL NOT NULL DEFAULT 1,
    `max_members` INT NOT NULL DEFAULT 5000,
    `allow_new_members_to_see_history` BOOL NOT NULL DEFAULT 1,
    `creator_id` VARCHAR(100) NOT NULL,
    `creator_name` VARCHAR(255),
    `icon_url` VARCHAR(500),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `is_archived` BOOL NOT NULL DEFAULT 0,
    `member_count` INT NOT NULL DEFAULT 0,
    `message_count` INT NOT NULL DEFAULT 0,
    `last_message_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `archived_at` DATETIME(6),
    KEY `idx_group_chats_group_i_ff00aa` (`group_id`),
    KEY `idx_group_chats_name_c11bc9` (`name`),
    KEY `idx_group_chats_creator_3310c7` (`creator_id`),
    KEY `idx_group_chats_is_acti_fdc80a` (`is_active`),
    KEY `idx_group_chats_created_4dad88` (`created_at`),
    KEY `idx_group_chats_is_publ_7812a6` (`is_public`, `is_active`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `group_activities` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `activity_id` VARCHAR(100) NOT NULL UNIQUE,
    `actor_id` VARCHAR(100) NOT NULL,
    `actor_name` VARCHAR(255),
    `action` VARCHAR(50) NOT NULL,
    `action_details` JSON NOT NULL,
    `target_user_id` VARCHAR(100),
    `target_message_id` VARCHAR(100),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `group_id` INT NOT NULL,
    CONSTRAINT `fk_group_ac_group_ch_23b244a7` FOREIGN KEY (`group_id`) REFERENCES `group_chats` (`id`) ON DELETE CASCADE,
    KEY `idx_group_activ_activit_800058` (`activity_id`),
    KEY `idx_group_activ_actor_i_4967e1` (`actor_id`),
    KEY `idx_group_activ_action_e2925d` (`action`),
    KEY `idx_group_activ_created_a3e2ee` (`created_at`),
    KEY `idx_group_activ_group_i_629184` (`group_id`, `created_at`)
) CHARACTER SET utf8mb4 COMMENT='Audit log for group activities.';
CREATE TABLE IF NOT EXISTS `group_invitations` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `invitation_id` VARCHAR(100) NOT NULL UNIQUE,
    `invitee_id` VARCHAR(100) NOT NULL,
    `invitee_name` VARCHAR(255),
    `invitee_email` VARCHAR(255),
    `inviter_id` VARCHAR(100) NOT NULL,
    `inviter_name` VARCHAR(255),
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending',
    `invitation_message` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `responded_at` DATETIME(6),
    `expires_at` DATETIME(6) NOT NULL,
    `group_id` INT NOT NULL,
    CONSTRAINT `fk_group_in_group_ch_9581956d` FOREIGN KEY (`group_id`) REFERENCES `group_chats` (`id`) ON DELETE CASCADE,
    KEY `idx_group_invit_invitat_b56a47` (`invitation_id`),
    KEY `idx_group_invit_invitee_2c10b6` (`invitee_id`),
    KEY `idx_group_invit_status_3cd2df` (`status`),
    KEY `idx_group_invit_created_ef3d57` (`created_at`),
    KEY `idx_group_invit_expires_4490ca` (`expires_at`),
    KEY `idx_group_invit_group_i_921a54` (`group_id`, `status`)
) CHARACTER SET utf8mb4 COMMENT='Represents an invitation to join a group.';
CREATE TABLE IF NOT EXISTS `group_members` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `user_id` VARCHAR(100) NOT NULL,
    `user_name` VARCHAR(255) NOT NULL,
    `user_avatar` VARCHAR(500),
    `role` VARCHAR(20) NOT NULL DEFAULT 'member',
    `can_send_messages` BOOL NOT NULL DEFAULT 1,
    `can_delete_own_messages` BOOL NOT NULL DEFAULT 1,
    `can_delete_others_messages` BOOL NOT NULL DEFAULT 0,
    `can_pin_messages` BOOL NOT NULL DEFAULT 0,
    `can_invite_members` BOOL NOT NULL DEFAULT 0,
    `can_change_group_settings` BOOL NOT NULL DEFAULT 0,
    `can_remove_members` BOOL NOT NULL DEFAULT 0,
    `is_active` BOOL NOT NULL DEFAULT 1,
    `is_muted` BOOL NOT NULL DEFAULT 0,
    `is_blocked` BOOL NOT NULL DEFAULT 0,
    `last_read_message_id` VARCHAR(100),
    `last_read_at` DATETIME(6),
    `unread_count` INT NOT NULL DEFAULT 0,
    `joined_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `left_at` DATETIME(6),
    `group_id` INT NOT NULL,
    UNIQUE KEY `uid_group_membe_group_i_871198` (`group_id`, `user_id`),
    CONSTRAINT `fk_group_me_group_ch_c92aa589` FOREIGN KEY (`group_id`) REFERENCES `group_chats` (`id`) ON DELETE CASCADE,
    KEY `idx_group_membe_user_id_1ed761` (`user_id`),
    KEY `idx_group_membe_role_ead010` (`role`),
    KEY `idx_group_membe_is_acti_821a29` (`is_active`),
    KEY `idx_group_membe_joined__9749ef` (`joined_at`),
    KEY `idx_group_membe_group_i_46d185` (`group_id`, `is_active`)
) CHARACTER SET utf8mb4 COMMENT='Represents membership in a group.';
CREATE TABLE IF NOT EXISTS `group_messages` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `message_id` VARCHAR(100) NOT NULL UNIQUE,
    `sender_id` VARCHAR(100) NOT NULL,
    `sender_name` VARCHAR(255) NOT NULL,
    `sender_avatar` VARCHAR(500),
    `text` LONGTEXT NOT NULL,
    `content_type` VARCHAR(20) NOT NULL DEFAULT 'text',
    `media_url` VARCHAR(500),
    `media_metadata` JSON NOT NULL,
    `reactions` JSON NOT NULL,
    `edited_count` INT NOT NULL DEFAULT 0,
    `edited_at` DATETIME(6),
    `is_deleted` BOOL NOT NULL DEFAULT 0,
    `deleted_at` DATETIME(6),
    `deleted_by_id` VARCHAR(100),
    `is_pinned` BOOL NOT NULL DEFAULT 0,
    `pinned_at` DATETIME(6),
    `pinned_by_id` VARCHAR(100),
    `replied_to_message_id` VARCHAR(100),
    `reply_count` INT NOT NULL DEFAULT 0,
    `read_by_count` INT NOT NULL DEFAULT 0,
    `read_by_userids` JSON NOT NULL,
    `is_important` BOOL NOT NULL DEFAULT 0,
    `tags` JSON NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `group_id` INT NOT NULL,
    CONSTRAINT `fk_group_me_group_ch_69abfb08` FOREIGN KEY (`group_id`) REFERENCES `group_chats` (`id`) ON DELETE CASCADE,
    KEY `idx_group_messa_message_c66def` (`message_id`),
    KEY `idx_group_messa_sender__b8e786` (`sender_id`),
    KEY `idx_group_messa_content_08da0b` (`content_type`),
    KEY `idx_group_messa_is_dele_537cca` (`is_deleted`),
    KEY `idx_group_messa_is_pinn_479227` (`is_pinned`),
    KEY `idx_group_messa_created_a3346a` (`created_at`),
    KEY `idx_group_messa_group_i_352543` (`group_id`, `created_at`)
) CHARACTER SET utf8mb4 COMMENT='Represents a single message in a group chat.';
CREATE TABLE IF NOT EXISTS `group` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL UNIQUE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `permission` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `codename` VARCHAR(100) NOT NULL UNIQUE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `users` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `name` VARCHAR(50),
    `email` VARCHAR(100) UNIQUE,
    `password` VARCHAR(128) NOT NULL,
    `photo` VARCHAR(255),
    `phone` VARCHAR(255),
    `address` VARCHAR(255),
    `dob` DATE,
    `role` VARCHAR(12) NOT NULL COMMENT 'USER: USER\nORGANIZATION: organization\nADMIN: ADMIN' DEFAULT 'USER',
    `is_active` BOOL NOT NULL DEFAULT 1,
    `is_staff` BOOL NOT NULL DEFAULT 0,
    `is_superadmin` BOOL NOT NULL DEFAULT 0,
    `last_login_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `organization_id` CHAR(36),
    CONSTRAINT `fk_users_users_ad99a602` FOREIGN KEY (`organization_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `communication` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `channel` VARCHAR(50) NOT NULL,
    `status` VARCHAR(50) NOT NULL,
    `provider_response` JSON,
    `sent_at` DATETIME(6),
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `template_id` INT,
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_communic_messaget_88bf3fe0` FOREIGN KEY (`template_id`) REFERENCES `messagetemplate` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_communic_users_6f7ce90c` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `auditlog` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `action` VARCHAR(255) NOT NULL,
    `entity` VARCHAR(255) NOT NULL,
    `entity_id` INT NOT NULL,
    `ip_address` VARCHAR(50) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` CHAR(36),
    CONSTRAINT `fk_auditlog_users_5b017bf0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_settings` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `email_notifications` BOOL NOT NULL DEFAULT 0,
    `push_notifications` BOOL NOT NULL DEFAULT 0,
    `promotional_notifications` BOOL NOT NULL DEFAULT 0,
    `parental_notifications` BOOL NOT NULL DEFAULT 0,
    `user_activity_alerts` BOOL NOT NULL DEFAULT 0,
    `language` VARCHAR(255) NOT NULL DEFAULT 'ENGLISH',
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_user_set_users_9237a864` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `devicetoken` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `token` VARCHAR(256) NOT NULL,
    `platform` VARCHAR(32) NOT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_deviceto_users_1a8b733b` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `notifications` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `title` VARCHAR(255),
    `body` LONGTEXT,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `is_read` BOOL NOT NULL DEFAULT 0,
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_notifica_users_ca29871f` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `plans` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL UNIQUE,
    `description` LONGTEXT,
    `duration_days` INT NOT NULL DEFAULT 30,
    `basic_dispute_generation` BOOL NOT NULL DEFAULT 0,
    `unlimited_disputes` BOOL NOT NULL DEFAULT 0,
    `disputes_per_month` INT,
    `email_support` BOOL NOT NULL DEFAULT 0,
    `priority_email_support` BOOL NOT NULL DEFAULT 0,
    `phone_support_24_7` BOOL NOT NULL DEFAULT 0,
    `dedicated_account_manager` BOOL NOT NULL DEFAULT 0,
    `access_basic_modules` BOOL NOT NULL DEFAULT 0,
    `access_all_modules` BOOL NOT NULL DEFAULT 0,
    `ai_task_recommendations` BOOL NOT NULL DEFAULT 0,
    `advanced_analytics` BOOL NOT NULL DEFAULT 0,
    `regular_task_alerts` BOOL NOT NULL DEFAULT 0,
    `ai_token` INT,
    `price` DOUBLE DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_plans` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `basic_dispute_generation` BOOL NOT NULL DEFAULT 0,
    `unlimited_disputes` BOOL NOT NULL DEFAULT 0,
    `disputes_per_month` INT,
    `email_support` BOOL NOT NULL DEFAULT 0,
    `priority_email_support` BOOL NOT NULL DEFAULT 0,
    `phone_support_24_7` BOOL NOT NULL DEFAULT 0,
    `dedicated_account_manager` BOOL NOT NULL DEFAULT 0,
    `access_basic_modules` BOOL NOT NULL DEFAULT 0,
    `access_all_modules` BOOL NOT NULL DEFAULT 0,
    `ai_task_recommendations` BOOL NOT NULL DEFAULT 0,
    `advanced_analytics` BOOL NOT NULL DEFAULT 0,
    `regular_task_alerts` BOOL NOT NULL DEFAULT 0,
    `ai_token` INT,
    `price` DOUBLE DEFAULT 0,
    `duration_days` INT NOT NULL DEFAULT 30,
    `paused_at` DATETIME(6),
    `started_at` DATETIME(6),
    `status` VARCHAR(9) NOT NULL COMMENT 'ACTIVE: ACTIVE\nPAUSED: PAUSED\nCANCELLED: CANCELLED' DEFAULT 'ACTIVE',
    `auto_renewal` BOOL NOT NULL DEFAULT 1,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `plan_id` CHAR(36),
    CONSTRAINT `fk_user_pla_plans_b28a7e01` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`) ON DELETE SET NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `group_permissions` (
    `group_id` INT NOT NULL,
    `permission_id` INT NOT NULL,
    FOREIGN KEY (`group_id`) REFERENCES `group` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_group_permi_group_i_c7a36c` (`group_id`, `permission_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_groups` (
    `users_id` CHAR(36) NOT NULL,
    `group_id` INT NOT NULL,
    FOREIGN KEY (`users_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`group_id`) REFERENCES `group` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_user_groups_users_i_7ef143` (`users_id`, `group_id`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user_permissions` (
    `users_id` CHAR(36) NOT NULL,
    `permission_id` INT NOT NULL,
    FOREIGN KEY (`users_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_user_permis_users_i_035bf3` (`users_id`, `permission_id`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
