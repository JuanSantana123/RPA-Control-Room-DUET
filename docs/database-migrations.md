# Migrações versionadas do PostgreSQL

O schema do DUET é controlado por Alembic. A revisão inicial
`5e3799a70fb6` representa integralmente o metadata atual: tabelas, índices,
constraints, relações e tipos PostgreSQL.

## Startup seguro

`criar_banco()` serializa a operação com advisory lock e segue três caminhos:

1. banco vazio: aplica `alembic upgrade head`;
2. banco legado sem `alembic_version`: compara o schema real ao metadata e só
   registra o baseline quando não existe nenhuma diferença;
3. banco versionado: aplica apenas revisões ainda pendentes.

Um banco legado divergente interrompe a inicialização com as primeiras diferenças
encontradas. O sistema não tenta adivinhar alterações nem marca um schema
incompleto como atualizado.

## Operação manual

Sempre faça backup verificado antes de migrar um ambiente operacional.

```powershell
$env:DATABASE_URL = "postgresql://usuario:senha@host:5432/duet"
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe check
```

Para gerar uma nova revisão após alterar `models.py`:

```powershell
.\.venv\Scripts\alembic.exe revision --autogenerate -m "descricao objetiva"
```

Revise o arquivo gerado, especialmente relações circulares, defaults, operações
destrutivas e o `downgrade`. Autogeração é uma proposta de migration, não uma
aprovação automática.

## Evidência do baseline

O baseline foi exercitado em PostgreSQL 16 descartável com os ciclos:

- banco vazio → `upgrade head` → `alembic check` sem diferenças;
- `downgrade base` → `upgrade head` → `alembic check` sem diferenças;
- schema legado equivalente → stamp do baseline;
- schema legado com índice ausente → startup rejeitado e sem stamp.

O banco local de desenvolvimento `duet-ui-dev-db` também foi comparado antes do
stamp: zero diferenças foram encontradas. Nenhuma base externa ou de produção foi
acessada.
