from tortoise.transactions import in_transaction
from tortoise.exceptions import IntegrityError
from applications.user.models import User, UserRole


async def seed_dummy_users():
    try:
        async with in_transaction():

            # ==================================================
            # ADMINS (5)
            # ==================================================
            admins = [
                # Superadmin
                {
                    "email": "superadmin@gmail.com",
                    "name": "Super Admin",
                    "password": "supadmin",
                    "role": UserRole.ADMIN,
                    "is_staff": True,
                    "is_superadmin": True,
                },
                # Staff Admins
                {
                    "email": "staff1@gmail.com",
                    "name": "Staff One",
                    "password": "staff",
                    "role": UserRole.ADMIN,
                    "is_staff": True,
                },
                {
                    "email": "staff2@gmail.com",
                    "name": "Staff Two",
                    "password": "staff",
                    "role": UserRole.ADMIN,
                    "is_staff": True,
                },
                # Normal Admins
                {
                    "email": "admin@gmail.com",
                    "name": "Admin One",
                    "password": "admin",
                    "role": UserRole.ADMIN,
                },
                {
                    "email": "admin1@gmail.com",
                    "name": "Admin Two",
                    "password": "admin",
                    "role": UserRole.ADMIN,
                },
            ]

            for data in admins:
                raw_password = data.pop("password")

                user, created = await User.get_or_create(
                    email=data["email"],
                    defaults={**data, "password": raw_password},
                )

                if not user.password.startswith("$2b$"):
                    user.password = User.set_password(raw_password)
                    await user.save()

                print("👑 Admin created" if created else "⚠️ Admin exists", user.email)

            # ==================================================
            # ORGANIZATIONS (5)
            # ==================================================
            organizations = []

            for i in range(1, 6):
                org, created = await User.get_or_create(
                    email=f"organization{i}@gmail.com",
                    defaults={
                        "name": f"Organization {i}",
                        "password": "org",
                        "role": UserRole.ORGANIZATION,
                    },
                )

                if not org.password.startswith("$2b$"):
                    org.password = User.set_password("org")
                    await org.save()

                organizations.append(org)

                print("🏢 Organization created" if created else "⚠️ Organization exists", org.email)

            # ==================================================
            # USERS WITHOUT ORGANIZATION (5)
            # ==================================================
            for i in range(1, 6):
                user, created = await User.get_or_create(
                    email=f"user_no_org{i}@gmail.com",
                    defaults={
                        "name": f"User No Org {i}",
                        "password": "user",
                        "role": UserRole.USER,
                        "organization": None,
                    },
                )

                if not user.password.startswith("$2b$"):
                    user.password = User.set_password("user")
                    await user.save()

                print("👤 User (no org)" if created else "⚠️ Exists", user.email)

            # USERS WITH ORGANIZATION (15)
            counter = 1

            for org in organizations:
                for i in range(1, 4):
                    user, created = await User.get_or_create(
                        email=f"user_org{counter}@gmail.com",
                        defaults={
                            "name": f"Org User {counter}",
                            "password": "user",
                            "role": UserRole.USER,
                            "organization": org,
                        },
                    )

                    if not user.password.startswith("$2b$"):
                        user.password = User.set_password("user")
                        await user.save()

                    print("👤 User (with org)" if created else "⚠️ Exists", user.email)

                    counter += 1

            print("\n🎉 USER SEEDING COMPLETED SUCCESSFULLY")

    except IntegrityError as e:
        print("❌ Integrity error:", e)

    except Exception as e:
        print("❌ Unexpected error:", e)
