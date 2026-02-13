import logging
from typing import Dict, Any

from django.utils import timezone

from core.models import Process, Task
from core.models import ProcessExecution, TaskExecution
from core.services.agent_factory import AgentFactory
from core.services.condition_evaluator import ConditionEvaluator
from core.services.mapping_resolver import MappingResolver

logger = logging.getLogger(__name__)


class ProcessExecutor:
    def __init__(self, process_name):
        logger.info(f"Inicializando ProcessExecutor para processo: '{process_name}'")
        self.agent_factory = AgentFactory()
        self.process = self._get_process(process_name)
        logger.info(f"ProcessExecutor inicializado com sucesso - Process ID: {self.process.id}")

    def execute(
        self,
        input_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Executa um processo completo pelo nome
        """
        logger.info(f"========== INICIANDO EXECUÇÃO DO PROCESSO: {self.process.name} ==========")
        logger.debug(f"Input payload recebido: {input_payload}")
        
        state = {
            "input": input_payload,
            "results": {},
            "meta": {}
        }

        process_execution = ProcessExecution.objects.create(
            process=self.process,
            input_payload=input_payload,
            state=state,
            status="running"
        )
        logger.info(f"ProcessExecution criado - ID: {process_execution.id}, Status: running")

        current_task = self.process.entry_task
        task_count = 0

        try:
            while current_task:
                task_count += 1
                logger.info(f"--- Executando Task #{task_count}: '{current_task.name}' (ID: {current_task.id}) ---")
                
                task_execution = TaskExecution.objects.create(
                    process_execution=process_execution,
                    task=current_task,
                    input_payload={}
                )
                logger.debug(f"TaskExecution criado - ID: {task_execution.id}")

                # Executa task
                try:
                    output = self._execute_task(current_task, state)
                    logger.info(f"Task '{current_task.name}' executada com sucesso")
                    logger.debug(f"Output da task: {output}")
                except Exception as task_error:
                    logger.error(f"Erro ao executar task '{current_task.name}': {str(task_error)}", exc_info=True)
                    raise

                task_execution.output_payload = output
                task_execution.status = "completed"
                task_execution.finished_at = timezone.now()
                task_execution.save()
                logger.info(f"TaskExecution {task_execution.id} salvo com status: completed")

                # Atualiza state
                state["results"][current_task.name] = output

                # Determina próxima task
                next_task = self._get_next_task(
                    self.process,
                    current_task,
                    state
                )
                
                if next_task:
                    logger.info(f"Transição aprovada - Próxima task: '{next_task.name}' (ID: {next_task.id})")
                else:
                    logger.info("Nenhuma transição válida encontrada - Finalizando processo")
                
                current_task = next_task

            # Finalização com sucesso
            process_execution.state = state
            process_execution.status = "completed"
            process_execution.finished_at = timezone.now()
            process_execution.save()
            
            logger.info(f"========== PROCESSO '{self.process.name}' CONCLUÍDO COM SUCESSO ==========")
            logger.info(f"Total de tasks executadas: {task_count}")
            logger.info(f"ProcessExecution ID: {process_execution.id}, Status: completed")
            logger.debug(f"Estado final do processo: {state}")

        except Exception as e:
            logger.error(
                f"========== ERRO NA EXECUÇÃO DO PROCESSO '{self.process.name}' ==========",
                exc_info=True
            )
            logger.error(f"Tipo do erro: {type(e).__name__}")
            logger.error(f"Mensagem: {str(e)}")
            logger.error(f"Tasks executadas antes do erro: {task_count}")
            
            process_execution.status = "failed"
            process_execution.finished_at = timezone.now()
            process_execution.state = state
            process_execution.save()
            
            logger.info(f"ProcessExecution {process_execution.id} marcado como failed")

            raise e

        return state

    # ---------- Métodos internos ----------

    def _get_process(self, process_name: str) -> Process:
        logger.debug(f"Buscando processo com nome: '{process_name}'")
        try:
            process = Process.objects.get(
                name=process_name,
                is_active=True
            )
            logger.debug(f"Processo encontrado - ID: {process.id}, Versão: {process.version}")
            return process
        except Process.DoesNotExist:
            logger.error(f"Processo '{process_name}' não encontrado ou inativo no banco de dados")
            raise RuntimeError(f"Process '{process_name}' não encontrado")

    def _get_next_task(self, process: Process, current_task: Task, state: dict):
        logger.debug(f"Avaliando transições a partir da task '{current_task.name}'")
        
        transitions = process.transitions.filter(
            from_task=current_task
        )
        
        logger.debug(f"Total de transições encontradas: {transitions.count()}")

        for idx, transition in enumerate(transitions, 1):
            logger.debug(f"Avaliando transição #{idx}: '{transition.from_task.name}' → '{transition.to_task.name}'")
            logger.debug(f"Condição: {transition.condition}")
            
            try:
                result = ConditionEvaluator.evaluate(
                    transition.condition,
                    state
                )
                logger.debug(f"Resultado da avaliação: {result}")
                
                if result:
                    logger.info(f"Condição satisfeita para transição: '{transition.to_task.name}'")
                    return transition.to_task
                else:
                    logger.debug(f"Condição não satisfeita - Continuando para próxima transição")
                    
            except Exception as eval_error:
                logger.warning(
                    f"Erro ao avaliar condição da transição #{idx}: {str(eval_error)}",
                    exc_info=True
                )
                continue

        logger.debug("Nenhuma transição teve condição satisfeita")
        return None

    def _execute_task(self, task: Task, state: dict) -> dict:
        """
        Executa uma Task:
        - resolve inputs a partir do state
        - executa o agent
        - retorna output estruturado
        """
        logger.debug(f"Preparando execução da task '{task.name}'")
        logger.debug(f"Agent associado: '{task.agent.name}' (ID: {task.agent.id})")

        # Resolve inputs
        logger.debug(f"Resolvendo input_mapping: {task.input_mapping}")
        input_payload = MappingResolver.resolve(
            task.input_mapping,
            state
        )
        logger.debug(f"Input payload resolvido: {input_payload}")

        # Cria o runtime do agent
        logger.debug(f"Criando runtime do agent '{task.agent.name}'")
        agent_runtime = self.agent_factory.create(task.agent, output_schema=task.output_schema)

        # Executa o agent
        logger.info(f"Invocando agent '{task.agent.name}' via LLM")
        try:
            output = agent_runtime.run(input_payload)
            logger.info(f"Agent '{task.agent.name}' retornou resposta com sucesso")
            logger.debug(f"Output bruto do agent: {output}")
        except Exception as agent_error:
            logger.error(f"Erro durante execução do agent '{task.agent.name}': {str(agent_error)}", exc_info=True)
            raise

        # Aplica output_mapping (se existir)
        if task.output_mapping:
            logger.debug(f"Aplicando output_mapping: {task.output_mapping}")
            output = MappingResolver.apply_output_mapping(
                task.output_mapping,
                output,
                state
            )
            logger.debug(f"Output após mapping: {output}")
        else:
            logger.debug("Nenhum output_mapping definido - Usando output bruto")

        return output