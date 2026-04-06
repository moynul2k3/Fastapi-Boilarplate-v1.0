from datetime import datetime, timedelta, timezone
from enum import Enum

from tortoise import models, fields

class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"



class UserPlan(models.Model):
    id = fields.UUIDField(pk=True)

    # Basic Info
    user = fields.OneToOneField("models.User", related_name="subscription", on_delete=fields.CASCADE)
    plan = fields.ForeignKeyField("models.Plan", related_name="plan", on_delete=fields.SET_NULL, null=True)

    # Dispute Features
    basic_dispute_generation = fields.BooleanField(default=False)
    unlimited_disputes = fields.BooleanField(default=False)
    disputes_per_month = fields.IntField(null=True)

    # Support Features
    email_support = fields.BooleanField(default=False)
    priority_email_support = fields.BooleanField(default=False)
    phone_support_24_7 = fields.BooleanField(default=False)
    dedicated_account_manager = fields.BooleanField(default=False)

    # Education Features
    access_basic_modules = fields.BooleanField(default=False)
    access_all_modules = fields.BooleanField(default=False)

    # AI / Advanced Features
    ai_task_recommendations = fields.BooleanField(default=False)
    advanced_analytics = fields.BooleanField(default=False)
    regular_task_alerts = fields.BooleanField(default=False)
    ai_token = fields.IntField(null=True)

    # Pricing
    price = fields.DecimalField(max_digits=10, decimal_places=2, null=True, default=0.0)

    # manage_plan
    duration_days = fields.IntField(default=30)
    paused_at = fields.DatetimeField(null=True)
    started_at = fields.DatetimeField(null=True)

    status = fields.CharEnumField(SubscriptionStatus, default=SubscriptionStatus.ACTIVE)
    auto_renewal = fields.BooleanField(default=True)
    current_period_end = fields.DatetimeField(null=True)
    cancel_at_period_end = fields.BooleanField(default=False)

    # Stripe Info
    stripe_customer_id = fields.CharField(max_length=255, null=True)
    stripe_subscription_id = fields.CharField(max_length=255, null=True)
    stripe_price_id = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "user_plans"

    @property
    def expires_at(self):
        if not self.started_at:
            return None
        return self.started_at + timedelta(days=self.duration_days)

    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    # Pause Plan
    async def pause_plan(self):
        if self.status != SubscriptionStatus.ACTIVE:
            return
        if self.is_expired:
            return
        now = datetime.now(timezone.utc)
        remaining_seconds = (self.expires_at - now).total_seconds()
        remaining_days = max(int(remaining_seconds // 86400), 0)

        self.duration_days = remaining_days
        self.paused_at = now
        self.status = SubscriptionStatus.PAUSED
        await self.save()


    # Resume Plan
    async def resume_plan(self):
        if self.status != SubscriptionStatus.PAUSED:
            return
        now = datetime.now(timezone.utc)
        self.started_at = now
        self.paused_at = None
        self.status = SubscriptionStatus.ACTIVE
        await self.save()

    def _sync_with_plan(self):
        if not self.plan:
            return

        self.basic_dispute_generation = self.plan.basic_dispute_generation
        self.unlimited_disputes = self.plan.unlimited_disputes
        self.disputes_per_month = self.plan.disputes_per_month

        self.email_support = self.plan.email_support
        self.priority_email_support = self.plan.priority_email_support
        self.phone_support_24_7 = self.plan.phone_support_24_7
        self.dedicated_account_manager = self.plan.dedicated_account_manager

        self.access_basic_modules = self.plan.access_basic_modules
        self.access_all_modules = self.plan.access_all_modules

        self.ai_task_recommendations = self.plan.ai_task_recommendations
        self.advanced_analytics = self.plan.advanced_analytics
        self.regular_task_alerts = self.plan.regular_task_alerts
        self.ai_token = self.plan.ai_token

        self.price = self.plan.price
        self.duration_days = self.plan.duration_days

    async def renew(self, at_now: bool = False):
        if not self.plan:
            return
        now = datetime.now(timezone.utc)
        if at_now:
            base_time = now
        # Auto-renew
        elif self.auto_renewal and self.is_expired and self.status == SubscriptionStatus.ACTIVE:
            # extend from previous expiry (not from now)
            base_time = self.expires_at or now
        else:
            return
        self._sync_with_plan()

        # Reset subscription timing
        self.started_at = base_time
        self.paused_at = None
        self.status = SubscriptionStatus.ACTIVE

        await self.save()





class Plan(models.Model):
    id = fields.UUIDField(pk=True)

    # Basic Info
    name = fields.CharField(max_length=50, unique=True)
    description = fields.TextField(null=True)

    # Duration
    duration_days = fields.IntField(default=30)

    # Dispute Features
    basic_dispute_generation = fields.BooleanField(default=False)
    unlimited_disputes = fields.BooleanField(default=False)
    disputes_per_month = fields.IntField(null=True)

    # Support Features
    email_support = fields.BooleanField(default=False)
    priority_email_support = fields.BooleanField(default=False)
    phone_support_24_7 = fields.BooleanField(default=False)
    dedicated_account_manager = fields.BooleanField(default=False)

    # Education Features
    access_basic_modules = fields.BooleanField(default=False)
    access_all_modules = fields.BooleanField(default=False)

    # AI / Advanced Features
    ai_task_recommendations = fields.BooleanField(default=False)
    advanced_analytics = fields.BooleanField(default=False)
    regular_task_alerts = fields.BooleanField(default=False)
    ai_token = fields.IntField(null=True)

    # Pricing
    price = fields.DecimalField(max_digits=10, decimal_places=2, null=True, default=0.0)

    is_active = fields.BooleanField(default=True)

    # Stripe Info
    stripe_product_id = fields.CharField(max_length=255, null=True)
    stripe_price_id = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "plans"



"""
* ✔ No string-based expiry
* ✔ `is_expired` boolean check
* ✔ Auto-renew only when:
  * `auto_renewal == True`
  * `is_expired == True`
  * `status == ACTIVE`
* ✔ Extends from previous expiry (professional logic)
* ✔ `_sync_with_plan()` clean
* ✔ No incorrect `await`

---

## Current Behavior Summary
### Manual Renew
### Auto Renew (cron/background job)
Works only if:
* Expired
* Auto renewal enabled
* Still ACTIVE

---

Your subscription lifecycle now properly supports:
* Activate
* Pause
* Resume
* Expiry check
* Manual renew
* Auto renew
* Plan feature sync

"""
