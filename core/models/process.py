from django.db import models
from core.models.task import Task


class Process(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    entry_task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT,
        related_name="entry_for_process"
    )

    # JSON que define nós, edges, condições, etc
    graph_definition = models.JSONField()

    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "process"
        unique_together = ("name", "version")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"

