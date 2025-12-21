import operator
from typing import Dict, Any, Callable

from langgraph.graph import StateGraph, END

from core.models import Task
from core.services.agent_factory import AgentFactory

OPERATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}

class GraphBuilder:
    def __init__(
        self,
        process,
        tasks_by_id: Dict[int, Task]
    ):
        self.process = process
        self.tasks_by_id = tasks_by_id
        self.agent_factory = AgentFactory()

    def build(self):
        graph = StateGraph(dict)

        # Criar nós de task
        for node_name, node_data in self.process.graph_definition["nodes"].items():
            task = self.tasks_by_id[node_data["task_id"]]
            graph.add_node(
                node_name,
                self._build_task_node(task)
            )

        # Edges diretas
        for source, target in self.process.graph_definition.get("edges", []):
            graph.add_edge(source, target)

        # Branching condicional
        for node_name, config in self.process.graph_definition.get("conditional_edges", {}).items():
            graph.add_conditional_edges(
                node_name,
                self._build_condition_fn(config),
                self._build_condition_routes(config)
            )

        # Entry point
        graph.set_entry_point(self._entry_node_name())

        return graph.compile()

    # ---------- Internos ----------

    def _entry_node_name(self) -> str:
        """
        Resolve o node name do entry_task
        """
        entry_task_id = self.process.entry_task_id

        for node_name, node in self.process.graph_definition["nodes"].items():
            if node["task_id"] == entry_task_id:
                return node_name

        raise RuntimeError("Entry task não encontrada no grafo")

    def _build_task_node(self, task: Task) -> Callable:
        """
        Cria a função executável do nó
        """

        agent = self.agent_factory.create(task.agent)

        def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
            # Construir input do agente
            agent_input = self._resolve_input_mapping(
                task.input_mapping,
                state
            )

            # Executar agente
            result = agent.run(agent_input)

            # Aplicar output mapping
            self._apply_output_mapping(
                task,
                result,
                state
            )

            return state

        return node_fn

    def _build_condition_fn(self, config):
        path = config["path"]
        rules = config["rules"]

        def condition_fn(state):
            value = self._get_by_path(state, path)

            for rule in rules:
                op_fn = OPERATORS[rule["operator"]]
                if op_fn(value, rule["value"]):
                    return rule["next"]

            raise RuntimeError(f"Nenhuma condição satisfeita para valor: {value}")

        return condition_fn

    def _build_condition_routes(self, config):
        return {
            rule["next"]: rule["next"]
            for rule in config["rules"]
        }

    # ---------- Mapping ----------

    def _resolve_input_mapping(
        self,
        mapping: Dict[str, str],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not mapping:
            return state.get("input", {})

        resolved = {}
        for key, path in mapping.items():
            resolved[key] = self._get_by_path(state, path)

        return resolved

    def _apply_output_mapping(
        self,
        task: Task,
        result: Dict[str, Any],
        state: Dict[str, Any]
    ):
        if "results" not in state:
            state["results"] = {}

        # Se não houver mapping, salva direto
        if not task.output_mapping:
            state["results"][task.name] = result
            return

        output = {}
        for key, path in task.output_mapping.items():
            output[key] = self._get_by_path(result, key)

        state["results"][task.name] = output

    # ---------- Utils ----------

    def _get_by_path(self, data: Dict[str, Any], path: str):
        """
        Exemplo: 'input.product' ou 'results.copy.text'
        """
        current = data
        for part in path.split("."):
            current = current.get(part)
            if current is None:
                return None
        return current

