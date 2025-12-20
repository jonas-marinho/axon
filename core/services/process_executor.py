from typing import Dict, Any

from core.models import Process, Task
from core.services.graph_builder import GraphBuilder


class ProcessExecutor:
    def __init__(self):
        pass

    def execute(
        self,
        process_name: str,
        input_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executa um processo completo pelo nome.
        """

        # Buscar processo ativo
        process = self._get_process(process_name)

        # Buscar tasks envolvidas
        tasks_by_id = self._get_tasks(process)

        # Construir grafo
        graph = GraphBuilder(
            process=process,
            tasks_by_id=tasks_by_id
        ).build()

        # Estado inicial
        initial_state = {
            "input": input_payload,
            "results": {},
            "meta": {}
        }

        # Executar grafo
        final_state = graph.invoke(initial_state)

        # Retornar output final
        return self._build_response(final_state)

    # ---------- Métodos internos ----------

    def _get_process(self, process_name: str) -> Process:
        try:
            return Process.objects.get(
                name=process_name,
                is_active=True
            )
        except Process.DoesNotExist:
            raise RuntimeError(f"Process '{process_name}' não encontrado")

    def _get_tasks(self, process: Process) -> Dict[int, Task]:
        """
        Extrai os task_ids do graph_definition
        e carrega tudo em um único query.
        """
        task_ids = {
            node["task_id"]
            for node in process.graph_definition["nodes"].values()
        }

        tasks = Task.objects.select_related("agent").filter(
            id__in=task_ids
        )

        return {task.id: task for task in tasks}

    def _build_response(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Por enquanto, retorna todos os resultados.
        No futuro:
        - filtrar output
        - aplicar schema final
        """
        return {
            "results": final_state.get("results", {}),
            "meta": final_state.get("meta", {})
        }

