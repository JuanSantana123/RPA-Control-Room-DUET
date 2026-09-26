# Operação do runtime DUET

## Processos de background

O Control Room executa três loops internos: Scheduler, fila de execuções e
monitoramento de heartbeat dos Devices. Em uma instalação simples, o comportamento
padrão permanece inalterado e os três iniciam junto com a API.

Para executar múltiplas réplicas HTTP, deixe somente uma instância responsável
pelos workers e configure as demais com:

```text
CONTROL_ROOM_ENABLE_BACKGROUND_WORKERS=false
```

Isso evita multiplicar consultas e ciclos operacionais sem retirar as proteções
transacionais existentes. A instância dedicada aos workers deve manter o valor
`true` (padrão). Essa variável não substitui supervisão do processo nem alta
disponibilidade; ela apenas define a responsabilidade de cada instância.

No encerramento da aplicação, os três loops recebem um sinal cooperativo, deixam
de iniciar novos ciclos e têm até dez segundos cada para finalizar. Um timeout é
registrado no log estruturado sem bloquear indefinidamente o desligamento.

## Verificação

```powershell
$env:DATABASE_URL = "postgresql://duet_test:duet_test@127.0.0.1:1/duet_test"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:DATABASE_URL
```

Os testes usam uma URL PostgreSQL sintética e não abrem conexão: as rotinas de
banco executadas pelos loops são substituídas por funções controladas. Eles
verificam inicialização única, thread ativa e encerramento de cada worker.

## Health checks e correlação

- `GET /health/live`: confirma que o processo HTTP responde, sem depender do banco.
- `GET /health/ready`: valida PostgreSQL, revisão Alembic e os workers exigidos pela
  função desta instância. Retorna HTTP 503 quando algum requisito não está pronto.

Toda resposta inclui `X-Request-ID`. O frontend envia `X-Client-Request-ID`, que é
preservado quando possui formato seguro; valores inválidos são substituídos por
UUID. O mesmo identificador entra automaticamente nos logs emitidos durante a
requisição, junto de método, endpoint, status e duração.

As respostas da API também recebem `X-Content-Type-Options: nosniff`,
`X-Frame-Options: DENY` e `Referrer-Policy: no-referrer`.

## Schema

O bootstrap utiliza migrações versionadas e rejeita automaticamente um banco
legado divergente. O procedimento completo, incluindo adoção segura do baseline,
está em `docs/database-migrations.md`.

## Fuso horário dos agendamentos

O Scheduler interpreta datas e horários no fuso IANA definido por
`DUET_TIMEZONE`. O padrão retrocompatível é:

```text
DUET_TIMEZONE=America/Sao_Paulo
```

Todas as réplicas HTTP e o processo responsável pelos workers devem usar o mesmo
valor. A API informa esse fuso ao formulário de agendamento, e horários civis
inexistentes ou ambíguos durante transições de horário são recusados antes da
persistência. A dependência `tzdata` mantém a base IANA disponível também em
hosts Windows e imagens sem dados de fuso do sistema operacional.

Alterar o fuso em uma instalação que já possui agendamentos modifica a
interpretação civil dos horários legados. Faça essa mudança somente em janela
operacional, após revisar os agendamentos existentes; não há conversão automática
silenciosa.

## Recuperação de ocorrências atrasadas

Cada agendamento possui uma política explícita para reinícios e indisponibilidades:

- `run_once` (padrão retrocompatível): materializa uma única execução atrasada e
  retoma a agenda, sem reproduzir todas as ocorrências do período indisponível;
- `skip`: registra a ocorrência perdida e avança para a próxima data válida sem
  criar uma execução antiga.

`misfire_grace_seconds` define a tolerância antes de aplicar a política (cinco
minutos por padrão). Atrasos dentro dessa janela executam normalmente. A última
ocorrência ignorada fica visível na página de Agendamentos; um agendamento único
ignorado é preservado inativo para diagnóstico e reagendamento consciente.

## Prioridade e atenção da fila

Execuções entram com prioridade `normal` e preservam `queued_at` como evidência do
tempo de espera. O worker ordena cada disputa por `urgent`, `high`, `normal` e
`low`; dentro da mesma prioridade usa o instante de entrada e o ID como desempate
determinístico. A alteração de prioridade é atômica e recusada quando o worker já
retirou a execução da fila.

A Central de Execuções sinaliza esperas acima da janela operacional configurada:

```text
DUET_QUEUE_WARNING_SECONDS=900
```

O valor aceito fica entre 60 e 86.400 segundos; ausência ou valor inválido retorna
ao padrão seguro de 15 minutos. A janela é um indicador de atenção, não cancela,
repete nem promove trabalho automaticamente.

## Manutenção e disponibilidade dos Devices

`accepting_work` é independente de `status` e `is_active`: um Device pode continuar
online e cadastrado durante manutenção, sem receber novas reservas. Pausar exige um
motivo operacional de até 240 caracteres; liberar remove esse motivo. A mudança usa
a mesma trava transacional por Device que as reservas, eliminando a janela em que
uma nova execução poderia iniciar depois da confirmação de pausa.

Execuções já em andamento não são interrompidas. Itens já enfileirados permanecem
na fila, preservando prioridade e `queued_at`, mas o worker não os despacha enquanto
o Device estiver em manutenção. Agendamentos automáticos não selecionam Devices
pausados; agendamentos vinculados aguardam disponibilidade sem serem descartados.
