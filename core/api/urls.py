from django.urls import path
from core.api.views import (
    ExecuteProcessAPIView,
    ProcessExecutionDetailAPIView,
    ProcessExecutionsAPIView,
    ExecutionTasksAPIView,
)

urlpatterns = [
    path(
        "processes/<int:process_id>/execute/",
        ExecuteProcessAPIView.as_view(),
    ),
    path(
        "executions/<int:execution_id>/",
        ProcessExecutionDetailAPIView.as_view(),
    ),
    path(
        "processes/<int:process_id>/executions/",
        ProcessExecutionsAPIView.as_view(),
    ),
    path(
        "executions/<int:execution_id>/tasks/",
        ExecutionTasksAPIView.as_view(),
    ),
]
