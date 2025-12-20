# Axon

Axon é um **engine de orquestração de agentes de IA** orientado a dados, cujo objetivo principal é permitir a **criação, edição e execução de agentes e processos sem alteração de código**.

Este README descreve os **conceitos fundamentais**, a **modelagem de dados**, a relação com **LangChain / LangGraph**, as **premissas arquiteturais** e um **guia prático de uso**.

---

## 🎯 Objetivo do Axon

> Permitir que agentes de IA sejam definidos, versionados, organizados e orquestrados **via banco de dados**, sendo executados por processos configuráveis e expostos via API.

O Axon **não é um chatbot** e **não é um wrapper de LLM**.

Ele é:
- Um **motor de execução de workflows de agentes**
- Data-driven (configuração > código)
- Plugável a qualquer LLM
- Preparado para escala, observabilidade e execução assíncrona

---

## 🧠 Conceitos Fundamentais

### Agent

Um **Agent** representa uma entidade inteligente responsável por executar uma tarefa específica.

Ele define:
- Um papel (`role`)
- Um prompt base (`system_prompt`)
- Um schema de saída opcional
- Configuração de ferramentas (futuro)

📌 **O Agent não executa nada sozinho**. Ele é apenas uma definição.

---

### Task

Uma **Task** é o elo entre um **Process** e um **Agent**.

Ela define:
- Qual agente será executado
- Como os dados entram no agente (`input_mapping`)
- Como o resultado volta para o estado global (`output_mapping`)

📌 A mesma Task pode ser reutilizada em múltiplos processos.

---

### Process

Um **Process** representa um **workflow orquestrado de Tasks**.

Ele contém:
- Um ponto de entrada (`entry_task`)
- Um grafo de execução (`graph_definition`)
- Versionamento e ativação

📌 O Process **não contém lógica de execução** — apenas configuração.

---

## 🔗 Relacionamento entre Models

```
Agent
  └── Task (N)

Task
  └── Agent (1)

Process
  └── entry_task → Task
  └── graph_definition → referencia Tasks por ID
```

O grafo é a fonte de verdade da orquestração.

---

## 🧩 Relação com LangChain e LangGraph

Axon **não reimplementa** LangChain — ele o **orquestra**.

### Onde LangChain entra

- Execução de agentes
- Prompt templates
- Integração com LLMs

### Onde LangGraph entra

- Execução de grafos
- Controle de fluxo
- Encadeamento e paralelismo

### Papel do Axon

| Camada | Responsabilidade |
|------|------------------|
| Axon Models | Definição e persistência |
| AgentFactory | Construção de agentes LangChain |
| GraphBuilder | Construção do grafo LangGraph |
| ProcessExecutor | Orquestração completa |

📌 Axon atua como **camada de domínio e runtime** sobre LangChain.

---

## 🧠 Premissas Arquiteturais

Estas premissas **não devem ser quebradas**:

1. **Models não executam lógica**
2. **Execução acontece apenas em services**
3. **Processos são data-driven**
4. **Estado é explícito e serializável**
5. **Versionamento é obrigatório**

Essas decisões permitem:
- Replay de execuções
- Auditoria
- Evolução sem breaking changes

---

## 🗂️ Estrutura do Projeto

```
axon/
├── core/
│   ├── models/
│   │   ├── agent.py
│   │   ├── task.py
│   │   └── process.py
│   └── services/
│       ├── agent_factory.py
│       ├── graph_builder.py
│       └── process_executor.py
```

---

## ▶️ Fluxo de Execução

1. API chama `ProcessExecutor.execute()`
2. Process é carregado do banco
3. Tasks são resolvidas
4. Grafo é construído
5. Agentes são executados
6. Resultado final é retornado

```
API → ProcessExecutor → GraphBuilder → AgentFactory → LLM
```

---

## 🧪 Exemplo Prático de Uso

### 1️⃣ Criar um Agent

```python
Agent.objects.create(
    name="Copywriter",
    role="Marketing Specialist",
    system_prompt="Crie textos persuasivos"
)
```

---

### 2️⃣ Criar uma Task

```python
Task.objects.create(
    name="generate_copy",
    agent=agent
)
```

---

### 3️⃣ Criar um Process

```python
Process.objects.create(
    name="marketing_process",
    entry_task=task,
    graph_definition={
        "nodes": {
            "start": {"task_id": task.id}
        },
        "edges": []
    }
)
```

---

### 4️⃣ Executar

```python
executor = ProcessExecutor()

result = executor.execute(
    process_name="marketing_process",
    input_payload={"product": "Curso de Python"}
)
```

---

## 🚀 O que o Axon já é

- Engine de agentes
- Orquestrador de workflows
- Configurável via banco
- Pronto para API
- Pronto para UI

---

## 🧭 Próximos Passos

- API REST
- Persistência de execuções
- Execução assíncrona
- Observabilidade
- UI de configuração

---

## 📌 Filosofia Final

> **Código define capacidades. Banco define comportamento.**

Axon existe para garantir que você **nunca precise alterar código para mudar o comportamento dos agentes**.

