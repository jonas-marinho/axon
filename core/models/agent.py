from django.db import models


class Agent(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)

    llm_config = models.JSONField(
        default=dict,
        help_text="Configuração do LLM (provider, model, params)"
    )
    system_prompt = models.TextField()
    tools_config = models.JSONField(null=True, blank=True)
    output_schema = models.JSONField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "agent"
        unique_together = ("name", "version")
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version})"

