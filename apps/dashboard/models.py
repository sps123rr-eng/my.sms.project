from django.db import models


class ActivityLog(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=255)
    module = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.display_name if self.user else "System"
        return f"[{self.module}] {user_str}: {self.action} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"


def log_activity(user, action, module="General"):
    """
    Utility function to record an activity in the real database activity log.
    """
    try:
        ActivityLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            module=module
        )
    except Exception:
        pass
