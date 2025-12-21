class MappingResolver:

    @staticmethod
    def resolve(mapping: dict, state: dict) -> dict:
        """
        Ex:
        mapping = {
            "product": "input.product"
        }
        """
        resolved = {}

        for key, path in mapping.items():
            resolved[key] = MappingResolver._get_by_path(
                state,
                path
            )

        return resolved

    @staticmethod
    def apply_output_mapping(mapping: dict, output: dict, state: dict):
        """
        Ex:
        mapping = {
            "final_text": "text"
        }
        """
        mapped = {}

        for target_key, source_key in mapping.items():
            mapped[target_key] = output.get(source_key)

        return mapped

    @staticmethod
    def _get_by_path(data: dict, path: str):
        current = data
        for part in path.split("."):
            if current is None:
                return None
            current = current.get(part)
        return current

