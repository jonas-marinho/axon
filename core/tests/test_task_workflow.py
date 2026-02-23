from dotenv import load_dotenv
from django.test import TestCase

from core.models import Agent, Task, TaskExecution
from core.services.task_executor import TaskExecutor


class TaskExecutionTest(TestCase):

    def setUp(self):
        load_dotenv()

        self.agent = Agent.objects.create(
            name="CopywriterAgent",
            role="Copywriter",
            system_prompt="Você escreve copies de marketing claras e objetivas.",
            llm_config={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
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

    def test_task_executes_and_returns_output(self):
        executor = TaskExecutor(self.task.id)

        output = executor.execute(
            input_payload={"product": "Curso de Python para Iniciantes"}
        )

        self.assertIn("text", output)
        self.assertIn("confidence", output)

        self.assertIsInstance(output["text"], str)
        self.assertIsInstance(output["confidence"], float)

    def test_task_execution_record_is_created(self):
        executor = TaskExecutor(self.task.id)

        executor.execute(
            input_payload={"product": "Curso de Python para Iniciantes"}
        )

        self.assertEqual(TaskExecution.objects.count(), 1)

        execution = TaskExecution.objects.first()
        self.assertEqual(execution.status, "completed")
        self.assertEqual(execution.task, self.task)
        self.assertIsNotNone(execution.output_payload)
        self.assertIsNotNone(execution.finished_at)

    def test_task_execution_fails_gracefully(self):
        """
        Execução com agent inválido deve marcar TaskExecution como failed
        e relançar a exceção.
        """
        self.agent.llm_config = {"provider": "openai", "model": "modelo-inexistente"}
        self.agent.save()

        executor = TaskExecutor(self.task.id)

        with self.assertRaises(Exception):
            executor.execute(
                input_payload={"product": "Qualquer produto"}
            )

        execution = TaskExecution.objects.first()
        self.assertIsNotNone(execution)
        self.assertEqual(execution.status, "failed")
        self.assertIsNotNone(execution.error)

    def test_task_without_input_mapping_passes_payload_directly(self):
        """
        Task sem input_mapping deve repassar o payload diretamente ao agent.
        """
        task_no_mapping = Task.objects.create(
            name="free_task",
            agent=self.agent,
            input_mapping=None,
            output_schema={
                "text": "string",
                "confidence": "number",
            }
        )

        executor = TaskExecutor(task_no_mapping.id)

        output = executor.execute(
            input_payload={"product": "Notebook Gamer"}
        )

        self.assertIn("text", output)
        self.assertIn("confidence", output)