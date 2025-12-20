from pydantic import BaseModel, ValidationError
from typing import Any, Dict, Callable

# ---- Mock de chamada LLM (substituir depois) ----
def call_llm(prompt: str) -> Dict[str, Any]:
    # Simulação de resposta de um LLM
    return {
        "result": f"Resposta simulada para prompt: {prompt[:50]}..."
    }


class AgentRuntime:
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        output_schema: Dict | None = None,
        tools: Dict | None = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.output_schema = output_schema
        self.tools = tools or {}

    def build_prompt(self, input_data: Dict[str, Any]) -> str:
        return f"""Role: {self.role}

Instructions:
{self.system_prompt}

Input:
{input_data}
"""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.build_prompt(input_data)
        raw_output = call_llm(prompt)

        if self.output_schema:
            try:
                class OutputModel(BaseModel):
                    __root__: Dict[str, Any]

                validated = OutputModel.parse_obj(raw_output)
                return validated.__root__
            except ValidationError as e:
                raise RuntimeError(f"Output inválido: {e}")

        return raw_output


class AgentFactory:
    @staticmethod
    def from_dict(agent_def: Dict[str, Any]) -> AgentRuntime:
        return AgentRuntime(
            name=agent_def["name"],
            role=agent_def["role"],
            system_prompt=agent_def["system_prompt"],
            output_schema=agent_def.get("output_schema"),
            tools=agent_def.get("tools_config"),
        )