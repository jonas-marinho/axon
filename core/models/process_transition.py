from django.db import models

from core.models.process import Process
from core.models.task import Task

class ProcessTransition(models.Model):

    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name="transitions"
    )

    from_task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT,
        related_name="outgoing_transitions"
    )

    to_task = models.ForeignKey(
        Task,
        on_delete=models.PROTECT,
        related_name="incoming_transitions"
    )

    condition = models.TextField(
        help_text="Ex: results.output.confidence >= 0.8"
    )

    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "process_transitions"
        ordering = ["order"]

    def __str__(self):
        return f"{self.from_task} → {self.to_task}"

