from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from core.api.views import (
    TaskListAPIView,
    ExecuteTaskAPIView,
    TaskExecutionsAPIView,
    ExecutionDetailAPIView,
)

urlpatterns = [
    # ========== Authentication ==========
    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),
    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh"
    ),
    path(
        "auth/token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify"
    ),

    # ========== Tasks ==========
    path(
        "tasks/",
        TaskListAPIView.as_view(),
        name="task_list"
    ),
    path(
        "tasks/<int:task_id>/execute/",
        ExecuteTaskAPIView.as_view(),
        name="execute_task"
    ),
    path(
        "tasks/<int:task_id>/executions/",
        TaskExecutionsAPIView.as_view(),
        name="task_executions"
    ),

    # ========== Executions ==========
    path(
        "executions/<int:execution_id>/",
        ExecutionDetailAPIView.as_view(),
        name="execution_detail"
    ),
]