from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.models import Process
from core.services.process_executor import ProcessExecutor
from core.api.serializers import (
    ProcessExecutionSerializer,
    TaskExecutionSerializer,
    ProcessSerializer  # Vamos criar este
)
from core.api.permissions import (
    CanExecuteProcess,
    CanViewProcessExecutions,
    CanViewExecutionDetail
)


class ProcessListAPIView(APIView):
    """
    GET /api/v1/processes/
    
    Lista todos os processos que o usuário tem acesso.
    """
    
    # Permite acesso sem autenticação para ver processos 'open'
    permission_classes = []
    
    def get(self, request):
        """
        Retorna lista de processos acessíveis pelo usuário.
        """
        user = request.user if request.user.is_authenticated else None
        
        # Usa o método otimizado do QuerySet
        processes = Process.objects.with_permissions().accessible_by(user)
        
        serializer = ProcessSerializer(processes, many=True)
        return Response(serializer.data)


class ExecuteProcessAPIView(APIView):
    """
    POST /api/v1/processes/{process_id}/execute/
    
    Executa um processo com o payload fornecido.
    Requer autenticação (exceto se o processo for 'open').
    """
    
    def get_permissions(self):
        """
        Permissões customizadas por método.
        """
        return [CanExecuteProcess()]
    
    def post(self, request, process_id):
        try:
            process = Process.objects.with_permissions().get(id=process_id)
        except Process.DoesNotExist:
            return Response(
                {"error": "Process not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        executor = ProcessExecutor(process.name)
        
        try:
            result = executor.execute(
                input_payload=request.data
            )
        except Exception as e:
            return Response(
                {
                    "error": "Process execution failed",
                    "detail": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        execution = process.processexecution_set.latest("started_at")
        serializer = ProcessExecutionSerializer(execution)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProcessExecutionDetailAPIView(APIView):
    """
    GET /api/v1/executions/{execution_id}/
    
    Retorna detalhes de uma execução específica.
    """
    
    permission_classes = [CanViewExecutionDetail]
    
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
    """
    GET /api/v1/processes/{process_id}/executions/
    
    Lista todas as execuções de um processo.
    """
    
    permission_classes = [CanViewProcessExecutions]
    
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
    """
    GET /api/v1/executions/{execution_id}/tasks/
    
    Lista todas as tasks executadas em uma execução.
    """
    
    permission_classes = [CanViewExecutionDetail]
    
    def get(self, request, execution_id):
        from core.models import TaskExecution
        
        tasks = TaskExecution.objects.filter(
            process_execution_id=execution_id
        )
        
        serializer = TaskExecutionSerializer(tasks, many=True)
        return Response(serializer.data)