from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver


class TaskPermission(models.Model):
    """
    Define permissões de acesso a uma Task.

    Uma task pode ser:
    - Restrita (apenas users/groups específicos)
    - Pública (qualquer usuário autenticado)
    - Aberta (até usuários não autenticados)
    """

    ACCESS_TYPES = [
        ('restricted', 'Restricted'),
        ('public', 'Public'),
        ('open', 'Open'),
    ]

    task = models.OneToOneField(
        'Task',
        on_delete=models.CASCADE,
        related_name='permission',
        help_text="Task à qual esta permissão se aplica"
    )

    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPES,
        default='restricted',
        help_text="Tipo de acesso à task"
    )

    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='task_permissions',
        help_text="Usuários com acesso (apenas para access_type='restricted')"
    )

    allowed_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='task_permissions',
        help_text="Grupos com acesso (apenas para access_type='restricted')"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "task_permission"
        verbose_name = "Task Permission"
        verbose_name_plural = "Task Permissions"

    def __str__(self):
        return f"{self.task.name} - {self.get_access_type_display()}"

    def has_access(self, user=None) -> bool:
        if self.access_type == 'open':
            return True

        if self.access_type == 'public':
            return user is not None and user.is_authenticated

        if self.access_type == 'restricted':
            if not user or not user.is_authenticated:
                return False

            if user.is_superuser:
                return True

            if self.allowed_users.filter(id=user.id).exists():
                return True

            if self.allowed_groups.filter(user=user).exists():
                return True

            return False

        return False


@receiver(post_save, sender='core.Task')
def create_default_task_permission(sender, instance, created, **kwargs):
    """
    Cria uma permissão 'restricted' padrão quando uma Task é criada.
    """
    if created and not hasattr(instance, 'permission'):
        TaskPermission.objects.create(
            task=instance,
            access_type='restricted'
        )
 