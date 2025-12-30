from django.db import models

class TaskExecution(models.Model):
    process_execution = models.ForeignKey(
        "ProcessExecution",
        on_delete=models.CASCADE,
        related_name="task_executions"
    )

    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE
    )

    input_payload = models.JSONField()
    output_payload = models.JSONField(null=True, blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="running"
    )

    error = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.task.name} (Exec {self.process_execution.id})"

