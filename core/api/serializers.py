from rest_framework import serializers
from core.models import ProcessExecution, Process
from core.models import TaskExecution


class ProcessSerializer(serializers.ModelSerializer):
    """
    Serializer para listar processos com informações de permissão.
    """
    
    access_type = serializers.CharField(source='permission.access_type', read_only=True)
    allowed_users_count = serializers.SerializerMethodField()
    allowed_groups_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Process
        fields = [
            'id',
            'name',
            'description',
            'version',
            'is_active',
            'access_type',
            'allowed_users_count',
            'allowed_groups_count',
        ]
    
    def get_allowed_users_count(self, obj):
        """Retorna quantidade de usuários com acesso (apenas para restricted)"""
        if hasattr(obj, 'permission') and obj.permission.access_type == 'restricted':
            return obj.get_allowed_users_count()
        return None
    
    def get_allowed_groups_count(self, obj):
        """Retorna quantidade de grupos com acesso (apenas para restricted)"""
        if hasattr(obj, 'permission') and obj.permission.access_type == 'restricted':
            return obj.get_allowed_groups_count()
        return None


class ProcessExecutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProcessExecution
        fields = [
            "id",
            "process",
            "status",
            "input_payload",
            "state",
            "started_at",
            "finished_at",
        ]

class TaskExecutionSerializer(serializers.ModelSerializer):

    task_name = serializers.CharField(source="task.name")

    class Meta:
        model = TaskExecution
        fields = [
            "id",
            "task_name",
            "status",
            "input_payload",
            "output_payload",
            "started_at",
            "finished_at",
            "error",
        ]