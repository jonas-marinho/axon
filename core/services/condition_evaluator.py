import logging
import operator

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le
    }

    @classmethod
    def evaluate(cls, condition: str, state: dict) -> bool:
        """
        Exemplo:
        'results.generate_copy.confidence >= 0.8'
        """
        logger.debug(f"Iniciando avaliação da condição: '{condition}'")
        logger.debug(f"Estado disponível para avaliação: {list(state.keys())}")

        # Parse da condição
        tokens = condition.split()
        logger.debug(f"Tokens extraídos da condição: {tokens}")

        if len(tokens) != 3:
            logger.error(f"Condição inválida - Esperado 3 tokens, recebido {len(tokens)}: '{condition}'")
            raise ValueError(f"Condição inválida: {condition}")

        left, op, right = tokens
        logger.debug(f"Parseado - Left: '{left}', Operator: '{op}', Right: '{right}'")

        # Resolve valor à esquerda (path no state)
        logger.debug(f"Resolvendo path à esquerda: '{left}'")
        left_value = cls._resolve_path(left, state)
        logger.debug(f"Valor resolvido à esquerda: {left_value} (tipo: {type(left_value).__name__})")

        # Resolve valor à direita (literal)
        logger.debug(f"Convertendo valor literal à direita: '{right}'")
        right_value = cls._cast_value(right)
        logger.debug(f"Valor convertido à direita: {right_value} (tipo: {type(right_value).__name__})")

        # Valida operador
        if op not in cls.OPERATORS:
            logger.error(f"Operador não suportado: '{op}'. Operadores válidos: {list(cls.OPERATORS.keys())}")
            raise ValueError(f"Operador não suportado: {op}")

        # Executa comparação
        operator_fn = cls.OPERATORS[op]
        logger.debug(f"Executando comparação: {left_value} {op} {right_value}")
        
        try:
            result = operator_fn(left_value, right_value)
            logger.info(f"Condição avaliada: '{condition}' = {result}")
            return result
        except Exception as e:
            logger.error(
                f"Erro ao executar operação '{op}' entre {left_value} e {right_value}: {str(e)}",
                exc_info=True
            )
            raise

    @staticmethod
    def _resolve_path(path: str, state: dict):
        """
        Resolve um caminho no formato 'results.task_name.field'
        """
        logger.debug(f"Resolvendo path: '{path}'")
        parts = path.split(".")
        logger.debug(f"Path dividido em {len(parts)} partes: {parts}")
        
        current = state
        for idx, part in enumerate(parts):
            logger.debug(f"Navegando parte {idx + 1}/{len(parts)}: '{part}'")
            
            if current is None:
                logger.warning(f"Valor None encontrado antes de completar o path na parte '{part}'")
                return None
            
            if not isinstance(current, dict):
                logger.error(f"Tentando acessar '{part}' em um valor não-dict: {type(current).__name__}")
                return None
            
            if part not in current:
                logger.warning(f"Chave '{part}' não encontrada no dicionário. Chaves disponíveis: {list(current.keys())}")
                return None
            
            current = current.get(part)
            logger.debug(f"Valor atual após navegar '{part}': {current}")
        
        logger.debug(f"Path '{path}' resolvido com sucesso para: {current}")
        return current

    @staticmethod
    def _cast_value(value: str):
        """
        Converte string para o tipo apropriado (float ou string)
        """
        logger.debug(f"Tentando converter valor: '{value}'")
        
        # Tenta converter para número
        if value.replace(".", "", 1).lstrip("-").isdigit():
            converted = float(value)
            logger.debug(f"Valor convertido para float: {converted}")
            return converted
        
        # Remove aspas se houver
        stripped = value.strip('"').strip("'")
        
        if stripped != value:
            logger.debug(f"Aspas removidas: '{value}' -> '{stripped}'")
        else:
            logger.debug(f"Mantido como string: '{stripped}'")
        
        return stripped