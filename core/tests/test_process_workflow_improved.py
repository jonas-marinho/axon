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


class ImprovedProcessFlowTest(TestCase):
    """
    Testes melhorados com validação robusta de schema.
    """

    def setUp(self):
        load_dotenv()
        
        # ---------- Agent ----------
        self.agent = Agent.objects.create(
            name="CopywriterAgent",
            role="Copywriter",
            system_prompt="Você escreve copies de marketing claras e objetivas.",
            llm_config={
                "provider": "openai",
                "model": "gpt-4",  # Modelo maior = melhor adherência ao schema
                "temperature": 0.3,  # Baixa temperatura = mais determinístico
            },
            output_schema={
                "text": "string",
                "confidence": "number",
            },
        )

        # ---------- Tasks ----------
        self.generate_copy = Task.objects.create(
            name="generate_copy",
            agent=self.agent,
            input_mapping={
                "product": "input.product"
            },
            output_mapping={}
        )

        self.publish_copy = Task.objects.create(
            name="publish_copy",
            agent=self.agent,
            input_mapping={
                "text": "results.generate_copy.text"
            },
            output_mapping={}
        )

        self.revise_copy = Task.objects.create(
            name="revise_copy",
            agent=self.agent,
            input_mapping={
                "text": "results.generate_copy.text"
            },
            output_mapping={}
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

    def test_process_with_robust_schema_validation(self):
        """
        Teste com validação robusta de schema.
        """
        executor = ProcessExecutor("CopyProcess")

        input_payload = {
            "product": "Curso de Python para Iniciantes"
        }

        state = executor.execute(
            input_payload=input_payload
        )

        # ---------- Validação de State ----------
        self.assertIn("results", state)
        self.assertIn("generate_copy", state["results"])

        generate_output = state["results"]["generate_copy"]

        # ---------- Validação de Schema ----------
        # Se houver erro de schema, falha o teste com mensagem clara
        if "_error" in generate_output:
            error_type = generate_output["_error"]
            
            if error_type == "missing_required_fields":
                self.fail(
                    f"Agent output missing required fields: {generate_output['missing_fields']}. "
                    f"Partial output: {generate_output.get('partial_output')}"
                )
            elif error_type == "type_mismatch":
                self.fail(
                    f"Agent output has type errors: {generate_output['type_errors']}. "
                    f"Partial output: {generate_output.get('partial_output')}"
                )
            elif error_type == "invalid_json":
                self.fail(
                    f"Agent output is not valid JSON: {generate_output['error_detail']}. "
                    f"Raw output: {generate_output.get('raw_output')}"
                )
            else:
                self.fail(
                    f"Agent output has unknown error: {error_type}. "
                    f"Details: {generate_output}"
                )

        # Validação de presença de campos
        self.assertIn("text", generate_output, "Field 'text' missing from output")
        self.assertIn("confidence", generate_output, "Field 'confidence' missing from output")

        # Validação de tipos
        self.assertIsInstance(
            generate_output["text"], 
            str, 
            f"Field 'text' should be string, got {type(generate_output['text'])}"
        )
        self.assertIsInstance(
            generate_output["confidence"], 
            (int, float), 
            f"Field 'confidence' should be number, got {type(generate_output['confidence'])}"
        )

        # Validação de ranges (opcional)
        self.assertGreaterEqual(
            generate_output["confidence"], 
            0.0,
            "Confidence should be >= 0.0"
        )
        self.assertLessEqual(
            generate_output["confidence"], 
            1.0,
            "Confidence should be <= 1.0"
        )

        # Validação de conteúdo
        self.assertGreater(
            len(generate_output["text"]), 
            0, 
            "Text should not be empty"
        )

        # ---------- Validação de Branching ----------
        executed_tasks = state["results"].keys()

        self.assertTrue(
            "publish_copy" in executed_tasks or "revise_copy" in executed_tasks,
            f"Neither publish_copy nor revise_copy executed. Tasks executed: {list(executed_tasks)}"
        )

        # Validação de consistência com a transição
        if generate_output["confidence"] >= 0.8:
            self.assertIn(
                "publish_copy", 
                executed_tasks,
                f"Expected publish_copy for confidence={generate_output['confidence']}"
            )
        else:
            self.assertIn(
                "revise_copy", 
                executed_tasks,
                f"Expected revise_copy for confidence={generate_output['confidence']}"
            )

        # ---------- Validação de Execution Record ----------
        self.assertEqual(ProcessExecution.objects.count(), 1)

        execution = ProcessExecution.objects.first()
        self.assertEqual(execution.status, "completed")
        self.assertGreaterEqual(execution.task_executions.count(), 1)
        
        # Validação de task executions
        for task_exec in execution.task_executions.all():
            self.assertEqual(task_exec.status, "completed")
            self.assertIsNotNone(task_exec.output_payload)
            
            # Validação de schema em cada task
            if "_error" in task_exec.output_payload:
                self.fail(
                    f"Task {task_exec.task.name} failed schema validation: "
                    f"{task_exec.output_payload['_error']}"
                )

    def test_schema_validation_helper_method(self):
        """
        Teste usando método helper para validação de schema.
        """
        executor = ProcessExecutor("CopyProcess")

        state = executor.execute(
            input_payload={"product": "Curso de Python"}
        )

        generate_output = state["results"]["generate_copy"]
        
        # Usa método helper
        self._assert_valid_schema(
            generate_output,
            expected_schema={
                "text": str,
                "confidence": (int, float)
            }
        )

    # ---------- Helper Methods ----------

    def _assert_valid_schema(self, output: dict, expected_schema: dict):
        """
        Helper method para validar schema de forma reutilizável.
        
        Args:
            output: Dicionário de output do agent
            expected_schema: Dict com {campo: tipo_esperado}
        
        Exemplo:
            self._assert_valid_schema(
                output,
                {"text": str, "confidence": (int, float)}
            )
        """
        # Verificar se há erro de schema
        if "_error" in output:
            error_msg = self._format_schema_error(output)
            self.fail(error_msg)
        
        # Verificar presença de todos os campos
        for field_name, expected_type in expected_schema.items():
            self.assertIn(
                field_name,
                output,
                f"Missing required field: {field_name}"
            )
            
            # Verificar tipo
            actual_value = output[field_name]
            self.assertIsInstance(
                actual_value,
                expected_type,
                f"Field '{field_name}' has wrong type. "
                f"Expected {expected_type}, got {type(actual_value)}"
            )

    def _format_schema_error(self, output: dict) -> str:
        """
        Formata mensagem de erro de schema de forma legível.
        """
        error_type = output["_error"]
        
        if error_type == "missing_required_fields":
            return (
                f"Schema validation failed: Missing required fields\n"
                f"  Missing: {output['missing_fields']}\n"
                f"  Partial output: {output.get('partial_output')}\n"
                f"  Raw output: {output.get('raw_output')[:200]}..."
            )
        elif error_type == "type_mismatch":
            return (
                f"Schema validation failed: Type mismatch\n"
                f"  Errors: {output['type_errors']}\n"
                f"  Partial output: {output.get('partial_output')}\n"
                f"  Raw output: {output.get('raw_output')[:200]}..."
            )
        elif error_type == "invalid_json":
            return (
                f"Schema validation failed: Invalid JSON\n"
                f"  Error: {output.get('error_detail')}\n"
                f"  Raw output: {output.get('raw_output')[:200]}..."
            )
        else:
            return f"Schema validation failed: {error_type}\nDetails: {output}"

    def _print_execution_debug_info(self, state: dict):
        """
        Helper para debugging: imprime informações da execução.
        """
        print("\n" + "="*60)
        print("EXECUTION DEBUG INFO")
        print("="*60)
        
        print("\nInput:")
        print(f"  {state['input']}")
        
        print("\nResults:")
        for task_name, task_output in state["results"].items():
            print(f"\n  Task: {task_name}")
            
            if "_error" in task_output:
                print(f"    ❌ ERROR: {task_output['_error']}")
                if "missing_fields" in task_output:
                    print(f"    Missing: {task_output['missing_fields']}")
                if "type_errors" in task_output:
                    print(f"    Type errors: {task_output['type_errors']}")
            else:
                print(f"    ✅ Valid output")
                for key, value in task_output.items():
                    print(f"    {key}: {value} ({type(value).__name__})")
        
        print("\n" + "="*60 + "\n")
