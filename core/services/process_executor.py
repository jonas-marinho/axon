from typing import Dict, Any

from django.utils import timezone

from core.models import Process, Task
from core.models import ProcessExecution, TaskExecution
from core.services.agent_factory import AgentFactory
from core.services.condition_evaluator import ConditionEvaluator
# from core.services.graph_builder import GraphBuilder
from core.services.mapping_resolver import MappingResolver


class ProcessExecutor:
    def __init__(self, process_name):
        self.agent_factory = AgentFactory()
        self.process = self._get_process(process_name)

    def execute(
        self,
        input_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executa um processo completo pelo nome
        """
        state = {
            "input": input_payload,
            "results": {},
            "meta": {}
        }

        process_execution = ProcessExecution.objects.create(
            process=self.process,
            input_payload=input_payload,
            state=state,
            status="running"
        )

        current_task = self.process.entry_task

        try:
            while current_task:
                task_execution = TaskExecution.objects.create(
                    process_execution=process_execution,
                    task=current_task,
                    input_payload={}
                )

                # Executa task
                output = self._execute_task(current_task, state)

                task_execution.output_payload = output
                task_execution.status = "completed"
                task_execution.finished_at = timezone.now()
                task_execution.save()

                # Atualiza state
                state["results"][current_task.name] = output

                current_task = self._get_next_task(
                    self.process,
                    current_task,
                    state
                )

            process_execution.state = state
            process_execution.status = "completed"
            process_execution.finished_at = timezone.now()
            process_execution.save()

        except Exception as e:
            process_execution.status = "failed"
            process_execution.finished_at = timezone.now()
            process_execution.state = state
            process_execution.save()

            raise e

        return state

    # ---------- Métodos internos ----------

    def _get_process(self, process_name: str) -> Process:
        try:
            return Process.objects.get(
                name=process_name,
                is_active=True
            )
        except Process.DoesNotExist:
            raise RuntimeError(f"Process '{process_name}' não encontrado")

    def _get_next_task(self, process: Process, current_task: Task, state: dict):
        transitions = process.transitions.filter(
            from_task=current_task
        )

        for transition in transitions:
            if ConditionEvaluator.evaluate(
                transition.condition,
                state
            ):
                return transition.to_task

        return None

    def _execute_task(self, task: Task, state: dict) -> dict:
        """
        Executa uma Task:
        - resolve inputs a partir do state
        - executa o agent
        - retorna output estruturado
        """

        # Resolve inputs
        input_payload = MappingResolver.resolve(
            task.input_mapping,
            state
        )

        # Cria o runtime do agent
        agent_runtime = self.agent_factory.create(task.agent)

        # Executa o agent
        output = agent_runtime.run(input_payload)

        # Aplica output_mapping (se existir)
        if task.output_mapping:
            output = MappingResolver.apply_output_mapping(
                task.output_mapping,
                output,
                state
            )

        return output
