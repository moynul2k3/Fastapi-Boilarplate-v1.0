from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `plans` ADD `stripe_product_id` VARCHAR(255);
        ALTER TABLE `plans` ADD `stripe_price_id` VARCHAR(255);
        ALTER TABLE `plans` MODIFY COLUMN `price` DECIMAL(10,2) DEFAULT 0;
        ALTER TABLE `plans` MODIFY COLUMN `price` DECIMAL(10,2) DEFAULT 0;
        ALTER TABLE `user_plans` ADD `stripe_price_id` VARCHAR(255);
        ALTER TABLE `user_plans` ADD `stripe_subscription_id` VARCHAR(255);
        ALTER TABLE `user_plans` ADD `current_period_end` DATETIME(6);
        ALTER TABLE `user_plans` ADD `user_id` CHAR(36) NOT NULL UNIQUE;
        ALTER TABLE `user_plans` ADD `stripe_customer_id` VARCHAR(255);
        ALTER TABLE `user_plans` ADD `cancel_at_period_end` BOOL NOT NULL DEFAULT 0;
        ALTER TABLE `user_plans` MODIFY COLUMN `price` DECIMAL(10,2) DEFAULT 0;
        ALTER TABLE `user_plans` MODIFY COLUMN `price` DECIMAL(10,2) DEFAULT 0;
        ALTER TABLE `user_plans` ADD CONSTRAINT `fk_user_pla_users_a900d7b8` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `user_plans` DROP FOREIGN KEY `fk_user_pla_users_a900d7b8`;
        ALTER TABLE `plans` DROP COLUMN `stripe_product_id`;
        ALTER TABLE `plans` DROP COLUMN `stripe_price_id`;
        ALTER TABLE `plans` MODIFY COLUMN `price` DOUBLE DEFAULT 0;
        ALTER TABLE `user_plans` DROP COLUMN `stripe_price_id`;
        ALTER TABLE `user_plans` DROP COLUMN `stripe_subscription_id`;
        ALTER TABLE `user_plans` DROP COLUMN `current_period_end`;
        ALTER TABLE `user_plans` DROP COLUMN `user_id`;
        ALTER TABLE `user_plans` DROP COLUMN `stripe_customer_id`;
        ALTER TABLE `user_plans` DROP COLUMN `cancel_at_period_end`;
        ALTER TABLE `user_plans` MODIFY COLUMN `price` DOUBLE DEFAULT 0;"""
