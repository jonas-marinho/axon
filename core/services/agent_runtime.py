import json
from langchain_core.prompts import ChatPromptTemplate
from core.services.llm_provider import LLMProvider

class AgentRuntime:
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        llm_config: dict,
        output_schema=None,
        tools_config=None
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = LLMProvider.create(llm_config)
        self.output_schema = output_schema or {}
        self.tools_config = tools_config


    def run(self, input_payload: dict) -> dict:
        messages = self._build_messages(input_payload)
        response = self.llm.invoke(messages)

        raw_content = response.content

        if self.output_schema:
            return self._parse_structured_output(raw_content)

        return {"text": raw_content}

    def _build_messages(self, input_payload):
        messages = [
            ("system", "Atue como {role}. {system_prompt}"),
            ("human", "{input_payload}")
        ] # O que está marcado com { } será substituído na promp.format_messages, de acordo com os parâmetros passados
        if self.output_schema:
            messages.append(
                ("system", self._output_schema_instruction())
            )
        prompt = ChatPromptTemplate.from_messages(messages)
        return prompt.format_messages(
            role=self.role,
            system_prompt=self.system_prompt,
            input_payload=str(input_payload)
        )

    def _output_schema_instruction(self) -> str:
        fields = '{{' + ", ".join(
            f'"{key}": {value}'
            for key, value in self.output_schema.items()
        ) + '}}'

        return f"Responda EXCLUSIVAMENTE em JSON válido no seguinte formato: '{fields}'. Não inclua explicações, comentários ou texto fora do JSON."

    def _parse_structured_output(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "_error": "invalid_json",
                "raw_output": content
            }
