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
