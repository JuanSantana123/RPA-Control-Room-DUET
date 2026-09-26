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

## Schema

O bootstrap utiliza migrações versionadas e rejeita automaticamente um banco
legado divergente. O procedimento completo, incluindo adoção segura do baseline,
está em `docs/database-migrations.md`.
