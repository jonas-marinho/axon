# Axon

**Axon** é um motor de execução de agentes de IA orientado a dados, projetado para permitir a criação, edição e execução de agentes **sem alteração de código**.

## 🎯 O que é o Axon?

Imagine que você precisa que um agente de IA:
1. Receba um documento de requisitos de um cliente
2. Extraia as informações principais e avalie a complexidade
3. Retorne um output estruturado e rastreável

Com Axon, você **define esse agente inteiro no banco de dados** — incluindo o modelo de LLM, o prompt, o schema de saída e as permissões de acesso. Nenhuma linha de código precisa ser modificada para criar ou alterar esse comportamento.

## 🧩 Como funciona?

### Arquitetura Conceitual

O Axon organiza a execução de agentes em 3 camadas principais:

```
Tasks  →  Agents  →  LLM Provider
```

### Componentes Principais

#### 1. **Agent** — A Definição da Inteligência

Um Agent configura **como** um agente de IA deve se comportar:

```python
Agent.objects.create(
    name="RequirementsAnalyzer",
    role="Technical Analyst",
    system_prompt="Você é um analista técnico especializado em extrair e avaliar requisitos de projetos de software.",
    llm_config={
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.3
    }
)
```

> Um Agent é apenas uma definição — ele não executa nada sozinho.

#### 2. **Task** — A Unidade de Execução

Uma Task conecta um Agent a um contexto de execução específico, definindo como os dados entram e saem:

```python
Task.objects.create(
    name="analyze_requirements",
    agent=requirements_analyzer,
    input_mapping={
        "document": "input.document"  # Resolve a partir do payload recebido
    },
    output_schema={
        "requirements": "array",
        "complexity": "number",
        "summary": "string"
    }
)
```

**Mapeamento de Dados:**
- `input_mapping`: Define como o payload recebido é passado ao agent. O caminho `"input.document"` resolve o campo `document` do payload de entrada.
- `output_schema`: Define e valida o formato estruturado de saída do agent. Se `None`, retorna texto puro.

#### 3. **TaskPermission** — Controle de Acesso

Cada Task tem uma permissão associada, criada automaticamente ao criar a Task:

```python
task.permission.access_type = 'restricted'  # Padrão
task.permission.allowed_users.add(user)
task.permission.save()
```

| Tipo | Quem pode acessar |
|------|-------------------|
| `restricted` | Apenas users/groups listados explicitamente (e superusers) |
| `public` | Qualquer usuário autenticado |
| `open` | Todos, incluindo não autenticados |

### Fluxo de Execução

```python
executor = TaskExecutor(task_id=1)
output = executor.execute(
    input_payload={
        "document": "Cliente precisa de um sistema de gerenciamento de estoque..."
    }
)
```

Internamente, o Axon:

1. **Carrega a Task** do banco de dados
2. **Resolve o `input_mapping`** para construir o input do agent
3. **Executa o Agent** através do LLM configurado
4. **Valida o output** contra o `output_schema`
5. **Persiste o `TaskExecution`** com input, output, status e timestamps

### Output Estruturado

Quando `output_schema` está definido, o Axon instrui o LLM a responder em JSON e valida a resposta:

```json
{
  "requirements": ["Controle de estoque", "Relatórios em tempo real"],
  "complexity": 4,
  "summary": "Sistema de média complexidade"
}
```

Se o LLM não seguir o schema, o output retorna com um campo `_error` descrevendo o problema (`missing_required_fields`, `type_mismatch`, `invalid_json`).

### Rastreabilidade

Toda execução é persistida automaticamente:

```python
TaskExecution
  ├── task
  ├── input_payload
  ├── output_payload
  ├── status          # running | completed | failed
  ├── error           # preenchido apenas em caso de falha
  ├── started_at
  └── finished_at
```

## 🔧 Suporte a Visão (Multimodal)

Tasks com agents de modelos multimodais (ex: `gpt-4o`) suportam imagens automaticamente.

**Formato estruturado:**
```json
{
  "text": "Descreva esta imagem",
  "images": [
    {"data": "<base64>", "media_type": "image/png"}
  ]
}
```

**Formato simples:**
```json
{
  "text": "Descreva esta imagem",
  "image": "<base64>"
}
```

Tasks com modelos sem suporte a visão ignoram os campos de imagem graciosamente.

## 🚀 API REST

**Autenticação (JWT):**
```bash
POST /api/v1/auth/token/
POST /api/v1/auth/token/refresh/
POST /api/v1/auth/token/verify/
```

**Tasks:**
```bash
GET  /api/v1/tasks/
POST /api/v1/tasks/{task_id}/execute/
GET  /api/v1/tasks/{task_id}/executions/
```

**Execuções:**
```bash
GET  /api/v1/executions/{execution_id}/
```

**Exemplo de execução:**
```bash
POST /api/v1/tasks/1/execute/
Authorization: Bearer <token>

{
  "document": "Cliente precisa de um sistema de gerenciamento de estoque..."
}
```

## 🛠️ Tecnologias

- **Django 6.0** — Framework web e ORM
- **Django REST Framework** — API REST
- **Simple JWT** — Autenticação
- **OpenAI / Anthropic / Grok / Gemini** — Providers de LLM
- **MySQL** — Persistência

## 💡 Providers de LLM Suportados

| Provider | Chave no `.env` |
|----------|-----------------|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Grok (xAI) | `XAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` |

Configuração via `llm_config` no Agent:
```python
llm_config = {
    "provider": "anthropic",
    "model": "claude-opus-4-6",
    "temperature": 0.7,
    "max_tokens": 1024
}
```

## 🗂️ Estrutura do Projeto

```
axon/
├── core/
│   ├── models/
│   │   ├── agent.py
│   │   ├── task.py
│   │   ├── task_execution.py
│   │   └── task_permission.py
│   │
│   ├── services/
│   │   ├── agent_factory.py
│   │   ├── agent_runtime.py
│   │   ├── task_executor.py
│   │   └── llm_provider.py
│   │
│   └── api/
│       ├── views.py
│       ├── serializers.py
│       ├── permissions.py
│       └── urls.py
│
├── settings.py
├── urls.py
└── manage.py
```

## 📦 Instalação

```bash
# Clone o repositório
git clone [url-do-repo]

# Configure o ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Instale dependências
pip install -r requirements.txt

# Execute migrações
python manage.py migrate

# Inicie o servidor
python manage.py runserver
```

## 🧪 Testes

```bash
# Permissões
python manage.py test core.tests.test_permissions

# Execução de tasks
python manage.py test core.tests.test_task_workflow

# Validação robusta de schema
python manage.py test core.tests.test_task_workflow_improved

# Suporte a visão
python manage.py test core.tests.test_vision_support
```

> Os testes de execução e visão realizam chamadas reais à API do LLM. Certifique-se de que a variável de ambiente correspondente está configurada no `.env`.

## 🎯 Casos de Uso

- **Análise de documentos** — extração de requisitos, resumos, classificações
- **Geração de conteúdo** — copies, descrições, e-mails
- **Análise de imagens** — descrição visual, extração de dados, comparações
- **Processamento de dados** — classificação, enriquecimento, validação

## 💡 Princípios de Design

**Data-Driven** — Comportamento é configuração, não código.

**Separation of Concerns** — Models definem e persistem; Services executam; API expõe.

**Estado Explícito** — Toda execução é rastreável e auditável.

**Composição** — Agents são reutilizáveis em múltiplas Tasks.

## 🔮 Roadmap

- [ ] Execução assíncrona (Celery)
- [ ] Orquestração de workflows multi-task
- [ ] Interface web para configuração visual
- [ ] Observabilidade avançada (traces, métricas)
- [ ] Sistema de plugins para ferramentas customizadas
- [ ] Templates de tasks comuns

## 📄 Licença

Este projeto está licenciado sob a **MIT License** — veja o arquivo [license.txt](./license.txt) para mais detalhes.

---

**Axon** — Execução de agentes de IA orientada a dados.