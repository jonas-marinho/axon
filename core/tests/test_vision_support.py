import os
import base64
from dotenv import load_dotenv
from django.test import TestCase

from core.models import Agent, Task, Process
from core.services.process_executor import ProcessExecutor


class VisionSupportTest(TestCase):
    """
    Testes para verificar o suporte a análise de imagens.
    """

    def setUp(self):
        load_dotenv()
        
        # Agent com suporte a visão
        self.vision_agent = Agent.objects.create(
            name="ImageAnalyzer",
            role="Visual Analyst",
            system_prompt="Analise imagens e descreva o que vê.",
            llm_config={
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 0.3,
            },
            output_schema={
                "description": "string",
                "elements": "array",
                "confidence": "number"
            }
        )
        
        # Agent sem suporte a visão
        self.text_agent = Agent.objects.create(
            name="TextAnalyzer",
            role="Text Analyst",
            system_prompt="Analise textos.",
            llm_config={
                "provider": "openai",
                "model": "gpt-4",  # Sem visão
                "temperature": 0.3,
            }
        )
        
        # Tasks
        self.vision_task = Task.objects.create(
            name="analyze_image",
            agent=self.vision_agent,
            input_mapping={
                "text": "input.text",
                "images": "input.images"
            }
        )
        
        self.text_task = Task.objects.create(
            name="analyze_text",
            agent=self.text_agent,
            input_mapping={
                "text": "input.text"
            }
        )
        
        # Processes
        self.vision_process = Process.objects.create(
            name="VisionProcess",
            entry_task=self.vision_task
        )
        
        self.text_process = Process.objects.create(
            name="TextProcess",
            entry_task=self.text_task
        )

    def test_image_detection_structured_format(self):
        """
        Testa detecção de imagens no formato estruturado.
        """
        from core.services.agent_factory import AgentFactory
        
        runtime = AgentFactory().create(self.vision_agent)
        
        # Com imagens
        payload_with_images = {
            "text": "Analise",
            "images": [{"data": "abc123", "media_type": "image/png"}]
        }
        self.assertTrue(runtime._detect_images(payload_with_images))
        
        # Sem imagens
        payload_without_images = {
            "text": "Analise apenas texto"
        }
        self.assertFalse(runtime._detect_images(payload_without_images))

    def test_image_detection_simple_format(self):
        """
        Testa detecção de imagens no formato simples.
        """
        from core.services.agent_factory import AgentFactory
        
        runtime = AgentFactory().create(self.vision_agent)
        
        # Formato simples com base64 longo
        payload = {
            "text": "Analise",
            "image": "a" * 200  # String longa simula base64
        }
        self.assertTrue(runtime._detect_images(payload))
        
        # String curta não é detectada como imagem
        payload_short = {
            "text": "Analise",
            "image": "short"
        }
        self.assertFalse(runtime._detect_images(payload_short))

    def test_process_execution_with_vision(self):
        """
        Testa execução completa de processo com imagem.
        NOTA: Este teste requer uma API key válida e fará uma chamada real.
        """
        # Cria uma imagem simples de teste (1x1 pixel PNG vermelho)
        # PNG header + IHDR + IDAT + IEND
        test_image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        test_image_base64 = base64.b64encode(test_image_bytes).decode('utf-8')
        
        executor = ProcessExecutor("VisionProcess")
        
        try:
            result = executor.execute(
                input_payload={
                    "text": "Descreva esta imagem",
                    "images": [
                        {
                            "data": test_image_base64,
                            "media_type": "image/png"
                        }
                    ]
                }
            )
            
            # Verifica estrutura do resultado
            self.assertIn("results", result)
            self.assertIn("analyze_image", result["results"])
            
            output = result["results"]["analyze_image"]
            
            # Verifica output schema
            self.assertIn("description", output)
            self.assertIn("elements", output)
            self.assertIn("confidence", output)
            
            # Verifica tipos
            self.assertIsInstance(output["description"], str)
            self.assertIsInstance(output["elements"], list)
            self.assertIsInstance(output["confidence"], (int, float))
            
        except Exception as e:
            # Se falhar por falta de API key, é esperado
            if "API key" in str(e):
                self.skipTest("API key não configurada")
            else:
                raise

    def test_text_process_ignores_images(self):
        """
        Testa que processo sem visão ignora imagens gracefully.
        """
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
        
        executor = ProcessExecutor("TextProcess")
        
        try:
            result = executor.execute(
                input_payload={
                    "text": "Analise este texto",
                    "images": [
                        {
                            "data": test_image_base64,
                            "media_type": "image/png"
                        }
                    ]
                }
            )
            
            # Deve executar normalmente, ignorando as imagens
            self.assertIn("results", result)
            self.assertIn("analyze_text", result["results"])
            
        except Exception as e:
            if "API key" in str(e):
                self.skipTest("API key não configurada")
            else:
                raise

    def test_multiple_images(self):
        """
        Testa processamento de múltiplas imagens.
        """
        # Cria uma imagem simples de teste (1x1 pixel PNG vermelho)
        # PNG header + IHDR + IDAT + IEND
        test_image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        )
        test_image_base64 = base64.b64encode(test_image_bytes).decode('utf-8')
        
        executor = ProcessExecutor("VisionProcess")
        
        try:
            result = executor.execute(
                input_payload={
                    "text": "Compare estas imagens",
                    "images": [
                        {"data": test_image_base64, "media_type": "image/png"},
                        {"data": test_image_base64, "media_type": "image/png"},
                        {"data": test_image_base64, "media_type": "image/png"}
                    ]
                }
            )
            
            self.assertIn("results", result)
            
        except Exception as e:
            if "API key" in str(e):
                self.skipTest("API key não configurada")
            else:
                raise

    def test_image_extraction(self):
        """
        Testa extração correta de imagens do payload.
        """
        from core.services.agent_factory import AgentFactory
        
        runtime = AgentFactory().create(self.vision_agent)
        
        # Formato estruturado
        payload1 = {
            "text": "Teste",
            "images": [
                {"data": "abc", "media_type": "image/png"},
                {"data": "def", "media_type": "image/jpeg"}
            ]
        }
        
        images1 = runtime._extract_images(payload1)
        self.assertEqual(len(images1), 2)
        self.assertEqual(images1[0]["data"], "abc")
        self.assertEqual(images1[1]["media_type"], "image/jpeg")
        
        # Formato simples
        payload2 = {
            "text": "Teste",
            "image": "xyz123"
        }
        
        images2 = runtime._extract_images(payload2)
        self.assertEqual(len(images2), 1)
        self.assertEqual(images2[0]["data"], "xyz123")

    def test_text_extraction_ignores_images(self):
        """
        Testa que extração de texto ignora campos de imagem.
        """
        from core.services.agent_factory import AgentFactory
        
        runtime = AgentFactory().create(self.vision_agent)
        
        payload = {
            "product": "Curso Python",
            "description": "Aprenda Python",
            "images": [{"data": "base64", "media_type": "image/png"}],
            "image": "another_base64"
        }
        
        text = runtime._extract_text(payload)
        
        # Deve conter campos de texto
        self.assertIn("product", text)
        self.assertIn("description", text)
        
        # Não deve conter referências a imagens
        self.assertNotIn("base64", text)
        self.assertNotIn("another_base64", text)