from core.services.agent_runtime import AgentRuntime


class AgentFactory:
    """
    Responsável por criar instâncias executáveis de agentes
    a partir de modelos persistidos no banco.
    """

    def create(self, agent_model, output_schema=None):
        """
        Recebe um Agent (Django model) e retorna um AgentRuntime
        """

        return AgentRuntime(
            name=agent_model.name,
            role=agent_model.role,
            system_prompt=agent_model.system_prompt,
            llm_config=agent_model.llm_config,
            output_schema=output_schema,
            tools_config=agent_model.tools_config,
        )

