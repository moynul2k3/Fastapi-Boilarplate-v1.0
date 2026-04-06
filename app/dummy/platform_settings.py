from tortoise.transactions import in_transaction
from tortoise.exceptions import IntegrityError
from applications.site.settings import PlatformSettings

# SINGLE PLATFORM SETTING
DEFAULT_PLATFORM_SETTING = {
    "support_email": "support@example.com",
    "admin_email": "admin@example.com",
    "allow_user_registration": True,
    "allow_organization_registration": True,
}

# MAIN SEED FUNCTION
async def seed_platform_settings():
    try:
        async with in_transaction():
            obj = await PlatformSettings.all().first()

            if obj:
                await obj.update_from_dict(DEFAULT_PLATFORM_SETTING)
                await obj.save()
                print(f">> Updated existing platform setting - Admin: {obj.admin_email}")
            else:
                obj = await PlatformSettings.create(**DEFAULT_PLATFORM_SETTING)
                print(f">> Created platform setting - Admin: {obj.admin_email}")
            print("\n PLATFORM SETTINGS SEEDING COMPLETED")

    except IntegrityError as e:
        print(">> Integrity error:", e)
    except Exception as e:
        print(">> Unexpected error:", e)
