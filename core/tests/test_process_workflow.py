import os

from dotenv import load_dotenv
from django.test import TestCase

from core.models import (
    Agent,
    Task,
    Process,
    ProcessTransition
)
from core.services.process_executor import ProcessExecutor
from core.models import ProcessExecution


class ProcessFlowIntegrationTest(TestCase):

    def setUp(self):
        load_dotenv()
        # ---------- Agent ----------
        self.agent = Agent.objects.create(
            name="CopywriterAgent",
            role="Copywriter",
            system_prompt="Você escreve copies de marketing claras e objetivas.",
            llm_config={
                "provider": "openai",
                "model": "gpt-5-nano",
                "temperature": 0.7,
            }
        )

        # ---------- Tasks ----------
        self.generate_copy = Task.objects.create(
            name="generate_copy",
            agent=self.agent,
            input_mapping={
                "product": "input.product"
            },
            output_mapping={},
            output_schema={
                "text": "string",
                "confidence": "number",
            }
        )

        self.publish_copy = Task.objects.create(
            name="publish_copy",
            agent=self.agent,
            input_mapping={
                "text": "results.generate_copy.text"
            },
            output_mapping={},
            output_schema={
                "text": "string",
                "confidence": "number",
            }
        )

        self.revise_copy = Task.objects.create(
            name="revise_copy",
            agent=self.agent,
            input_mapping={
                "text": "results.generate_copy.text"
            },
            output_mapping={},
            output_schema={
                "text": "string",
                "confidence": "number",
            }
        )

        # ---------- Process ----------
        self.process = Process.objects.create(
            name="CopyProcess",
            entry_task=self.generate_copy
        )

        # ---------- Transitions ----------
        ProcessTransition.objects.create(
            process=self.process,
            from_task=self.generate_copy,
            to_task=self.publish_copy,
            condition="results.generate_copy.confidence >= 0.8",
            order=1,
        )

        ProcessTransition.objects.create(
            process=self.process,
            from_task=self.generate_copy,
            to_task=self.revise_copy,
            condition="results.generate_copy.confidence < 0.8",
            order=2,
        )

    def test_process_executes_and_branches_correctly(self):
        executor = ProcessExecutor("CopyProcess")

        input_payload = {
            "product": "Curso de Python para Iniciantes"
        }

        state = executor.execute(
            input_payload=input_payload
        )

        # ---------- Assertions ----------
        self.assertIn("results", state)
        self.assertIn("generate_copy", state["results"])

        generate_output = state["results"]["generate_copy"]

        self.assertIn("text", generate_output)
        self.assertIn("confidence", generate_output)

        self.assertIsInstance(generate_output["confidence"], float)

        # Branching assertion (flexível e robusta)
        executed_tasks = state["results"].keys()

        self.assertTrue(
            "publish_copy" in executed_tasks
            or "revise_copy" in executed_tasks
        )

        self.assertEqual(ProcessExecution.objects.count(), 1)

        execution = ProcessExecution.objects.first()
        self.assertEqual(execution.status, "completed")
        self.assertGreaterEqual(execution.task_executions.count(), 1)
        return
