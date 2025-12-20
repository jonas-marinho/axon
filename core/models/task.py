from django.db import models
from core.models.agent import Agent


class Task(models.Model):
    name = models.CharField(max_length=255)

    agent = models.ForeignKey(
        Agent,
        on_delete=models.PROTECT,
        related_name="tasks"
    )

    # Mapeia dados do state -> input do agente
    input_mapping = models.JSONField(null=True, blank=True)

    # Mapeia output do agente -> state
    output_mapping = models.JSONField(null=True, blank=True)

    description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "task"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

