from dotenv import load_dotenv
from django.test import TestCase

from core.models import Agent, Task, TaskExecution
from core.services.task_executor import TaskExecutor


class ImprovedTaskExecutionTest(TestCase):
    """
    Testes com validação robusta de schema de output.
    """

    def setUp(self):
        load_dotenv()

        self.agent = Agent.objects.create(
            name="CopywriterAgent",
            role="Copywriter",
            system_prompt="Você escreve copies de marketing claras e objetivas.",
            llm_config={
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.3,
            }
        )

        self.task = Task.objects.create(
            name="generate_copy",
            agent=self.agent,
            input_mapping={
                "product": "input.product"
            },
            output_schema={
                "text": "string",
                "confidence": "number",
            }
        )

    def test_task_with_robust_schema_validation(self):
        """
        Valida estrutura, tipos e ranges do output.
        """
        executor = TaskExecutor(self.task.id)

        output = executor.execute(
            input_payload={"product": "Curso de Python para Iniciantes"}
        )

        self._assert_valid_schema(
            output,
            expected_schema={
                "text": str,
                "confidence": (int, float),
            }
        )

        self.assertGreater(
            len(output["text"]),
            0,
            "text não deve ser vazio"
        )
        self.assertGreaterEqual(
            output["confidence"],
            0.0,
            "confidence deve ser >= 0.0"
        )
        self.assertLessEqual(
            output["confidence"],
            1.0,
            "confidence deve ser <= 1.0"
        )

    def test_execution_record_schema_is_valid(self):
        """
        O output_payload salvo no TaskExecution também deve ser válido.
        """
        executor = TaskExecutor(self.task.id)
        executor.execute(
            input_payload={"product": "Curso de Python"}
        )

        execution = TaskExecution.objects.first()
        self.assertEqual(execution.status, "completed")
        self.assertIsNotNone(execution.output_payload)

        if "_error" in execution.output_payload:
            self.fail(
                f"TaskExecution output_payload contém erro de schema: "
                f"{execution.output_payload['_error']}"
            )

    def test_multiple_executions_are_independent(self):
        """
        Execuções consecutivas da mesma task devem ser independentes.
        """
        executor = TaskExecutor(self.task.id)

        output1 = executor.execute(
            input_payload={"product": "Produto A"}
        )
        output2 = executor.execute(
            input_payload={"product": "Produto B"}
        )

        self._assert_valid_schema(output1, {"text": str, "confidence": (int, float)})
        self._assert_valid_schema(output2, {"text": str, "confidence": (int, float)})

        self.assertEqual(TaskExecution.objects.count(), 2)

    def test_schema_with_array_field(self):
        """
        Valida que campos do tipo array são retornados corretamente.
        """
        task_with_array = Task.objects.create(
            name="requirements_task",
            agent=self.agent,
            input_mapping={"document": "input.document"},
            output_schema={
                "requirements": "array",
                "complexity": "number",
                "summary": "string",
            }
        )

        executor = TaskExecutor(task_with_array.id)

        output = executor.execute(
            input_payload={
                "document": "Sistema de gerenciamento de estoque com relatórios e integração ERP."
            }
        )

        self._assert_valid_schema(
            output,
            {
                "requirements": list,
                "complexity": (int, float),
                "summary": str,
            }
        )

    # ---------- Helpers ----------

    def _assert_valid_schema(self, output: dict, expected_schema: dict):
        """
        Valida presença e tipos de todos os campos do schema.
        """
        if "_error" in output:
            self.fail(self._format_schema_error(output))

        for field_name, expected_type in expected_schema.items():
            self.assertIn(
                field_name,
                output,
                f"Campo obrigatório ausente: '{field_name}'"
            )
            self.assertIsInstance(
                output[field_name],
                expected_type,
                f"Campo '{field_name}' tem tipo incorreto. "
                f"Esperado {expected_type}, recebido {type(output[field_name])}"
            )

    def _format_schema_error(self, output: dict) -> str:
        error_type = output["_error"]

        if error_type == "missing_required_fields":
            return (
                f"Campos obrigatórios ausentes: {output['missing_fields']}\n"
                f"Partial output: {output.get('partial_output')}"
            )
        if error_type == "type_mismatch":
            return (
                f"Tipos incorretos: {output['type_errors']}\n"
                f"Partial output: {output.get('partial_output')}"
            )
        if error_type == "invalid_json":
            return (
                f"JSON inválido: {output.get('json_error')}\n"
                f"Raw output: {output.get('raw_output', '')[:200]}"
            )
        return f"Erro desconhecido: {error_type}\nDetalhes: {output}"