from typing import Any, Dict, Union
from pydantic import BaseModel, ValidationError

from core.services.llm_provider import LLMProvider, MockLLMProvider


class AgentRuntime:
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        output_schema: Dict | None = None,
        tools: Dict | None = None,
        llm: LLMProvider | None = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.output_schema = output_schema
        self.tools = tools or {}
        self.llm = llm or MockLLMProvider()

    def build_prompt(self, input_data: Dict[str, Any]) -> str:
        return f"""
Role:
{self.role}

Instructions:
{self.system_prompt}

Input:
{input_data}
"""

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.build_prompt(input_data)
        raw_output = self.llm.call(prompt)

        if self.output_schema:
            try:
                class OutputModel(BaseModel):
                    __root__: Dict[str, Any]

                validated = OutputModel.parse_obj(raw_output)
                return validated.__root__
            except ValidationError as e:
                raise RuntimeError(f"Invalid output schema: {e}")

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

    @staticmethod
    def from_model(agent) -> AgentRuntime:
        return AgentRuntime(
            name=agent.name,
            role=agent.role,
            system_prompt=agent.system_prompt,
            output_schema=agent.output_schema,
            tools=agent.tools_config,
        )
