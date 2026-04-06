from tortoise import fields, models

class Task(models.Model):
    name = fields.CharField(max_length=100)
    description = fields.CharField(max_length=500)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    def __str__(self):
        return self.name
    class Meta:
        db_table = "task"
        ordering = ["created_at"]