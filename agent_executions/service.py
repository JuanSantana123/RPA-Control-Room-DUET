# ============================================================
# AGENT EXECUTIONS SERVICE
# ============================================================
#
# Regra de negócio responsável por processar o resultado final
# de uma execução enviado por um Agent.
#
# Responsabilidades:
#
# - localizar a Execution;
# - validar o Agent autenticado;
# - validar o Agent associado à Execution;
# - atualizar o status final;
# - atualizar finished_at;
# - atualizar ou limpar error_message;
# - persistir a alteração;
# - registrar logs técnicos e de observabilidade.
#
# Este módulo NÃO:
#
# - registra endpoints FastAPI;
# - autentica agent_token;
# - utiliza Depends();
# - define schemas Pydantic.
#
# ============================================================

from datetime import datetime
import logging

from database import SessionLocal
from models import Execution

from schemas.agent_executions import (
    ExecutionResultRequest,
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "control_room"
)


# ============================================================
# RECEBER RESULTADO DA EXECUÇÃO
# ============================================================

def receber_resultado_execucao_service(
    execution_id: int,
    request: ExecutionResultRequest,
    agent_autenticado,
):
    """
    Processa o resultado final de uma execução enviado pelo Agent.

    Parâmetros
    ----------
    execution_id:
        ID recebido através da URL.

    request:
        Payload enviado pelo Agent contendo execution_id,
        agent_id, status, message, started_at e finished_at.

    agent_autenticado:
        Agent previamente autenticado por get_agent_atual()
        na camada HTTP.

    Segurança
    ---------
    O agent_id informado no payload precisa corresponder:

    1. ao Agent autenticado pelo token;
    2. ao Agent associado à Execution.

    Observação
    ----------
    Preservamos o comportamento atual do sistema.

    Portanto, inclusive validações negadas retornam dicionários
    com status="error", em vez de HTTPException.
    """

    # ========================================================
    # VALIDA CONSISTÊNCIA DO EXECUTION_ID
    # ========================================================
    #
    # O identificador da execução atualmente é recebido em
    # dois pontos da requisição:
    #
    #     URL:
    #         /executions/{execution_id}/result
    #
    #     BODY:
    #         request.execution_id
    #
    # Os dois valores precisam representar exatamente a mesma
    # execução.
    #
    # Esta validação evita que um Agent, por erro de integração,
    # envie o resultado de uma execução no body enquanto aponta
    # para outra execução na URL.
    #
    # A validação ocorre ANTES da abertura da sessão do banco,
    # garantindo que uma requisição inconsistente seja rejeitada
    # sem consultar ou modificar nenhuma Execution.
    # ========================================================

    if execution_id != request.execution_id:

        logger.warning(
            "execution_id da URL não corresponde ao execution_id informado pelo Agent",
            extra={
                "event": "execution_result_id_mismatch",
                "execution_id_url": execution_id,
                "execution_id_body": request.execution_id,
                "agent_id": request.agent_id,
            },
        )

        return {
            "status": "error",
            "message": (
                "execution_id da URL não corresponde ao "
                "execution_id informado pelo Agent."
            ),
            "execution_id": execution_id,
        }


    # ========================================================
    # SESSÃO DO BANCO
    # ========================================================

    db = SessionLocal()

    try:

        # ====================================================
        # 1. LOCALIZA A EXECUÇÃO
        # ====================================================

        execucao = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id
            )
            .first()
        )


        if not execucao:

            # ------------------------------------------------
            # AUDITORIA
            # ------------------------------------------------

            logger.warning(
                "Resultado recebido para execução inexistente",
                extra={
                    "event": "execution_result_not_found",
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                },
            )


            return {
                "status": "error",
                "message": "Execução não encontrada",
                "execution_id": execution_id,
            }


        # ====================================================
        # 2. VALIDA O AGENT AUTENTICADO
        # ====================================================
        #
        # O token utilizado na requisição precisa pertencer
        # exatamente ao Agent declarado no payload.
        # ====================================================

        if agent_autenticado.agent_id != request.agent_id:

            logger.warning(
                (
                    "Agent autenticado não corresponde ao Agent "
                    "informado no resultado"
                ),
                extra={
                    "event": (
                        "execution_result_agent_auth_mismatch"
                    ),
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                },
            )


            return {
                "status": "error",
                "message": (
                    "O token não pertence ao Agent informado."
                ),
                "execution_id": execution_id,
            }


        # ====================================================
        # 3. VALIDA O AGENT DA EXECUÇÃO
        # ====================================================
        #
        # Mesmo que o Agent esteja corretamente autenticado,
        # ele só pode atualizar uma Execution associada ao
        # próprio agent_id.
        # ====================================================

        if execucao.agent_id != request.agent_id:

            logger.warning(
                (
                    "Agent não corresponde à execução "
                    "ao enviar resultado"
                ),
                extra={
                    "event": "execution_result_agent_mismatch",
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                },
            )


            return {
                "status": "error",
                "message": (
                    "Agent não corresponde à execução"
                ),
                "execution_id": execution_id,
            }


        # ====================================================
                # ====================================================
        # 4. VALIDA RESULTADO FINAL RECEBIDO DO AGENT
        # ====================================================
        #
        # O endpoint /result representa exclusivamente o
        # resultado FINAL de uma execução.
        #
        # Portanto, o Agent não pode utilizar este callback
        # para colocar uma execução em estados intermediários
        # como "queued" ou "running".
        # ====================================================

        status_finais_permitidos = {
            "success",
            "error",
            "stopped",
        }

        if request.status not in status_finais_permitidos:

            logger.warning(
                "Agent tentou informar status final inválido",
                extra={
                    "event": "execution_result_invalid_status",
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                    "current_status": execucao.status,
                    "received_status": request.status,
                },
            )

            return {
                "status": "error",
                "message": (
                    "Status inválido para resultado final "
                    "de execução."
                ),
                "execution_id": execution_id,
            }


        # ====================================================
        # 4.1 PROTEGE EXECUÇÕES JÁ FINALIZADAS
        # ====================================================
        #
        # Um callback atrasado ou repetido não pode sobrescrever
        # um resultado que já foi persistido.
        #
        # Exemplo bloqueado:
        #
        #     success -> error
        #     stopped -> success
        #
        # Um callback idêntico é tratado como idempotente.
        # Isso permite que o Agent repita o envio caso tenha
        # perdido a resposta HTTP do primeiro callback.
        # ====================================================

        status_atual = execucao.status

        if status_atual in status_finais_permitidos:

            if status_atual == request.status:

                logger.info(
                    "Callback duplicado de execução ignorado",
                    extra={
                        "event": "execution_result_duplicate",
                        "execution_id": execution_id,
                        "agent_id": request.agent_id,
                        "status": status_atual,
                    },
                )

                return {
                    "status": "success",
                    "message": (
                        "Resultado da execução já havia sido "
                        "processado."
                    ),
                    "execution_id": execution_id,
                    "execution_status": status_atual,
                    "duplicate": True,
                }

            logger.warning(
                "Tentativa de alterar execução já finalizada",
                extra={
                    "event": "execution_result_terminal_conflict",
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                    "current_status": status_atual,
                    "received_status": request.status,
                },
            )

            return {
                "status": "error",
                "message": (
                    "A execução já possui um resultado final "
                    "e não pode ser alterada."
                ),
                "execution_id": execution_id,
                "execution_status": status_atual,
            }


        # ====================================================
        # 4.2 VALIDA ESTADO DE ORIGEM
        # ====================================================
        #
        # Um resultado final somente pode ser aceito quando
        # a execução realmente chegou ao estado "running".
        #
        # Isso impede, por exemplo, que um callback atrasado
        # finalize uma execução ainda presente na fila.
        # ====================================================

        if status_atual != "running":

            logger.warning(
                "Resultado recebido para execução fora de running",
                extra={
                    "event": "execution_result_invalid_transition",
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                    "current_status": status_atual,
                    "received_status": request.status,
                },
            )

            return {
                "status": "error",
                "message": (
                    "A execução não está em estado válido "
                    "para receber resultado final."
                ),
                "execution_id": execution_id,
                "execution_status": status_atual,
            }


        # ====================================================
        # ====================================================
        # 4.3 PREPARA OS DADOS DO RESULTADO FINAL
        # ====================================================
        #
        # A transição:
        #
        #     running -> success/error/stopped
        #
        # será feita através de um UPDATE condicional.
        #
        # O próprio banco exigirá que a Execution continue
        # em "running" no instante da atualização.
        #
        # Isso elimina a janela em que dois callbacks
        # simultâneos poderiam ler "running" e ambos
        # finalizar a mesma Execution.
        # ====================================================

        finished_at = datetime.fromisoformat(
            request.finished_at
        )

        if request.status == "error":
            error_message = request.message
        else:
            error_message = None


        # ====================================================
        # 4.4 TRANSIÇÃO FINAL ATÔMICA
        # ====================================================

        linhas_atualizadas = (
            db.query(Execution)
            .filter(
                Execution.id == execution_id,
                Execution.status == "running"
            )
            .update(
                {
                    Execution.status: request.status,
                    Execution.finished_at: finished_at,
                    Execution.error_message: error_message,
                },
                synchronize_session=False
            )
        )


        # ====================================================
        # 4.5 CALLBACK PERDEU A CORRIDA
        # ====================================================
        #
        # Se nenhuma linha foi atualizada, outra transação
        # alterou o estado da Execution depois da nossa
        # leitura inicial.
        #
        # Fazemos rollback e consultamos novamente para
        # distinguir:
        #
        # 1. callback duplicado do mesmo resultado;
        # 2. callback conflitante com outro resultado final.
        # ====================================================

        if linhas_atualizadas != 1:

            db.rollback()

            execucao_atual = (
                db.query(Execution)
                .filter(
                    Execution.id == execution_id
                )
                .first()
            )

            if (
                execucao_atual
                and execucao_atual.status == request.status
            ):

                logger.info(
                    "Callback concorrente duplicado ignorado",
                    extra={
                        "event": (
                            "execution_result_concurrent_duplicate"
                        ),
                        "execution_id": execution_id,
                        "agent_id": request.agent_id,
                        "status": execucao_atual.status,
                    },
                )

                return {
                    "status": "success",
                    "message": (
                        "Resultado da execução já havia sido "
                        "processado."
                    ),
                    "execution_id": execution_id,
                    "execution_status": execucao_atual.status,
                    "duplicate": True,
                }

            logger.warning(
                "Callback perdeu transição atômica da execução",
                extra={
                    "event": (
                        "execution_result_atomic_conflict"
                    ),
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                    "current_status": (
                        execucao_atual.status
                        if execucao_atual
                        else None
                    ),
                    "received_status": request.status,
                },
            )

            return {
                "status": "error",
                "message": (
                    "A execução foi alterada por outro "
                    "processamento e o resultado recebido "
                    "não pôde ser aplicado."
                ),
                "execution_id": execution_id,
                "execution_status": (
                    execucao_atual.status
                    if execucao_atual
                    else None
                ),
            }


        # ====================================================
        # 5. PERSISTE A TRANSIÇÃO FINAL
        # ====================================================

        db.commit()


        # ====================================================
        # 6. SINCRONIZA O OBJETO ORM
        # ====================================================
        #
        # Como o UPDATE foi executado diretamente pela query
        # com synchronize_session=False, recarregamos a
        # Execution antes dos logs e do retorno.
        # ====================================================

        db.refresh(execucao)


        # ====================================================
        # 8. LOG DO RESULTADO
        # ====================================================
        #
        # Execuções com erro utilizam logger.error.
        #
        # Demais resultados utilizam logger.info.
        #
        # Isso preserva a semântica atual para ferramentas
        # externas de observabilidade.
        # ====================================================

        if request.status == "error":

            logger.error(
                "Execução finalizada com erro",
                extra={
                    "event": "execution_result_received",
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                    "status": execucao.status,
                    "error_message": request.message,
                },
            )


        else:

            logger.info(
                (
                    "Resultado final da execução "
                    "recebido do Agent"
                ),
                extra={
                    "event": "execution_result_received",
                    "execution_id": execution_id,
                    "agent_id": request.agent_id,
                    "status": execucao.status,
                },
            )


        # ====================================================
        # 9. RETORNO
        # ====================================================

        return {
            "status": "success",
            "message": (
                "Resultado da execução atualizado"
            ),
            "execution_id": execution_id,
            "execution_status": execucao.status,
        }


    except Exception as error:

        # ====================================================
        # ROLLBACK
        # ====================================================

        db.rollback()


        # ====================================================
        # LOG DA EXCEÇÃO
        # ====================================================

        logger.exception(
            "Erro ao atualizar resultado da execução",
            extra={
                "event": "execution_result_update_failed",
                "execution_id": execution_id,
                "agent_id": request.agent_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )


        # ====================================================
        # RETORNO DE ERRO
        # ====================================================
        #
        # Mantemos o comportamento existente de retornar
        # status="error" no payload.
        # ====================================================

        return {
            "status": "error",
            "message": "Erro ao atualizar execução",
            "error": str(error),
            "execution_id": execution_id,
        }


    finally:

        # ====================================================
        # ENCERRAMENTO DA SESSÃO
        # ====================================================

        db.close()