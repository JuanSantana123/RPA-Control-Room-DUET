"""
Segurança de rede para comunicação Control Room -> Agent.

Este módulo centraliza a validação dos destinos de rede utilizados
pelo Control Room antes de qualquer conexão HTTP com um Agent.

Objetivos principais:
- impedir SSRF para destinos especiais/perigosos;
- validar host e porta;
- resolver hostnames antes da conexão;
- permitir redes privadas legítimas utilizadas pelos Agents;
- bloquear redirects HTTP;
- centralizar timeouts de conexão/leitura.

IMPORTANTE:
Redes privadas RFC1918 são permitidas porque os Agents normalmente
executam dentro da infraestrutura privada da organização.
"""

import ipaddress
import os
import socket
from dataclasses import dataclass


# ============================================================
# CONFIGURAÇÃO DE REDE
# ============================================================

# Portas TCP válidas.
MIN_AGENT_PORT = 1
MAX_AGENT_PORT = 65535


# Timeout separado:
#
# CONNECT_TIMEOUT:
# tempo máximo para estabelecer conexão TCP.
#
# READ_TIMEOUT:
# tempo máximo aguardando resposta após conexão.
AGENT_CONNECT_TIMEOUT = 3
AGENT_READ_TIMEOUT = 5

AGENT_REQUEST_TIMEOUT = (
    AGENT_CONNECT_TIMEOUT,
    AGENT_READ_TIMEOUT,
)

# ============================================================
# PROTOCOLO DE COMUNICAÇÃO CONTROL ROOM -> AGENT
# ============================================================
#
# Permite preparar o DUET para HTTP ou HTTPS sem alterar
# os services que consomem ValidatedAgentTarget.base_url.
#
# Valores aceitos:
#
#     http
#     https
#
# O padrão permanece HTTP para preservar integralmente o
# comportamento das instalações atuais.
#
# Exemplo futuro:
#
#     DUET_AGENT_SCHEME=https
#
# Quando HTTPS for efetivamente habilitado, a configuração
# de confiança da CA/certificado será tratada separadamente.
# ============================================================

AGENT_SCHEME_ENV = "DUET_AGENT_SCHEME"


def obter_agent_scheme() -> str:
    """
    Retorna o protocolo configurado para comunicação
    Control Room -> RPA-Agent.

    O valor padrão é HTTP para manter compatibilidade com
    os Agents existentes.
    """

    scheme = (
        os.getenv(
            AGENT_SCHEME_ENV,
            "http",
        )
        .strip()
        .lower()
    )

    if scheme not in {
        "http",
        "https",
    }:
        raise AgentNetworkSecurityError(
            "Protocolo de comunicação com Agent inválido."
        )

    return scheme
# ============================================================
# RESULTADO DA VALIDAÇÃO
# ============================================================


@dataclass(frozen=True)
class ValidatedAgentTarget:
    """
    Representa um destino de Agent que passou pela validação
    de segurança.

    host:
        Host original normalizado.

    port:
        Porta TCP validada.

    resolved_ips:
        IPs obtidos pela resolução DNS ou pelo IP informado
        diretamente.
    """

    host: str
    port: int
    resolved_ips: tuple[str, ...]

    @property
    def base_url(self) -> str:
        """
        Monta a URL base utilizada pelo Control Room para
        comunicação com este RPA-Agent.

        O protocolo é obtido através de DUET_AGENT_SCHEME.

        Padrão:
            http

        Futuro ambiente TLS:
            https
        """

        scheme = obter_agent_scheme()

        # IPv6 literal precisa de colchetes quando utilizado
        # como host dentro de uma URL.
        try:
            endereco = ipaddress.ip_address(
                self.host
            )

            if endereco.version == 6:
                return (
                    f"{scheme}://"
                    f"[{self.host}]:{self.port}"
                )

        except ValueError:
            pass

        return (
            f"{scheme}://"
            f"{self.host}:{self.port}"
        )


# ============================================================
# EXCEÇÃO CONTROLADA
# ============================================================


class AgentNetworkSecurityError(ValueError):
    """
    Exceção lançada quando um destino de Agent não atende às
    regras de segurança de rede.
    """


# ============================================================
# NORMALIZAÇÃO DO HOST
# ============================================================


def _normalizar_host(host: object) -> str:
    """
    Normaliza e valida estruturalmente o host recebido.

    Não aceita:
    - host vazio;
    - URL completa;
    - caminho;
    - query string;
    - fragmento;
    - credenciais embutidas;
    - caracteres de controle.
    """

    if not isinstance(host, str):
        raise AgentNetworkSecurityError(
            "Host do Agent inválido."
        )

    host_normalizado = host.strip()

    if not host_normalizado:
        raise AgentNetworkSecurityError(
            "Host do Agent inválido."
        )

    # Evita entrada como:
    #
    # http://servidor
    # servidor/caminho
    # servidor?x=1
    # usuario@servidor
    #
    # O campo deve representar somente um hostname ou IP.
    caracteres_proibidos = (
        "/",
        "\\",
        "?",
        "#",
        "@",
    )

    if any(
        caractere in host_normalizado
        for caractere in caracteres_proibidos
    ):
        raise AgentNetworkSecurityError(
            "Host do Agent possui formato inválido."
        )

    # Caracteres de controle podem permitir manipulação de
    # protocolo/logs e nunca são válidos em nosso host.
    if any(
        ord(caractere) < 32
        for caractere in host_normalizado
    ):
        raise AgentNetworkSecurityError(
            "Host do Agent possui caracteres inválidos."
        )

    # Aceita IPv6 literal informado como [::1], removendo os
    # colchetes para a validação/resolução interna.
    if (
        host_normalizado.startswith("[")
        and host_normalizado.endswith("]")
    ):
        host_normalizado = host_normalizado[1:-1]

    return host_normalizado


# ============================================================
# VALIDAÇÃO DA PORTA
# ============================================================


def _validar_porta(port: object) -> int:
    """
    Converte e valida a porta TCP do Agent.

    Boolean é rejeitado explicitamente porque bool é subclasse
    de int em Python.
    """

    if isinstance(port, bool):
        raise AgentNetworkSecurityError(
            "Porta do Agent inválida."
        )

    try:
        porta = int(port)

    except (TypeError, ValueError):
        raise AgentNetworkSecurityError(
            "Porta do Agent inválida."
        )

    if not MIN_AGENT_PORT <= porta <= MAX_AGENT_PORT:
        raise AgentNetworkSecurityError(
            "Porta do Agent fora do intervalo permitido."
        )

    return porta


# ============================================================
# VALIDAÇÃO DO ENDEREÇO IP
# ============================================================


def _validar_ip(ip_texto: str):
    """
    Valida um endereço resolvido.

    Política do DUET:
    - IP privado é permitido;
    - IP público é permitido;
    - loopback é bloqueado;
    - link-local é bloqueado;
    - multicast é bloqueado;
    - unspecified é bloqueado;
    - reserved é bloqueado.

    Não bloqueamos RFC1918 porque os Agents executam
    normalmente em VMs da rede privada.
    """

    try:
        endereco = ipaddress.ip_address(ip_texto)

    except ValueError:
        raise AgentNetworkSecurityError(
            "Endereço IP do Agent inválido."
        )

    if endereco.is_loopback:
        raise AgentNetworkSecurityError(
            "Endereço loopback não é permitido para Agents."
        )

    if endereco.is_link_local:
        raise AgentNetworkSecurityError(
            "Endereço link-local não é permitido para Agents."
        )

    if endereco.is_multicast:
        raise AgentNetworkSecurityError(
            "Endereço multicast não é permitido para Agents."
        )

    if endereco.is_unspecified:
        raise AgentNetworkSecurityError(
            "Endereço não especificado não é permitido para Agents."
        )

    if endereco.is_reserved:
        raise AgentNetworkSecurityError(
            "Endereço reservado não é permitido para Agents."
        )

    return endereco


# ============================================================
# RESOLUÇÃO DNS
# ============================================================


def _resolver_host(
    host: str,
    port: int,
) -> tuple[str, ...]:
    """
    Resolve o host antes da conexão.

    Todos os IPs retornados são validados. Isso é importante:
    não basta validar apenas o primeiro endereço DNS.

    Caso qualquer endereço resolvido seja proibido, o destino
    inteiro é recusado.
    """

    # Primeiro verifica se o próprio host já é um IP literal.
    try:
        endereco = ipaddress.ip_address(host)

    except ValueError:
        endereco = None

    if endereco is not None:

        _validar_ip(str(endereco))

        return (
            str(endereco),
        )

    try:
        resultados = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM,
        )

    except socket.gaierror as error:
        raise AgentNetworkSecurityError(
            "Não foi possível resolver o host do Agent."
        ) from error

    ips = []

    for resultado in resultados:

        sockaddr = resultado[4]

        if not sockaddr:
            continue

        ip_resolvido = sockaddr[0]

        _validar_ip(ip_resolvido)

        if ip_resolvido not in ips:
            ips.append(ip_resolvido)

    if not ips:
        raise AgentNetworkSecurityError(
            "Host do Agent não possui endereço válido."
        )

    return tuple(ips)


# ============================================================
# VALIDAÇÃO PÚBLICA
# ============================================================


def validar_destino_agent(
    host: object,
    port: object,
) -> ValidatedAgentTarget:
    """
    Valida completamente o destino antes de o Control Room
    iniciar comunicação com o Agent.

    Esta é a função pública que deve ser utilizada pelos
    services antes de montar URLs ou chamar requests.
    """

    host_normalizado = _normalizar_host(host)
    porta = _validar_porta(port)

    ips = _resolver_host(
        host_normalizado,
        porta,
    )

    return ValidatedAgentTarget(
        host=host_normalizado,
        port=porta,
        resolved_ips=ips,
    )