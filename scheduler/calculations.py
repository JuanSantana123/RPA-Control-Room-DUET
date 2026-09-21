
# ============================================================
# DEPENDÊNCIAS DE DATA E HORA
# ============================================================
#
# datetime:
#   utilizado para criar, comparar e manipular as datas
#   das ocorrências do Scheduler.
#
# timedelta:
#   utilizado para avançar minutos, horas e dias nas
#   recorrências e execuções por intervalo.
# ============================================================

from datetime import datetime, timedelta


# ============================================================
# FUNÇÃO AUXILIAR - CONVERTE HORÁRIO
# ============================================================

def _horario_para_datetime(data_base, horario):

    try:

        hora, minuto = horario.split(":")[:2]

        return data_base.replace(
            hour=int(hora),
            minute=int(minuto),
            second=0,
            microsecond=0
        )

    except (ValueError, AttributeError):

        return None


# ============================================================
# CALCULAR PRÓXIMA EXECUÇÃO
# ============================================================

def calcular_proxima_execucao(schedule, agora=None):

    if agora is None:
        agora = datetime.now()

    inicio = schedule.data_inicio

    if not inicio:
        return None

    horario_inicial = _horario_para_datetime(
        inicio,
        schedule.horario
    )

    if horario_inicial is None:
        return None


    # ========================================================
    # UMA VEZ
    # ========================================================

    if schedule.tipo == "once":

        return horario_inicial


    # ========================================================
    # CONFIGURAÇÕES DE INTERVALO
    # ========================================================

    intervalo_ativo = getattr(
        schedule,
        "intervalo_ativo",
        0
    )

    intervalo_valor = getattr(
        schedule,
        "intervalo_valor",
        None
    )

    intervalo_unidade = getattr(
        schedule,
        "intervalo_unidade",
        None
    )

    horario_fim = getattr(
        schedule,
        "horario_fim",
        None
    )


    if (
        intervalo_ativo
        and intervalo_valor
        and intervalo_valor > 0
        and intervalo_unidade
        and horario_fim
    ):

        if intervalo_unidade == "minutes":

            incremento = timedelta(
                minutes=intervalo_valor
            )

        elif intervalo_unidade == "hours":

            incremento = timedelta(
                hours=intervalo_valor
            )

        else:

            incremento = None


        if incremento:
            # ------------------------------------------------
            # DIÁRIO COM INTERVALO
            # ------------------------------------------------

            if schedule.tipo == "daily":

                # O intervalo diário pode possuir várias ocorrências
                # dentro do mesmo dia.
                #
                # Exemplo:
                #
                #     início: 08:00
                #     intervalo: 2 horas
                #     fim: 18:00
                #
                # Se agora forem 13:00, a próxima execução correta
                # é 14:00, e não 08:00 do dia seguinte.

                for deslocamento in range(0, 2):

                    data = (
                        agora +
                        timedelta(days=deslocamento)
                    ).replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    )

                    inicio_dia = _horario_para_datetime(
                        data,
                        schedule.horario
                    )

                    fim_dia = _horario_para_datetime(
                        data,
                        horario_fim
                    )

                    if (
                        inicio_dia is None
                        or fim_dia is None
                    ):
                        continue

                    # Nunca permite ocorrência anterior à data
                    # inicial configurada para o Schedule.
                    if inicio_dia < horario_inicial:

                        inicio_dia = horario_inicial

                    # Se ainda não chegamos ao primeiro horário válido,
                    # ele próprio é a próxima execução.
                    if agora < inicio_dia:

                        if inicio_dia <= fim_dia:

                            return inicio_dia

                        continue

                    candidato = inicio_dia

                    # Avança dentro da janela até encontrar a primeira
                    # ocorrência estritamente futura.
                    while candidato <= agora:

                        candidato += incremento

                    if candidato <= fim_dia:

                        return candidato

                return None


            # ------------------------------------------------
            # SEMANAL COM INTERVALO
            # ------------------------------------------------

            if schedule.tipo == "weekly":

                dias = {
                    "mon": 0,
                    "tue": 1,
                    "wed": 2,
                    "thu": 3,
                    "fri": 4,
                    "sat": 5,
                    "sun": 6
                }

                selecionados = set(
                    dia.strip().lower()
                    for dia in (
                        schedule.dias_semana or ""
                    ).split(",")
                    if dia.strip()
                )

                numeros = sorted(
                    dias[dia]
                    for dia in selecionados
                    if dia in dias
                )

                if not numeros:
                    return None

                for deslocamento in range(0, 8):

                    data = (
                        agora +
                        timedelta(days=deslocamento)
                    ).replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    )

                    if data.weekday() not in numeros:
                        continue

                    inicio_dia = _horario_para_datetime(
                        data,
                        schedule.horario
                    )

                    fim_dia = _horario_para_datetime(
                        data,
                        horario_fim
                    )

                    if (
                        inicio_dia is None
                        or fim_dia is None
                    ):
                        continue

                    if inicio_dia < inicio:
                        continue

                    if agora < inicio_dia:
                        return inicio_dia

                    candidato = inicio_dia

                    while candidato <= agora:

                        candidato += incremento

                    if candidato <= fim_dia:

                        return candidato

                return None


            # ------------------------------------------------
            # MENSAL COM INTERVALO
            # ------------------------------------------------

            if schedule.tipo == "monthly":

                dia_mes = inicio.day

                ano = agora.year
                mes = agora.month

                for _ in range(24):

                    try:

                        data = datetime(
                            ano,
                            mes,
                            dia_mes
                        )

                    except ValueError:

                        data = None

                    if data is not None:

                        inicio_dia = _horario_para_datetime(
                            data,
                            schedule.horario
                        )

                        fim_dia = _horario_para_datetime(
                            data,
                            horario_fim
                        )

                        if (
                            inicio_dia is not None
                            and fim_dia is not None
                            and inicio_dia >= inicio
                        ):

                            if agora < inicio_dia:

                                return inicio_dia

                            candidato = inicio_dia

                            while candidato <= agora:

                                candidato += incremento

                            if candidato <= fim_dia:

                                return candidato

                    mes += 1

                    if mes > 12:

                        mes = 1
                        ano += 1

                return None


    # ========================================================
    # DIÁRIO SEM INTERVALO
    # ========================================================

    if schedule.tipo == "daily":

        candidato = _horario_para_datetime(
            agora,
            schedule.horario
        )

        if candidato is None:
            return None

        if candidato < inicio:

            candidato = horario_inicial

        if candidato <= agora:

            candidato += timedelta(days=1)

        return candidato


    # ========================================================
    # SEMANAL SEM INTERVALO
    # ========================================================

    if schedule.tipo == "weekly":

        dias = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6
        }

        selecionados = set(
            dia.strip().lower()
            for dia in (
                schedule.dias_semana or ""
            ).split(",")
            if dia.strip()
        )

        numeros = sorted(
            dias[dia]
            for dia in selecionados
            if dia in dias
        )

        if not numeros:
            return None

        for deslocamento in range(0, 8):

            data = agora + timedelta(
                days=deslocamento
            )

            candidato = _horario_para_datetime(
                data,
                schedule.horario
            )

            if (
                data.weekday() in numeros
                and candidato is not None
                and candidato >= inicio
                and candidato > agora
            ):

                return candidato

        return None


    # ========================================================
    # MENSAL SEM INTERVALO
    # ========================================================

    if schedule.tipo == "monthly":

        dia_mes = inicio.day

        ano = agora.year
        mes = agora.month

        for _ in range(24):

            try:

                candidato_base = datetime(
                    ano,
                    mes,
                    dia_mes
                )

            except ValueError:

                candidato_base = None

            if candidato_base is not None:

                candidato = _horario_para_datetime(
                    candidato_base,
                    schedule.horario
                )

                if (
                    candidato is not None
                    and candidato >= inicio
                    and candidato > agora
                ):

                    return candidato

            mes += 1

            if mes > 12:

                mes = 1
                ano += 1

        return None


    return None


# ============================================================
# PRÓXIMA EXECUÇÃO APÓS UMA EXECUÇÃO
# ============================================================

def proxima_execucao_apos_execucao(
    schedule,
    agora=None
):

    if agora is None:
        agora = datetime.now()


    # ========================================================
    # UMA VEZ
    # ========================================================

    if schedule.tipo == "once":

        return None


    # ========================================================
    # INTERVALO
    # ========================================================

    intervalo_ativo = getattr(
        schedule,
        "intervalo_ativo",
        0
    )

    intervalo_valor = getattr(
        schedule,
        "intervalo_valor",
        None
    )

    intervalo_unidade = getattr(
        schedule,
        "intervalo_unidade",
        None
    )

    horario_fim = getattr(
        schedule,
        "horario_fim",
        None
    )


    if (
        intervalo_ativo
        and intervalo_valor
        and intervalo_valor > 0
        and intervalo_unidade
        and horario_fim
    ):

        if intervalo_unidade == "minutes":

            incremento = timedelta(
                minutes=intervalo_valor
            )

        elif intervalo_unidade == "hours":

            incremento = timedelta(
                hours=intervalo_valor
            )

        else:

            incremento = None


        if incremento:

            proxima = agora + incremento

            fim = _horario_para_datetime(
                agora,
                horario_fim
            )

            if (
                fim is not None
                and proxima <= fim
            ):

                return proxima


    # ========================================================
    # SEM INTERVALO / FIM DO INTERVALO
    # ========================================================

    return calcular_proxima_execucao(
        schedule,
        agora
    )

