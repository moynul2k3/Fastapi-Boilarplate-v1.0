from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `plans` ADD `is_active` BOOL NOT NULL DEFAULT 1;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `plans` DROP COLUMN `is_active`;"""
