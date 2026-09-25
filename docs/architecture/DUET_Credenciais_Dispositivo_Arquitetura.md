# DUET — Credenciais de Dispositivo

## Objetivo

Separar visualmente e funcionalmente:

- **Credenciais de Automação**: SAP, Oracle, APIs, SharePoint, sistemas usados pelos robôs.
- **Credenciais de Dispositivo**: identidades Windows usadas pelos Agents para criar/desbloquear sessões interativas.

A implementação continua usando o **mesmo Vault e a mesma camada de criptografia**. Não serão criados dois cofres independentes.

---

## Estrutura de navegação

### Credenciais

A página atual `Vault` passa a ter duas abas:

1. **Credenciais de Automação**
2. **Credenciais de Dispositivo**

A aba de Automação preserva integralmente a árvore de pastas e o CRUD atuais.

A aba de Dispositivo apresenta uma lista operacional de identidades Windows, sem árvore de pastas como elemento principal.

Exemplo:

```text
Credenciais

[ Credenciais de Automação ] [ Credenciais de Dispositivo ]

Credenciais de Dispositivo

Buscar credencial...                         + Nova credencial

Windows - Pilucos
DESKTOP-7T4IJEQ\Pilucos
Tipo: Windows
Devices associados: 1
Status: Ativa
```

---

## Regra de segurança

O Device **não armazena senha**.

O Agent também **não recebe senha de forma persistente**.

A associação será feita por referência:

```text
Agent
  execution_credential_id = 12
```

O Vault contém:

```text
Credential 12
  name     = Windows - Pilucos
  scope    = device
  type     = windows

Fields
  domain   = DESKTOP-7T4IJEQ
  username = Pilucos
  password = [AES-256-GCM / secret]
```

Na execução:

```text
Control Room
    ↓
Agent.execution_credential_id
    ↓
Vault
    ↓
resolve domain / username / password
    ↓
entrega temporária ao Agent
    ↓
session_authenticator.py
    ↓
RPA-Agent-Session-Broker.exe
    ↓
DuetCredentialProvider.dll
    ↓
LogonUI / Winlogon
```

---

## Banco de dados

### 1. `vault_credentials`

A tabela existente será reutilizada.

Adicionar:

```text
scope
    automation | device

credential_type
    generic | windows
```

Para `automation`:

```text
folder_id obrigatório
```

Para `device`:

```text
folder_id = NULL
```

Regra recomendada no service, não apenas na interface.

### 2. `agents`

Adicionar:

```text
execution_credential_id
```

Foreign Key:

```text
vault_credentials.id
```

O Agent guarda somente a referência da credencial.

Campos de telemetria como `username` continuam representando o usuário realmente observado na sessão Windows e não substituem `execution_credential_id`.

---

## Campos da credencial Windows

Uma credencial de Device do tipo Windows terá exatamente:

```text
domain
username
password
```

Regras:

- `domain`: não secreto.
- `username`: não secreto.
- `password`: secreto.
- Password nunca é devolvido pelo GET.
- Password nunca aparece no card.
- Não haverá botão "mostrar senha".
- Na edição, senha vazia significa preservar a senha existente.
- Alteração de senha deve ser uma ação explícita.

---

## Endpoints

### Credenciais de dispositivo

```http
GET /vault/device-credentials
POST /vault/device-credentials
GET /vault/device-credentials/{credential_id}
PUT /vault/device-credentials/{credential_id}
DELETE /vault/device-credentials/{credential_id}
```

### Associação ao Agent

```http
PATCH /agents/{agent_id}/execution-credential
```

Payload:

```json
{
  "credential_id": 12
}
```

### Remover associação

```json
{
  "credential_id": null
}
```

### Resolver credencial para execução

Esse endpoint não será exposto ao navegador.

O Control Room deve resolver internamente a credencial no momento da execução e enviar o segredo apenas ao Agent autenticado.

---

## Devices

Na edição/detalhe de um Agent:

```text
IDENTIDADE DE EXECUÇÃO WINDOWS

Credencial
[ Windows - Pilucos                    ▼ ]

Conta
DESKTOP-7T4IJEQ\Pilucos

Status
● Credencial configurada

[ Testar credencial ]
```

O dropdown consulta somente:

```text
scope = device
credential_type = windows
```

O frontend nunca recebe a senha.

---

## Roles / permissões

Credenciais de automação continuam usando as permissões atuais.

Adicionar permissões específicas para a camada Device:

```text
DeviceCredentials:view
DeviceCredentials:create
DeviceCredentials:edit
DeviceCredentials:delete
DeviceCredentials:assign
DeviceCredentials:test
```

`assign` controla quem pode associar uma identidade Windows a um Agent.

`test` controla quem pode iniciar teste de login/desbloqueio.

---

## Administração

Administração não armazena credenciais.

Pode receber futuramente políticas globais:

```text
Permitir login automático por Credential Provider
Tempo máximo de segredo em memória
Auditoria obrigatória
Bloquear execução Desktop sem identidade configurada
Política de rotação de senha
```

---

## Fluxo automático final do Agent

```text
Execução solicitada
        ↓
verificar_sessao_windows()
        ↓
Sessão correta já READY?
  ├─ Sim
  │    ↓
  │ executar Robot
  │
  └─ Não
       ↓
preparar_sessao_windows()
       ↓
Sessão ficou READY?
  ├─ Sim → executar Robot
  │
  └─ Não
       ↓
Control Room resolve execution_credential_id
       ↓
Vault descriptografa segredo somente em memória
       ↓
Agent recebe domain / username / password
       ↓
autenticar_sessao_windows()
       ↓
Broker
       ↓
Credential Provider
       ↓
Windows cria/desbloqueia sessão
       ↓
verificar_sessao_windows()
       ↓
READY para a identidade esperada?
  ├─ Não → execução bloqueada + erro auditável
  └─ Sim → iniciar_processo_robot()
```

---

## Sequência de implementação

Para evitar quebrar o que já está funcionando, aplicar um arquivo por vez nesta ordem:

1. **Models / migração**
   - `vault_credentials.scope`
   - `vault_credentials.credential_type`
   - `vault_credentials.folder_id` nullable
   - `agents.execution_credential_id`

2. **Backend de Device Credentials**
   - repository/service
   - criptografia usando a camada atual do Vault
   - endpoints.

3. **Frontend Vault**
   - abas Automação / Dispositivos.
   - preservar integralmente a aba Automação atual.
   - criar painel profissional de Device Credentials.

4. **Devices**
   - seletor de credencial de execução.
   - resumo da conta sem segredo.
   - associação por `credential_id`.

5. **Bootstrap/config do Agent**
   - sincronizar somente metadados necessários.
   - não persistir password.

6. **Execução**
   - resolver a credencial no Control Room.
   - entregar segredo temporário ao Agent.
   - integrar `session_authenticator.py`.

7. **Teste / Auditoria**
   - testar login/desbloqueio.
   - logar credential_id, Agent e resultado.
   - nunca registrar password.

---

## Decisão de arquitetura

```text
Credenciais
    ├── Automação
    │     └── organização por pastas
    │
    └── Dispositivos
          └── identidades Windows

Devices
    └── referencia uma Credencial de Dispositivo

Vault
    └── protege os segredos

Roles
    └── autoriza quem pode visualizar/criar/editar/associar/testar

Administração
    └── políticas globais
```

Essa será a arquitetura adotada para a próxima etapa.
