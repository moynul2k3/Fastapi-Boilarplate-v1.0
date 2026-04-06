from tortoise import fields, models
from passlib.hash import bcrypt
from enum import Enum


class Permission(models.Model):
    id = fields.IntField(pk=True, readonly=True, hidden=True)
    name = fields.CharField(max_length=100, unique=True, editable=False)
    codename = fields.CharField(max_length=100, unique=True, editable=False)

    def __str__(self):
        return f"{self.codename}"


class Group(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)

    permissions: fields.ManyToManyRelation["Permission"] = fields.ManyToManyField(
        "models.Permission", related_name="groups", through="group_permissions"
    )

    def __str__(self):
        return self.name


class UserRole(str, Enum):
    USER = "USER"
    ORGANIZATION = "organization"
    ADMIN = "ADMIN"

class User(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=50, null=True, blank=True)
    email = fields.CharField(max_length=100, null=True, unique=True)
    password = fields.CharField(max_length=128)

    photo = fields.CharField(max_length=255, null=True, blank=True)
    phone = fields.CharField(max_length=255, null=True, blank=True)
    address = fields.CharField(max_length=255, null=True, blank=True)
    dob = fields.DateField(null=True, blank=True)

    role = fields.CharEnumField(UserRole, default=UserRole.USER)

    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    is_superadmin = fields.BooleanField(default=False)

    last_login_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    organization = fields.ForeignKeyField("models.User", related_name="organizations", null=True, blank=True)

    groups: fields.ManyToManyRelation["Group"] = fields.ManyToManyField(
        "models.Group", related_name="users", through="user_groups"
    )

    user_permissions: fields.ManyToManyRelation["Permission"] = fields.ManyToManyField(
        "models.Permission", related_name="users", through="user_permissions"
    )

    @property
    async def is_organization(self)->bool:
        return not bool(self.organization)


    async def has_permission(self, codename: str) -> bool:
        if self.role == UserRole.ADMIN or self.is_superadmin:
            return True

        await self.fetch_related("user_permissions", "groups__permissions")

        if self.is_staff:
            for perm in self.user_permissions:
                if perm.codename == codename:
                    return True

            for group in self.groups:
                for perm in group.permissions:
                    if perm.codename == codename:
                        return True
        return False

    @classmethod
    def set_password(cls, password: str) -> str:
        return bcrypt.hash(password)

    def verify_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password)

    class Meta:
        table = "users"

    def __str__(self):
        return f"{self.name} ({self.email})"

    async def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("$2b$"):
            self.password = self.set_password(self.password)

        await super().save(*args, **kwargs)
