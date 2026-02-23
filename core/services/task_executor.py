import logging
from typing import Dict, Any

from django.utils import timezone

from core.models import Task, TaskExecution
from core.services.agent_factory import AgentFactory

logger = logging.getLogger(__name__)


class TaskExecutor:
    def __init__(self, task_id: int):
        logger.info(f"Inicializando TaskExecutor para task ID: {task_id}")
        self.agent_factory = AgentFactory()
        self.task = self._get_task(task_id)
        logger.info(f"TaskExecutor inicializado — Task: '{self.task.name}'")

    def execute(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a task com o payload fornecido.

        O input_mapping da task é aplicado sobre {"input": input_payload},
        permitindo que mapeamentos como "input.product" continuem funcionando.
        """
        logger.info(f"===== INICIANDO EXECUÇÃO DA TASK: '{self.task.name}' =====")
        logger.debug(f"Input payload recebido: {input_payload}")

        task_execution = TaskExecution.objects.create(
            task=self.task,
            input_payload=input_payload,
            status="running"
        )
        logger.info(f"TaskExecution criado — ID: {task_execution.id}")

        try:
            resolved_input = self._resolve_input(input_payload)
            logger.debug(f"Input resolvido após mapping: {resolved_input}")

            agent_runtime = self.agent_factory.create(
                self.task.agent,
                output_schema=self.task.output_schema
            )

            output = agent_runtime.run(resolved_input)
            logger.info(f"Task '{self.task.name}' executada com sucesso")

            task_execution.output_payload = output
            task_execution.status = "completed"
            task_execution.finished_at = timezone.now()
            task_execution.save()

            logger.info(f"===== TASK '{self.task.name}' CONCLUÍDA =====")
            return output

        except Exception as e:
            logger.error(
                f"Erro na execução da task '{self.task.name}': {str(e)}",
                exc_info=True
            )
            task_execution.status = "failed"
            task_execution.error = str(e)
            task_execution.finished_at = timezone.now()
            task_execution.save()
            raise

    # ---------- Internos ----------

    def _get_task(self, task_id: int) -> Task:
        try:
            return Task.objects.select_related('agent').get(id=task_id)
        except Task.DoesNotExist:
            raise RuntimeError(f"Task com ID {task_id} não encontrada")

    def _resolve_input(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica o input_mapping da task sobre o payload recebido.

        Sem mapping → repassa o payload diretamente ao agent.
        Com mapping → resolve os caminhos usando {"input": input_payload} como estado.
        """
        if not self.task.input_mapping:
            return input_payload

        state = {"input": input_payload}
        resolved = {}

        for key, path in self.task.input_mapping.items():
            resolved[key] = self._get_by_path(state, path)

        return resolved

    @staticmethod
    def _get_by_path(data: Dict[str, Any], path: str):
        current = data
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current