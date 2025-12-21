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
        tools_config=None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = LLMProvider.create(llm_config)
        self.output_schema = output_schema
        self.tools_config = tools_config


    def run(self, input_payload: dict) -> dict:
        messages = self._build_messages(input_payload)

        response = self.llm.invoke(messages)

        return {
            "text": response.content
        }

    def _build_messages(self, input_payload):
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are {role}. {system_prompt}"),
            ("human", "{input_payload}")
        ])
        return prompt.format_messages(
            role=self.role,
            system_prompt=self.system_prompt,
            input_payload=str(input_payload)
        )

