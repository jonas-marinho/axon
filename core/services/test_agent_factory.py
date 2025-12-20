from agent_factory import AgentFactory

agent_definition = {
    "name": "Copywriter",
    "role": "Especialista em marketing",
    "system_prompt": "Crie um texto curto de marketing.",
    "output_schema": None,
}

agent = AgentFactory.from_dict(agent_definition)

result = agent.execute({
    "produto": "Curso de Python",
    "publico": "Iniciantes"
})

print(result)