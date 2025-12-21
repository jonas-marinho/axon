import operator

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

        tokens = condition.split()

        if len(tokens) != 3:
            raise ValueError(f"Condição inválida: {condition}")

        left, op, right = tokens

        left_value = cls._resolve_path(left, state)
        right_value = cls._cast_value(right)

        if op not in cls.OPERATORS:
            raise ValueError(f"Operador não suportado: {op}")

        return cls.OPERATORS[op](left_value, right_value)

    @staticmethod
    def _resolve_path(path: str, state: dict):
        current = state
        for part in path.split("."):
            current = current.get(part)
            if current is None:
                return None
        return current

    @staticmethod
    def _cast_value(value: str):
        if value.replace(".", "", 1).isdigit():
            return float(value)
        return value.strip('"').strip("'")

