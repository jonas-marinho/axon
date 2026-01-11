from rest_framework import permissions
from core.models import Process, ProcessExecution


class CanExecuteProcess(permissions.BasePermission):
    """
    Permissão para executar um processo.
    Verifica se o usuário tem acesso ao processo especificado.
    """
    
    message = "You do not have permission to execute this process."
    
    def has_permission(self, request, view):
        """
        Verifica permissão no nível da view.
        """
        # Pega o process_id da URL
        process_id = view.kwargs.get('process_id')
        
        if not process_id:
            return False
        
        try:
            # Usa with_permissions() para otimizar
            process = Process.objects.with_permissions().get(id=process_id)
        except Process.DoesNotExist:
            return False
        
        # Usa o método helper do Process
        return process.has_user_access(request.user)


class CanViewProcessExecutions(permissions.BasePermission):
    """
    Permissão para visualizar execuções de um processo.
    Usa a mesma lógica de permissão do processo.
    """
    
    message = "You do not have permission to view executions of this process."
    
    def has_permission(self, request, view):
        """
        Verifica permissão no nível da view.
        """
        # Pega o process_id da URL
        process_id = view.kwargs.get('process_id')
        
        if not process_id:
            return False
        
        try:
            # Usa with_permissions() para otimizar
            process = Process.objects.with_permissions().get(id=process_id)
        except Process.DoesNotExist:
            return False
        
        # Usa o método helper do Process
        return process.has_user_access(request.user)


class CanViewExecutionDetail(permissions.BasePermission):
    """
    Permissão para visualizar detalhes de uma execução específica.
    Verifica se o usuário tem acesso ao processo da execução.
    """
    
    message = "You do not have permission to view this execution."
    
    def has_permission(self, request, view):
        """
        Verifica permissão no nível da view.
        """
        execution_id = view.kwargs.get('execution_id')
        
        if not execution_id:
            return False
        
        try:
            execution = ProcessExecution.objects.select_related(
                'process__permission'
            ).get(id=execution_id)
        except ProcessExecution.DoesNotExist:
            return False
        
        # Usa o método helper do Process
        return execution.process.has_user_access(request.user)