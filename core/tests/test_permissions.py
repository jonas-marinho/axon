from dotenv import load_dotenv
from django.test import TestCase
from django.contrib.auth.models import User, Group

from core.models import Agent, Task, TaskPermission


class TaskPermissionTest(TestCase):
    """
    Testes para o sistema de permissões de Task.
    """

    def setUp(self):
        load_dotenv()

        # Usuários
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

        # Grupo
        self.marketing_group = Group.objects.create(name='Marketing')
        self.user2.groups.add(self.marketing_group)

        # Agent base
        self.agent = Agent.objects.create(
            name="TestAgent",
            role="Tester",
            system_prompt="Test prompt",
            llm_config={
                "provider": "openai",
                "model": "gpt-4o-mini"
            }
        )

        # Tasks com diferentes tipos de acesso
        self.task_restricted = Task.objects.create(
            name="RestrictedTask",
            agent=self.agent
        )
        self.task_public = Task.objects.create(
            name="PublicTask",
            agent=self.agent
        )
        self.task_open = Task.objects.create(
            name="OpenTask",
            agent=self.agent
        )

        # Configura permissões
        perm_restricted = self.task_restricted.permission
        perm_restricted.access_type = 'restricted'
        perm_restricted.save()
        perm_restricted.allowed_users.add(self.user1)

        perm_public = self.task_public.permission
        perm_public.access_type = 'public'
        perm_public.save()

        perm_open = self.task_open.permission
        perm_open.access_type = 'open'
        perm_open.save()

    def test_signal_creates_permission_automatically(self):
        """
        Signal deve criar TaskPermission ao criar uma Task.
        """
        new_task = Task.objects.create(
            name="NewTask",
            agent=self.agent
        )

        self.assertTrue(hasattr(new_task, 'permission'))
        self.assertEqual(new_task.permission.access_type, 'restricted')

    def test_restricted_access_allowed_user(self):
        self.assertTrue(
            self.task_restricted.has_user_access(self.user1)
        )

    def test_restricted_access_denied_user(self):
        self.assertFalse(
            self.task_restricted.has_user_access(self.user2)
        )

    def test_restricted_access_superuser(self):
        self.assertTrue(
            self.task_restricted.has_user_access(self.superuser)
        )

    def test_restricted_access_anonymous(self):
        self.assertFalse(
            self.task_restricted.has_user_access(None)
        )

    def test_public_access_authenticated(self):
        self.assertTrue(self.task_public.has_user_access(self.user1))
        self.assertTrue(self.task_public.has_user_access(self.user2))

    def test_public_access_anonymous_denied(self):
        self.assertFalse(
            self.task_public.has_user_access(None)
        )

    def test_open_access_everyone(self):
        self.assertTrue(self.task_open.has_user_access(None))
        self.assertTrue(self.task_open.has_user_access(self.user1))
        self.assertTrue(self.task_open.has_user_access(self.user2))

    def test_group_permission(self):
        """
        Permissão por grupo: user2 (Marketing) deve ter acesso,
        user1 (sem grupo) não.
        """
        task_group = Task.objects.create(
            name="GroupTask",
            agent=self.agent
        )

        perm = task_group.permission
        perm.access_type = 'restricted'
        perm.save()
        perm.allowed_groups.add(self.marketing_group)

        self.assertTrue(task_group.has_user_access(self.user2))
        self.assertFalse(task_group.has_user_access(self.user1))

    def test_queryset_accessible_by_user(self):
        """
        accessible_by() deve filtrar corretamente por usuário.
        """
        # user1: restricted (tem acesso) + public + open = 3
        accessible = Task.objects.accessible_by(self.user1)
        self.assertEqual(accessible.count(), 3)

        # user2: public + open = 2 (sem acesso ao restricted)
        accessible = Task.objects.accessible_by(self.user2)
        self.assertEqual(accessible.count(), 2)
        self.assertNotIn(self.task_restricted, accessible)

        # Anônimo: apenas open = 1
        accessible = Task.objects.accessible_by(None)
        self.assertEqual(accessible.count(), 1)
        self.assertIn(self.task_open, accessible)

        # Superuser: tudo = 3
        accessible = Task.objects.accessible_by(self.superuser)
        self.assertEqual(accessible.count(), 3)

    def test_task_permission_properties(self):
        """
        Testa as properties de acesso na Task.
        """
        self.assertEqual(self.task_restricted.access_type, 'restricted')
        self.assertEqual(self.task_public.access_type, 'public')
        self.assertEqual(self.task_open.access_type, 'open')

        self.assertEqual(self.task_restricted.get_allowed_users_count(), 1)
        self.assertEqual(self.task_public.get_allowed_users_count(), 0)

    def test_with_permissions_optimization(self):
        """
        with_permissions() deve reduzir o número de queries.
        """
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx1:
            task = Task.objects.get(id=self.task_restricted.id)
            _ = task.permission.access_type

        with CaptureQueriesContext(connection) as ctx2:
            task = Task.objects.with_permissions().get(
                id=self.task_restricted.id
            )
            _ = task.permission.access_type

        self.assertLess(len(ctx2), len(ctx1))