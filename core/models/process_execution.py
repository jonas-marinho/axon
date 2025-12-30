from django.db import models

class ProcessExecution(models.Model):
    process = models.ForeignKey(
        "Process",
        on_delete=models.CASCADE
    )

    input_payload = models.JSONField()
    state = models.JSONField(default=dict)

    status = models.CharField(
        max_length=20,
        choices=[
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="running"
    )

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Execution {self.id} - {self.process.name}"

