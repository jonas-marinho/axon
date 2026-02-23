from django.db import models
from core.models.agent import Agent


class TaskQuerySet(models.QuerySet):

    def with_permissions(self):
        return self.select_related('permission')

    def accessible_by(self, user):
        from django.db.models import Q

        if user and user.is_authenticated and user.is_superuser:
            return self

        open_q = Q(permission__access_type='open')

        if user and user.is_authenticated:
            public_q = Q(permission__access_type='public')
            user_q = Q(permission__allowed_users=user)
            groups_q = Q(permission__allowed_groups__in=user.groups.all())

            return self.filter(
                open_q | public_q | user_q | groups_q
            ).distinct()

        return self.filter(permission__access_type='open')


class Task(models.Model):
    name = models.CharField(max_length=255)

    agent = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        related_name="tasks"
    )

    input_mapping = models.JSONField(null=True, blank=True)
    output_mapping = models.JSONField(null=True, blank=True)

    output_schema = models.JSONField(
        null=True,
        blank=True,
        help_text="Define o formato de saída. Se None, retorna texto puro."
    )

    description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TaskQuerySet.as_manager()

    class Meta:
        db_table = "task"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def has_user_access(self, user=None) -> bool:
        if not hasattr(self, 'permission'):
            from core.models.task_permission import TaskPermission
            TaskPermission.objects.create(task=self, access_type='restricted')
            self.refresh_from_db()

        return self.permission.has_access(user)

    @property
    def access_type(self):
        if hasattr(self, 'permission'):
            return self.permission.access_type
        return 'restricted'

    def get_allowed_users_count(self):
        if hasattr(self, 'permission'):
            return self.permission.allowed_users.count()
        return 0

    def get_allowed_groups_count(self):
        if hasattr(self, 'permission'):
            return self.permission.allowed_groups.count()
        return 0