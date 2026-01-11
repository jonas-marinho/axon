import os
from dotenv import load_dotenv
from django.test import TestCase
from django.contrib.auth.models import User, Group

from core.models import (
    Agent,
    Task,
    Process,
    ProcessPermission
)


class ProcessPermissionTest(TestCase):
    """
    Testes para o sistema de permissões de Process.
    """
    
    def setUp(self):
        """
        Configuração inicial para os testes.
        """
        load_dotenv()
        
        # Criar usuários
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='pass123'
        )
        
        # Criar grupo
        self.marketing_group = Group.objects.create(name='Marketing')
        self.user2.groups.add(self.marketing_group)
        
        # Criar Agent e Task
        self.agent = Agent.objects.create(
            name="TestAgent",
            role="Tester",
            system_prompt="Test prompt",
            llm_config={
                "provider": "openai",
                "model": "gpt-5-nano"
            }
        )
        
        self.task = Task.objects.create(
            name="test_task",
            agent=self.agent
        )
        
        # Criar processos com diferentes tipos de acesso
        self.process_restricted = Process.objects.create(
            name="RestrictedProcess",
            entry_task=self.task
        )
        
        self.process_public = Process.objects.create(
            name="PublicProcess",
            entry_task=self.task
        )
        
        self.process_open = Process.objects.create(
            name="OpenProcess",
            entry_task=self.task
        )
        
        # Configurar permissões
        # Restricted: apenas user1 tem acesso
        perm_restricted = self.process_restricted.permission
        perm_restricted.access_type = 'restricted'
        perm_restricted.save()
        perm_restricted.allowed_users.add(self.user1)
        
        # Public: qualquer autenticado
        perm_public = self.process_public.permission
        perm_public.access_type = 'public'
        perm_public.save()
        
        # Open: até não autenticados
        perm_open = self.process_open.permission
        perm_open.access_type = 'open'
        perm_open.save()
    
    def test_signal_creates_permission_automatically(self):
        """
        Testa se o signal cria ProcessPermission ao criar um Process.
        """
        new_process = Process.objects.create(
            name="NewProcess",
            entry_task=self.task
        )
        
        # Deve ter criado a permissão automaticamente
        self.assertTrue(hasattr(new_process, 'permission'))
        self.assertEqual(new_process.permission.access_type, 'restricted')
    
    def test_restricted_access_allowed_user(self):
        """
        Testa acesso restrito para usuário permitido.
        """
        self.assertTrue(
            self.process_restricted.has_user_access(self.user1)
        )
    
    def test_restricted_access_denied_user(self):
        """
        Testa acesso restrito negado para usuário não permitido.
        """
        self.assertFalse(
            self.process_restricted.has_user_access(self.user2)
        )
    
    def test_restricted_access_superuser(self):
        """
        Testa que superuser sempre tem acesso.
        """
        self.assertTrue(
            self.process_restricted.has_user_access(self.superuser)
        )
    
    def test_restricted_access_anonymous(self):
        """
        Testa que usuário anônimo não tem acesso a restricted.
        """
        self.assertFalse(
            self.process_restricted.has_user_access(None)
        )
    
    def test_public_access_authenticated(self):
        """
        Testa acesso público para usuários autenticados.
        """
        self.assertTrue(
            self.process_public.has_user_access(self.user1)
        )
        self.assertTrue(
            self.process_public.has_user_access(self.user2)
        )
    
    def test_public_access_anonymous_denied(self):
        """
        Testa que usuário anônimo não tem acesso a public.
        """
        self.assertFalse(
            self.process_public.has_user_access(None)
        )
    
    def test_open_access_everyone(self):
        """
        Testa que processo open permite acesso a todos.
        """
        self.assertTrue(
            self.process_open.has_user_access(None)
        )
        self.assertTrue(
            self.process_open.has_user_access(self.user1)
        )
        self.assertTrue(
            self.process_open.has_user_access(self.user2)
        )
    
    def test_group_permission(self):
        """
        Testa permissão por grupo.
        """
        # Criar processo com permissão para grupo Marketing
        process_group = Process.objects.create(
            name="GroupProcess",
            entry_task=self.task
        )
        
        perm = process_group.permission
        perm.access_type = 'restricted'
        perm.save()
        perm.allowed_groups.add(self.marketing_group)
        
        # user2 pertence ao grupo Marketing
        self.assertTrue(process_group.has_user_access(self.user2))
        
        # user1 não pertence ao grupo
        self.assertFalse(process_group.has_user_access(self.user1))
    
    def test_queryset_accessible_by_user(self):
        """
        Testa o método accessible_by do QuerySet.
        """
        # user1 pode ver: restricted (tem acesso), public, open
        accessible = Process.objects.accessible_by(self.user1)
        self.assertEqual(accessible.count(), 3)
        
        # user2 pode ver: public, open (não tem acesso ao restricted)
        accessible = Process.objects.accessible_by(self.user2)
        self.assertEqual(accessible.count(), 2)
        self.assertNotIn(self.process_restricted, accessible)
        
        # Usuário anônimo pode ver apenas: open
        accessible = Process.objects.accessible_by(None)
        self.assertEqual(accessible.count(), 1)
        self.assertIn(self.process_open, accessible)
        
        # Superuser vê tudo
        accessible = Process.objects.accessible_by(self.superuser)
        self.assertEqual(accessible.count(), 3)
    
    def test_process_properties(self):
        """
        Testa as properties do Process.
        """
        # access_type property
        self.assertEqual(self.process_restricted.access_type, 'restricted')
        self.assertEqual(self.process_public.access_type, 'public')
        self.assertEqual(self.process_open.access_type, 'open')
        
        # Counts
        self.assertEqual(self.process_restricted.get_allowed_users_count(), 1)
        self.assertEqual(self.process_public.get_allowed_users_count(), 0)
    
    def test_with_permissions_optimization(self):
        """
        Testa se with_permissions() otimiza queries.
        """
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        # Sem with_permissions (deve fazer query extra)
        with CaptureQueriesContext(connection) as ctx1:
            process = Process.objects.get(id=self.process_restricted.id)
            _ = process.permission.access_type
        
        # Com with_permissions (deve fazer menos queries)
        with CaptureQueriesContext(connection) as ctx2:
            process = Process.objects.with_permissions().get(
                id=self.process_restricted.id
            )
            _ = process.permission.access_type
        
        # with_permissions deve fazer menos queries
        self.assertLess(len(ctx2), len(ctx1))