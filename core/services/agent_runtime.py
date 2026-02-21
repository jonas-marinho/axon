import json
import logging
from core.services.llm_provider import LLMProvider, Message

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
        """
        Executa o agente detectando automaticamente se há imagens.
        
        input_payload pode conter:
        - Texto puro: {"product": "Curso Python"}
        - Com imagens: {
            "text": "Analise esta imagem",
            "images": [{"data": "base64", "media_type": "image/jpeg"}]
          }
        - Base64 direto: {"image": "base64_string"}
        """
        logger.info(f"--- Iniciando execução do agent '{self.name}' ---")
        logger.debug(f"Input payload recebido: {input_payload}")
        
        # Constrói mensagens
        has_images = self._detect_images(input_payload)
        logger.debug("Construindo mensagens para o LLM")
        try:
            messages = self._build_messages(input_payload, has_images)
            logger.debug(f"Total de mensagens construídas: {len(messages)}")
            for idx, msg in enumerate(messages, 1):
                logger.debug(f"Mensagem {idx}: Tipo={type(msg).__name__}, Conteúdo preview={str(msg)[:100]}...")
        except Exception as e:
            logger.error(f"Erro ao construir mensagens: {str(e)}", exc_info=True)
            raise

        # Invoca LLM
        logger.info(f"Invocando LLM para agent '{self.name}'")
        logger.debug(f"Modelo configurado: {self.llm.model_name if hasattr(self.llm, 'model_name') else 'N/A'}")
        
        try:
            raw_content = self.llm.invoke(messages)
            logger.info(f"LLM respondeu com sucesso para agent '{self.name}'")
            logger.debug(f"Tipo de resposta: {type(raw_content).__name__}")
        except Exception as e:
            logger.error(f"Erro ao invocar LLM para agent '{self.name}': {str(e)}", exc_info=True)
            raise
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

    def _build_messages(self, input_payload: dict, has_images: bool) -> list[Message]:
        """
        Monta a lista de Message agnósticos que serão enviados ao provider.

        Estrutura:
        1. system  — persona + prompt do agente
        2. user    — conteúdo do input (texto e/ou imagens)
        3. system  — instrução de output schema (quando definido)
        """
        messages = []
        
        # 1. System: persona
        system_text = f"Atue como {self.role}. {self.system_prompt}"
        messages.append(Message(role=Message.SYSTEM, content=system_text))

        # 2. User: input (texto e/ou imagens)
        user_content = self._build_user_content(input_payload, has_images)
        messages.append(Message(role=Message.USER, content=user_content))

        # 3. System: instrução de schema (opcional)
        if self.output_schema:
            schema_instruction = self._output_schema_instruction()
            messages.append(Message(role=Message.SYSTEM, content=schema_instruction))

        logger.debug(f"{len(messages)} mensagens construídas para o LLM")
        return messages

    def _build_user_content(self, input_payload: dict, has_images: bool):
        """
        Retorna o conteúdo do usuário:
        - str  → se não houver imagens
        - list → se houver imagens (formato multimodal)
        """
        user_text = self._extract_text(input_payload)

        if not has_images:
            return user_text

        # Multimodal: texto primeiro, imagens depois
        content = []
        content.append({"type": "text", "text": user_text})
        for image in self._extract_images(input_payload):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image['media_type']};base64,{image['data']}"
                },
            })
        return content

    def _output_schema_instruction(self) -> str:
        """
        Gera instruções muito explícitas e assertivas para garantir
        que o LLM siga o schema definido.
        """
        logger.debug("Gerando instrução de output schema")
        logger.debug(f"Schema fields: {self.output_schema}")

        # Cria exemplo de estrutura esperada com tipos
        fields_description = []
        example_values = {
            "string": '"exemplo de texto"',
            "number": '0.85',
            "array": '["item1", "item2"]',
            "boolean": 'true',
            "object": '{"key": "value"}'
        }
        
        for key, value_type in self.output_schema.items():
            example = example_values.get(value_type, '"valor"')
            fields_description.append(f'  "{key}": {example}')
        
        fields_example = "{\n" + ",\n".join(fields_description) + "\n}"
        
        instruction = f"""CRITICAL: Your response MUST be ONLY valid JSON in this EXACT format:

{fields_example}

REQUIREMENTS:
- Include ALL fields: {', '.join(self.output_schema.keys())}
- Use correct types: {', '.join(f'{k}={v}' for k, v in self.output_schema.items())}
- NO explanations, NO markdown, NO text outside JSON
- Start with {{ and end with }}
- Ensure valid JSON syntax

If you include ANY text outside the JSON structure, the system will fail."""
        
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
            
            cleaned_content = cleaned_content.strip()
            parsed = json.loads(cleaned_content)
            logger.info("JSON parseado com sucesso")
            logger.debug(f"JSON parseado: {parsed}")
            
            # Validação: todas as chaves do schema devem estar presentes
            missing_keys = set(self.output_schema.keys()) - set(parsed.keys())
            if missing_keys:
                return {
                    "_error": "missing_required_fields",
                    "missing_fields": list(missing_keys),
                    "partial_output": parsed,
                    "raw_output": content
                }
            
            # Validação: tipos básicos
            type_errors = []
            for key, expected_type in self.output_schema.items():
                actual_value = parsed.get(key)
                
                if expected_type == "number" and not isinstance(actual_value, (int, float)):
                    type_errors.append(f"{key} should be number, got {type(actual_value).__name__}")
                elif expected_type == "string" and not isinstance(actual_value, str):
                    type_errors.append(f"{key} should be string, got {type(actual_value).__name__}")
                elif expected_type == "array" and not isinstance(actual_value, list):
                    type_errors.append(f"{key} should be array, got {type(actual_value).__name__}")
                elif expected_type == "boolean" and not isinstance(actual_value, bool):
                    type_errors.append(f"{key} should be boolean, got {type(actual_value).__name__}")
            
            if type_errors:
                return {
                    "_error": "type_mismatch",
                    "type_errors": type_errors,
                    "partial_output": parsed,
                    "raw_output": content
                }
            
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
    
    def _detect_images(self, payload: dict) -> bool:
        """
        Detecta se o payload contém imagens em qualquer formato.
        """
        # Formato estruturado: {"images": [...]}
        if "images" in payload and payload["images"]:
            return True
        
        # Formato direto: {"image": "base64..."}
        if "image" in payload and isinstance(payload["image"], str):
            # Verifica se parece com base64 (string longa sem espaços)
            if len(payload["image"]) > 100 and " " not in payload["image"]:
                return True
        
        return False

    def _extract_text(self, payload: dict) -> str:
        """
        Extrai o texto do payload, ignorando as imagens.
        """
        text_parts = []
        
        for key, value in payload.items():
            if key in ["images", "image"]:
                continue
            
            if isinstance(value, str):
                text_parts.append(f"{key}: {value}")
            else:
                text_parts.append(f"{key}: {str(value)}")
        
        return "\n".join(text_parts) if text_parts else "Analise o conteúdo fornecido"
        
    def _extract_images(self, payload: dict) -> list:
        """
        Extrai imagens do payload em qualquer formato.
        """
        images = []
        
        # Formato estruturado: {"images": [...]}
        if "images" in payload and isinstance(payload["images"], list):
            images.extend(payload["images"])
        
        # Formato direto: {"image": "base64"}
        elif "image" in payload and isinstance(payload["image"], str):
            images.append({
                "data": payload["image"],
                "media_type": "image/jpeg"  # Assume JPEG por padrão
            })
        
        return images