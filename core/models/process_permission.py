from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver


class ProcessPermission(models.Model):
    """
    Define permissões de acesso a um Process.
    
    Um processo pode ser:
    - Público (qualquer usuário autenticado)
    - Aberto (até usuários não autenticados)
    - Restrito (apenas users/groups específicos)
    """
    
    ACCESS_TYPES = [
        ('restricted', 'Restricted'),  # Apenas users/groups listados
        ('public', 'Public'),          # Qualquer usuário autenticado
        ('open', 'Open'),              # Até não autenticados
    ]
    
    process = models.OneToOneField(
        'Process',
        on_delete=models.CASCADE,
        related_name='permission',
        help_text="Processo ao qual esta permissão se aplica"
    )
    
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPES,
        default='restricted',
        help_text="Tipo de acesso ao processo"
    )
    
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='process_permissions',
        help_text="Usuários com acesso (apenas para access_type='restricted')"
    )
    
    allowed_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='process_permissions',
        help_text="Grupos com acesso (apenas para access_type='restricted')"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "process_permission"
        verbose_name = "Process Permission"
        verbose_name_plural = "Process Permissions"
    
    def __str__(self):
        return f"{self.process.name} - {self.get_access_type_display()}"
    
    def has_access(self, user=None):
        """
        Verifica se um usuário tem acesso ao processo.
        
        Args:
            user: User instance ou None (usuário anônimo)
        
        Returns:
            bool: True se tem acesso, False caso contrário
        """
        # Open: todos têm acesso
        if self.access_type == 'open':
            return True
        
        # Public: apenas autenticados
        if self.access_type == 'public':
            return user is not None and user.is_authenticated
        
        # Restricted: verifica users/groups
        if self.access_type == 'restricted':
            if not user or not user.is_authenticated:
                return False
            
            # Superuser sempre tem acesso
            if user.is_superuser:
                return True
            
            # Verifica se está na lista de usuários
            if self.allowed_users.filter(id=user.id).exists():
                return True
            
            # Verifica se está em algum grupo permitido
            if self.allowed_groups.filter(user=user).exists():
                return True
            
            return False
        
        return False


# Signal para criar ProcessPermission automaticamente
@receiver(post_save, sender='core.Process')
def create_default_permission(sender, instance, created, **kwargs):
    """
    Cria uma permissão 'restricted' padrão quando um Process é criado.
    """
    if created:
        # Verifica se já não existe (evita duplicação)
        if not hasattr(instance, 'permission'):
            ProcessPermission.objects.create(
                process=instance,
                access_type='restricted'
            )