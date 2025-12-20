from typing import Dict, Any
from langgraph.graph import StateGraph, END

from core.services.agent_factory import AgentFactory


class GraphBuilder:
    def __init__(self, process, tasks_by_id: Dict[int, Any]):
        """
        process: Django Process model
        tasks_by_id: dict { task_id: Task model }
        """
        self.process = process
        self.tasks_by_id = tasks_by_id

    def build(self):
        graph = StateGraph(dict)

        graph_def = self.process.graph_definition

        # Criar nós
        for node_name, node_data in graph_def["nodes"].items():
            task_id = node_data["task_id"]
            task = self.tasks_by_id[task_id]

            graph.add_node(
                node_name,
                self._build_task_callable(task)
            )

        # Definir entrada
        graph.set_entry_point(self._entry_node_name())

        # Conectar edges
        for edge in graph_def["edges"]:
            graph.add_edge(edge["from"], edge["to"])

        # Finalização
        last_nodes = self._find_terminal_nodes(graph_def)
        for node in last_nodes:
            graph.add_edge(node, END)

        return graph.compile()

    def _build_task_callable(self, task):
        agent_runtime = AgentFactory.from_model(task.agent)

        def task_fn(state: Dict[str, Any]) -> Dict[str, Any]:
            input_data = {
                **state.get("input", {}),
                **state.get("results", {})
            }

            result = agent_runtime.execute(input_data)

            state["results"][task.name] = result
            return state

        return task_fn

    def _entry_node_name(self) -> str:
        return self.process.graph_definition.get("entry")

    def _find_terminal_nodes(self, graph_def: Dict[str, Any]):
        from_nodes = {e["from"] for e in graph_def["edges"]}
        to_nodes = {e["to"] for e in graph_def["edges"]}
        return list(from_nodes - to_nodes)

