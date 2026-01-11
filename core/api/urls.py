from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from core.api.views import (
    ProcessListAPIView,
    ExecuteProcessAPIView,
    ProcessExecutionDetailAPIView,
    ProcessExecutionsAPIView,
    ExecutionTasksAPIView,
)

urlpatterns = [
    # ========== Authentication Endpoints ==========
    # Obter token (login)
    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),
    
    # Refresh token
    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),
    
    # Verificar se token é válido
    path(
        "auth/token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify"
    ),
    
    # ========== Process Endpoints ==========
    # Listar processos acessíveis
    path(
        "processes/",
        ProcessListAPIView.as_view(),
        name="process_list"
    ),
    
    # ========== Process Execution Endpoints ==========
    path(
        "processes/<int:process_id>/execute/",
        ExecuteProcessAPIView.as_view(),
        name="execute_process"
    ),
    
    path(
        "executions/<int:execution_id>/",
        ProcessExecutionDetailAPIView.as_view(),
        name="execution_detail"
    ),
    
    path(
        "processes/<int:process_id>/executions/",
        ProcessExecutionsAPIView.as_view(),
        name="process_executions"
    ),
    
    path(
        "executions/<int:execution_id>/tasks/",
        ExecutionTasksAPIView.as_view(),
        name="execution_tasks"
    ),
]