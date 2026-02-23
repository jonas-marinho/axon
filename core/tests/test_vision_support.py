import base64
from dotenv import load_dotenv
from django.test import TestCase

from core.models import Agent, Task, TaskExecution
from core.services.task_executor import TaskExecutor


# Imagem de teste: 1x1 pixel PNG vermelho
TEST_IMAGE_BASE64 = base64.b64encode(base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)).decode('utf-8')


class VisionSupportTest(TestCase):
    """
    Testes para verificar o suporte a análise de imagens via TaskExecutor.
    """

    def setUp(self):
        load_dotenv()

        self.vision_agent = Agent.objects.create(
            name="ImageAnalyzer",
            role="Visual Analyst",
            system_prompt="Analise imagens e descreva o que vê.",
            llm_config={
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.3,
            }
        )

        self.text_agent = Agent.objects.create(
            name="TextAnalyzer",
            role="Text Analyst",
            system_prompt="Analise textos.",
            llm_config={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
            }
        )

        self.vision_task = Task.objects.create(
            name="analyze_image",
            agent=self.vision_agent,
            input_mapping={
                "text": "input.text",
                "images": "input.images",
            },
            output_schema={
                "description": "string",
                "elements": "array",
                "confidence": "number",
            }
        )

        self.text_task = Task.objects.create(
            name="analyze_text",
            agent=self.text_agent,
            input_mapping={
                "text": "input.text",
            },
            output_schema=None
        )

    # ---------- Testes de detecção (sem chamada de API) ----------

    def test_image_detection_structured_format(self):
        """
        Detecta imagens no formato estruturado {"images": [...]}.
        """
        from core.services.agent_factory import AgentFactory

        runtime = AgentFactory().create(self.vision_agent)

        self.assertTrue(runtime._detect_images({
            "text": "Analise",
            "images": [{"data": "abc123", "media_type": "image/png"}]
        }))

        self.assertFalse(runtime._detect_images({
            "text": "Apenas texto"
        }))

    def test_image_detection_simple_format(self):
        """
        Detecta imagens no formato simples {"image": "base64..."}.
        String longa (> 100 chars) é tratada como base64.
        """
        from core.services.agent_factory import AgentFactory

        runtime = AgentFactory().create(self.vision_agent)

        self.assertTrue(runtime._detect_images({
            "text": "Analise",
            "image": "a" * 200
        }))

        self.assertFalse(runtime._detect_images({
            "text": "Analise",
            "image": "curta"
        }))

    def test_image_extraction_structured_format(self):
        """
        Extrai corretamente múltiplas imagens do formato estruturado.
        """
        from core.services.agent_factory import AgentFactory

        runtime = AgentFactory().create(self.vision_agent)

        payload = {
            "text": "Teste",
            "images": [
                {"data": "abc", "media_type": "image/png"},
                {"data": "def", "media_type": "image/jpeg"},
            ]
        }

        images = runtime._extract_images(payload)

        self.assertEqual(len(images), 2)
        self.assertEqual(images[0]["data"], "abc")
        self.assertEqual(images[1]["media_type"], "image/jpeg")

    def test_image_extraction_simple_format(self):
        """
        Extrai imagem do formato simples e assume media_type image/jpeg.
        """
        from core.services.agent_factory import AgentFactory

        runtime = AgentFactory().create(self.vision_agent)

        images = runtime._extract_images({"text": "Teste", "image": "xyz123"})

        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["data"], "xyz123")
        self.assertEqual(images[0]["media_type"], "image/jpeg")

    def test_text_extraction_ignores_image_fields(self):
        """
        _extract_text() não deve incluir conteúdo dos campos de imagem.
        """
        from core.services.agent_factory import AgentFactory

        runtime = AgentFactory().create(self.vision_agent)

        payload = {
            "product": "Curso Python",
            "description": "Aprenda Python",
            "images": [{"data": "base64data", "media_type": "image/png"}],
            "image": "another_base64",
        }

        text = runtime._extract_text(payload)

        self.assertIn("product", text)
        self.assertIn("description", text)
        self.assertNotIn("base64data", text)
        self.assertNotIn("another_base64", text)

    # ---------- Testes de execução (requerem API key válida) ----------

    def test_task_execution_with_single_image(self):
        """
        Executa a vision task com uma imagem e valida o schema de saída.
        """
        executor = TaskExecutor(self.vision_task.id)

        try:
            output = executor.execute(
                input_payload={
                    "text": "Descreva esta imagem",
                    "images": [
                        {"data": TEST_IMAGE_BASE64, "media_type": "image/png"}
                    ]
                }
            )
        except Exception as e:
            if "API key" in str(e) or "api_key" in str(e):
                self.skipTest("API key não configurada")
            raise

        self.assertNotIn("_error", output, f"Erro de schema: {output.get('_error')}")
        self.assertIn("description", output)
        self.assertIn("elements", output)
        self.assertIn("confidence", output)
        self.assertIsInstance(output["description"], str)
        self.assertIsInstance(output["elements"], list)
        self.assertIsInstance(output["confidence"], (int, float))

        execution = TaskExecution.objects.filter(task=self.vision_task).first()
        self.assertIsNotNone(execution)
        self.assertEqual(execution.status, "completed")

    def test_task_execution_with_multiple_images(self):
        """
        Executa a vision task com múltiplas imagens.
        """
        executor = TaskExecutor(self.vision_task.id)

        try:
            output = executor.execute(
                input_payload={
                    "text": "Compare estas imagens",
                    "images": [
                        {"data": TEST_IMAGE_BASE64, "media_type": "image/png"},
                        {"data": TEST_IMAGE_BASE64, "media_type": "image/png"},
                        {"data": TEST_IMAGE_BASE64, "media_type": "image/png"},
                    ]
                }
            )
        except Exception as e:
            if "API key" in str(e) or "api_key" in str(e):
                self.skipTest("API key não configurada")
            raise

        self.assertNotIn("_error", output, f"Erro de schema: {output.get('_error')}")
        self.assertIn("description", output)

    def test_text_task_ignores_images_gracefully(self):
        """
        Task sem suporte a visão deve ignorar imagens e executar normalmente.
        """
        executor = TaskExecutor(self.text_task.id)

        try:
            output = executor.execute(
                input_payload={
                    "text": "Analise este texto",
                    "images": [
                        {"data": TEST_IMAGE_BASE64, "media_type": "image/png"}
                    ]
                }
            )
        except Exception as e:
            if "API key" in str(e) or "api_key" in str(e):
                self.skipTest("API key não configurada")
            raise

        # output_schema=None → retorna texto puro
        self.assertIn("text", output)
        self.assertIsInstance(output["text"], str)

        execution = TaskExecution.objects.filter(task=self.text_task).first()
        self.assertIsNotNone(execution)
        self.assertEqual(execution.status, "completed")