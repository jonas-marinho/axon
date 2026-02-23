from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Task, TaskExecution
from core.services.task_executor import TaskExecutor
from core.api.serializers import TaskSerializer, TaskExecutionSerializer
from core.api.permissions import (
    CanExecuteTask,
    CanViewTaskExecutions,
    CanViewExecutionDetail,
)


class TaskListAPIView(APIView):
    """
    GET /api/v1/tasks/

    Lista todas as tasks que o usuário tem acesso.
    """

    permission_classes = []

    def get(self, request):
        user = request.user if request.user.is_authenticated else None
        tasks = Task.objects.with_permissions().accessible_by(user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class ExecuteTaskAPIView(APIView):
    """
    POST /api/v1/tasks/{task_id}/execute/

    Executa uma task com o payload fornecido.
    """

    def get_permissions(self):
        return [CanExecuteTask()]

    def post(self, request, task_id):
        try:
            task = Task.objects.with_permissions().get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        executor = TaskExecutor(task.id)

        try:
            executor.execute(input_payload=request.data)
        except Exception as e:
            return Response(
                {"error": "Task execution failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        execution = task.executions.latest("started_at")
        serializer = TaskExecutionSerializer(execution)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskExecutionsAPIView(APIView):
    """
    GET /api/v1/tasks/{task_id}/executions/

    Lista todas as execuções de uma task.
    """

    permission_classes = [CanViewTaskExecutions]

    def get(self, request, task_id):
        executions = TaskExecution.objects.filter(
            task_id=task_id
        ).order_by("-started_at")

        serializer = TaskExecutionSerializer(executions, many=True)
        return Response(serializer.data)


class ExecutionDetailAPIView(APIView):
    """
    GET /api/v1/executions/{execution_id}/

    Retorna detalhes de uma execução específica.
    """

    permission_classes = [CanViewExecutionDetail]

    def get(self, request, execution_id):
        try:
            execution = TaskExecution.objects.get(id=execution_id)
        except TaskExecution.DoesNotExist:
            return Response(
                {"error": "Execution not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TaskExecutionSerializer(execution)
        return Response(serializer.data)