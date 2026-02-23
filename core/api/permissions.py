from rest_framework import permissions
from core.models import Task, TaskExecution


class CanExecuteTask(permissions.BasePermission):
    message = "You do not have permission to execute this task."

    def has_permission(self, request, view):
        task_id = view.kwargs.get('task_id')

        if not task_id:
            return False

        try:
            task = Task.objects.with_permissions().get(id=task_id)
        except Task.DoesNotExist:
            return False

        return task.has_user_access(request.user)


class CanViewTaskExecutions(permissions.BasePermission):
    message = "You do not have permission to view executions of this task."

    def has_permission(self, request, view):
        task_id = view.kwargs.get('task_id')

        if not task_id:
            return False

        try:
            task = Task.objects.with_permissions().get(id=task_id)
        except Task.DoesNotExist:
            return False

        return task.has_user_access(request.user)


class CanViewExecutionDetail(permissions.BasePermission):
    message = "You do not have permission to view this execution."

    def has_permission(self, request, view):
        execution_id = view.kwargs.get('execution_id')

        if not execution_id:
            return False

        try:
            execution = TaskExecution.objects.select_related(
                'task__permission'
            ).get(id=execution_id)
        except TaskExecution.DoesNotExist:
            return False

        return execution.task.has_user_access(request.user)