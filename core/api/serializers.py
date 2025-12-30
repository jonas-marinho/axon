from rest_framework import serializers
from core.models import ProcessExecution
from core.models import TaskExecution


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
