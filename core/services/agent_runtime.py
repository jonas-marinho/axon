import json
import logging
from langchain_core.prompts import ChatPromptTemplate
from core.services.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


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
        logger.info(f"Inicializando AgentRuntime para '{name}'")
        logger.debug(f"Configurações - Role: '{role}', LLM Provider: '{llm_config.get('provider')}', Model: '{llm_config.get('model')}'")
        
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.output_schema = output_schema or {}
        self.tools_config = tools_config
        
        logger.debug(f"Output schema definido: {bool(output_schema)}")
        if output_schema:
            logger.debug(f"Schema fields: {list(output_schema.keys())}")
        
        logger.debug(f"Tools config definido: {bool(tools_config)}")
        
        # Cria instância do LLM
        try:
            logger.debug("Criando instância do LLM provider")
            self.llm = LLMProvider.create(llm_config)
            logger.info(f"LLM provider criado com sucesso para agent '{name}'")
        except Exception as e:
            logger.error(f"Erro ao criar LLM provider para agent '{name}': {str(e)}", exc_info=True)
            raise

    def run(self, input_payload: dict) -> dict:
        logger.info(f"--- Iniciando execução do agent '{self.name}' ---")
        logger.debug(f"Input payload recebido: {input_payload}")
        
        # Constrói mensagens
        logger.debug("Construindo mensagens para o LLM")
        try:
            messages = self._build_messages(input_payload)
            logger.debug(f"Total de mensagens construídas: {len(messages)}")
            for idx, msg in enumerate(messages, 1):
                logger.debug(f"Mensagem {idx}: Tipo={type(msg).__name__}, Conteúdo preview={str(msg)[:100]}...")
        except Exception as e:
            logger.error(f"Erro ao construir mensagens: {str(e)}", exc_info=True)
            raise

        # Invoca LLM
        logger.info(f"Invocando LLM para agent '{self.name}'")
        logger.debug(f"Modelo configurado: {self.llm.model_name if hasattr(self.llm, 'model_name') else 'N/A'}")
        
        
        logger.info(f"TEMP: {messages}")
        
        
        try:
            response = self.llm.invoke(messages)
            logger.info(f"LLM respondeu com sucesso para agent '{self.name}'")
            logger.debug(f"Tipo de resposta: {type(response).__name__}")
        except Exception as e:
            logger.error(f"Erro ao invocar LLM para agent '{self.name}': {str(e)}", exc_info=True)
            raise

        # Extrai conteúdo
        raw_content = response.content
        logger.debug(f"Conteúdo bruto recebido (primeiros 200 chars): {raw_content[:200]}...")
        logger.debug(f"Tamanho total do conteúdo: {len(raw_content)} caracteres")

        # Processa output
        if self.output_schema:
            logger.debug("Output schema definido - Parseando resposta estruturada")
            result = self._parse_structured_output(raw_content)
            
            if "_error" in result:
                logger.warning(f"Falha ao parsear JSON estruturado para agent '{self.name}'")
                logger.warning(f"Erro: {result['_error']}")
                logger.debug(f"Raw output que falhou no parse: {result.get('raw_output', '')[:500]}...")
            else:
                logger.info(f"JSON estruturado parseado com sucesso para agent '{self.name}'")
                logger.debug(f"Campos retornados: {list(result.keys())}")
            
            return result
        else:
            logger.debug("Nenhum output schema - Retornando texto puro")
            result = {"text": raw_content}
            logger.info(f"Agent '{self.name}' executado com sucesso - Retornando texto puro")
            return result

    def _build_messages(self, input_payload):
        logger.debug("Montando template de mensagens")
        
        messages = [
            ("system", "Atue como {role}. {system_prompt}"),
            ("human", "{input_payload}")
        ]
        logger.debug(f"Template base criado com {len(messages)} mensagens")
        
        if self.output_schema:
            logger.debug("Adicionando instrução de output schema")
            schema_instruction = self._output_schema_instruction()
            messages.append(("system", schema_instruction))
            logger.debug(f"Instrução de schema adicionada: {schema_instruction[:100]}...")
        
        logger.debug("Criando ChatPromptTemplate")
        prompt = ChatPromptTemplate.from_messages(messages)
        
        logger.debug("Formatando mensagens com valores reais")
        formatted_messages = prompt.format_messages(
            role=self.role,
            system_prompt=self.system_prompt,
            input_payload=str(input_payload)
        )
        
        logger.debug(f"Mensagens formatadas: {len(formatted_messages)} no total")
        return formatted_messages

    def _output_schema_instruction(self) -> str:
        logger.debug("Gerando instrução de output schema")
        logger.debug(f"Schema fields: {self.output_schema}")
        
        fields = '{{' + ", ".join(
            f'"{key}": {value}'
            for key, value in self.output_schema.items()
        ) + '}}'
        
        instruction = f"Responda EXCLUSIVAMENTE em JSON válido no seguinte formato: '{fields}'. Não inclua explicações, comentários ou texto fora do JSON."
        
        logger.debug(f"Instrução de schema gerada: {instruction}")
        return instruction

    def _parse_structured_output(self, content: str) -> dict:
        logger.debug("Tentando parsear conteúdo como JSON estruturado")
        logger.debug(f"Conteúdo a ser parseado (primeiros 300 chars): {content[:300]}...")
        
        try:
            # Tenta remover markdown code blocks se houver
            cleaned_content = content.strip()
            
            if cleaned_content.startswith("```"):
                logger.debug("Detectado markdown code block - Removendo")
                lines = cleaned_content.split('\n')
                cleaned_content = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned_content
                logger.debug(f"Conteúdo após remoção de markdown: {cleaned_content[:200]}...")
            
            parsed = json.loads(cleaned_content)
            logger.info("JSON parseado com sucesso")
            logger.debug(f"JSON parseado: {parsed}")
            
            # Valida campos esperados
            expected_fields = set(self.output_schema.keys())
            received_fields = set(parsed.keys())
            
            if expected_fields != received_fields:
                missing = expected_fields - received_fields
                extra = received_fields - expected_fields
                
                if missing:
                    logger.warning(f"Campos esperados ausentes no JSON: {missing}")
                if extra:
                    logger.warning(f"Campos extras recebidos no JSON: {extra}")
            else:
                logger.debug("Todos os campos esperados estão presentes no JSON")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {str(e)}")
            logger.error(f"Posição do erro: linha {e.lineno}, coluna {e.colno}")
            logger.error(f"Conteúdo completo que falhou: {content}")
            
            return {
                "_error": "invalid_json",
                "raw_output": content,
                "json_error": str(e)
            }
        except Exception as e:
            logger.error(f"Erro inesperado ao parsear JSON: {str(e)}", exc_info=True)
            return {
                "_error": "parse_error",
                "raw_output": content,
                "error_message": str(e)
            }