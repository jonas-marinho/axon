from django.db import models


class TaskExecution(models.Model):
    task = models.ForeignKey(
        "Task",
        on_delete=models.CASCADE,
        related_name="executions"
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
        return f"{self.task.name} (Exec {self.id})"