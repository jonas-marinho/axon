from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Process
from core.services.process_executor import ProcessExecutor
from core.api.serializers import ProcessExecutionSerializer


class ExecuteProcessAPIView(APIView):

    def post(self, request, process_id):
        try:
            process = Process.objects.get(id=process_id)
        except Process.DoesNotExist:
            return Response(
                {"error": "Process not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        executor = ProcessExecutor(process.name)

        result = executor.execute(
            input_payload=request.data
        )

        execution = process.processexecution_set.latest("started_at")

        serializer = ProcessExecutionSerializer(execution)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProcessExecutionDetailAPIView(APIView):

    def get(self, request, execution_id):
        from core.models import ProcessExecution

        try:
            execution = ProcessExecution.objects.get(id=execution_id)
        except ProcessExecution.DoesNotExist:
            return Response(
                {"error": "Execution not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProcessExecutionSerializer(execution)
        return Response(serializer.data)


class ProcessExecutionsAPIView(APIView):

    def get(self, request, process_id):
        from core.models import ProcessExecution

        executions = ProcessExecution.objects.filter(
            process_id=process_id
        ).order_by("-started_at")

        serializer = ProcessExecutionSerializer(
            executions,
            many=True
        )
        return Response(serializer.data)


class ExecutionTasksAPIView(APIView):

    def get(self, request, execution_id):
        from core.models import TaskExecution

        tasks = TaskExecution.objects.filter(
            process_execution_id=execution_id
        )

        serializer = TaskExecutionSerializer(tasks, many=True)
        return Response(serializer.data)
