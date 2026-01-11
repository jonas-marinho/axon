from django.db import models
from core.models.task import Task


class ProcessQuerySet(models.QuerySet):
    """
    Custom QuerySet para Process com métodos úteis.
    """
    
    def with_permissions(self):
        """
        Otimiza queries incluindo as permissões com select_related.
        
        Uso: Process.objects.with_permissions().all()
        """
        return self.select_related('permission')
    
    def accessible_by(self, user):
        """
        Retorna apenas processos que o usuário tem permissão de acessar.
        
        Args:
            user: User instance ou None
        
        Returns:
            QuerySet filtrado
        """
        from django.db.models import Q
        
        # Se é superuser, retorna tudo
        if user and user.is_authenticated and user.is_superuser:
            return self.filter(is_active=True)
        
        # Processos open (todos podem acessar)
        open_q = Q(permission__access_type='open')
        
        # Processos public (apenas autenticados)
        if user and user.is_authenticated:
            public_q = Q(permission__access_type='public')
            
            # Processos restricted onde o user está na lista
            user_q = Q(permission__allowed_users=user)
            
            # Processos restricted onde o user pertence a um grupo
            groups_q = Q(permission__allowed_groups__in=user.groups.all())
            
            return self.filter(
                is_active=True
            ).filter(
                open_q | public_q | user_q | groups_q
            ).distinct()
        
        # Usuário anônimo: apenas open
        return self.filter(
            is_active=True,
            permission__access_type='open'
        )


class Process(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    entry_task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT,
        related_name="entry_for_process"
    )

    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager
    objects = ProcessQuerySet.as_manager()

    class Meta:
        db_table = "process"
        unique_together = ("name", "version")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def has_user_access(self, user=None):
        """
        Shortcut para verificar se um usuário tem acesso ao processo.
        
        Args:
            user: User instance ou None (usuário anônimo)
        
        Returns:
            bool: True se tem acesso, False caso contrário
        
        Uso:
            if process.has_user_access(request.user):
                # executar processo
        """
        # Garante que existe uma permissão
        if not hasattr(self, 'permission'):
            from core.models import ProcessPermission
            ProcessPermission.objects.create(
                process=self,
                access_type='restricted'
            )
            # Refresh para carregar a permissão
            self.refresh_from_db()
        
        return self.permission.has_access(user)
    
    @property
    def access_type(self):
        """
        Property para facilitar acesso ao tipo de permissão.
        
        Uso: process.access_type => 'public'
        """
        if hasattr(self, 'permission'):
            return self.permission.access_type
        return 'restricted'  # Padrão se não existe
    
    def get_allowed_users_count(self):
        """
        Retorna quantidade de usuários com acesso explícito.
        """
        if hasattr(self, 'permission'):
            return self.permission.allowed_users.count()
        return 0
    
    def get_allowed_groups_count(self):
        """
        Retorna quantidade de grupos com acesso explícito.
        """
        if hasattr(self, 'permission'):
            return self.permission.allowed_groups.count()
        return 0