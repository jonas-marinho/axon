from rest_framework import serializers
from core.models import Task, TaskExecution


class TaskSerializer(serializers.ModelSerializer):
    access_type = serializers.CharField(
        source='permission.access_type',
        read_only=True
    )
    allowed_users_count = serializers.SerializerMethodField()
    allowed_groups_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id',
            'name',
            'description',
            'access_type',
            'allowed_users_count',
            'allowed_groups_count',
        ]

    def get_allowed_users_count(self, obj):
        if hasattr(obj, 'permission') and obj.permission.access_type == 'restricted':
            return obj.get_allowed_users_count()
        return None

    def get_allowed_groups_count(self, obj):
        if hasattr(obj, 'permission') and obj.permission.access_type == 'restricted':
            return obj.get_allowed_groups_count()
        return None


class TaskExecutionSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = TaskExecution
        fields = [
            'id',
            'task',
            'task_name',
            'status',
            'input_payload',
            'output_payload',
            'started_at',
            'finished_at',
            'error',
        ]