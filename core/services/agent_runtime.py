class AgentRuntime:
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        output_schema=None,
        tools_config=None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.output_schema = output_schema
        self.tools_config = tools_config

    def run(self, input_payload: dict) -> dict:
        """
        Executa o agente.
        Neste momento pode ser mock ou LLM real.
        """

        # MOCK TEMPORÁRIO (para o teste passar)
        return {
            "text": f"[{self.name}] Gerando conteúdo para: {input_payload}"
        }

