# DUET CORE — Release de Robôs e Bibliotecas

Implementação preparada sobre os arquivos enviados nesta conversa em 15/09/2026.
Os arquivos são completos: substitua os correspondentes, não cole blocos no final.

## 1. Aplicação

Faça uma cópia dos cinco arquivos que serão substituídos. Aplique os arquivos do
backend em conjunto com o Control Room parado, usando seu procedimento habitual
de reinício. Não altere a estrutura das pastas internas do ZIP.

Pasta principal do backend:

`C:\Users\Usuario\Desktop\Projeto RPA\RPA-Control-Room`

| Arquivo do ZIP | Destino | Ação |
|---|---|---|
| `backend/release_service.py` | `RPA-Control-Room/release_service.py`, ao lado de `main.py` | Adicionar |
| `backend/library_workspace.py` | `RPA-Control-Room/library_workspace.py`, ao lado de `main.py` | Adicionar |
| `backend/project_packager.py` | `RPA-Control-Room/project_packager.py` | Substituir |
| `backend/api/development.py` | `RPA-Control-Room/api/development.py` | Substituir |
| `backend/api/libraries.py` | `RPA-Control-Room/api/libraries.py` | Substituir |
| `backend/api/robots.py` | `RPA-Control-Room/api/robots.py` | Substituir |
| `frontend/Development.tsx` | O mesmo `Development.tsx` do frontend que você enviou | Substituir |

Não substitua a pasta `api` inteira: substitua apenas seus três arquivos listados.
Não precisa registrar novo router em `main.py`: as rotas foram adicionadas ao
router de Desenvolvimento já utilizado. Não há alteração de `models.py`,
`database.py`, migration, instalação de dependências ou alteração de `agent.py`,
`executions.py` ou `schedules.py`.

Reinicie o Control Room após copiar os seis arquivos Python. Atualize/recompile
o frontend pelo procedimento já utilizado no projeto. Backend e frontend desta
entrega precisam ser aplicados juntos: a confirmação agora envia os dados do Release.

## 2. Robô novo

1. Em Desenvolvimento, crie o projeto com origem **Novo Robô**.
2. Edite no Studio e teste pelo botão Executar.
3. Faça Checkin e leve o projeto até **Aprovado** no Kanban.
4. Acione Publicar para abrir a prévia do Release.
5. Escolha o nome do Robô e a pasta de destino.
6. Se precisar, preencha **Criar pastas dentro do destino**. Exemplo:
   `Financeiro/Pagamentos`. As pastas são criadas durante a publicação.
7. Confira Bibliotecas/versões, digite o nome do projeto e publique.
8. Confira o cadastro e execute o Robô publicado pela aba Robôs.

A mesma sequência de pastas já existente é reutilizada. Um projeto novo não
sobrescreve outro Robô de mesmo nome/pasta: nesse caso use a origem de PRD.

## 3. Alterar um Robô de PRD

Em **Novo projeto → Origem do projeto**, selecione o Robô de PRD e dê um nome ao
projeto de alteração. O backend recupera o código e as dependências do pacote.
O projeto nasce em Backlog, seguindo o Workflow existente.

Ao publicar a alteração, o mesmo Robot recebe a próxima versão inteira e conserva
seu ID e sua pasta. Os agendamentos que referenciam esse ID continuam referenciando
o mesmo cadastro. Uma versão mais recente em PRD bloqueia um projeto baseado em
versão antiga, evitando sobrescrever alterações feitas por outro projeto.

O Release não dispara execuções e não altera registros de agendamento.

## 4. Bibliotecas já vinculadas

Ao abrir/atualizar a árvore no Studio, o Control Room disponibiliza as cópias em:

`_libraries/<import_name>/`

Edite os arquivos internos normalmente, com Checkout. Os imports no Robô continuam
iguais, por exemplo `from pagamento import ...`: o empacotador coloca o namespace
na raiz do ZIP executável. `_libraries` é organização de Desenvolvimento.

- Biblioteca não alterada: mantém a versão base.
- Biblioteca alterada: o teste usa os arquivos editados, ainda sem criar uma versão.
- Na prévia do Release: a Biblioteca alterada recebe um campo de nova versão.
- Na confirmação: cria LibraryVersion e atualiza apenas a dependência desse projeto.
- Outros projetos/Robôs permanecem com as versões anteriores.

A sugestão inicial é o próximo número principal, como 2.0.0. Você pode informar
outro número semântico ainda não utilizado. Não se pode sobrescrever a 1.0.0.

Se você alterar dependências com o Studio já aberto, atualize a árvore/reabra o
Studio para visualizar as cópias novas. A execução já resolve a versão vinculada.

A troca/remoção de uma dependência com arquivos locais modificados é bloqueada para
não apagar seu trabalho. Publique as alterações ou restaure os arquivos à base
antes dessa troca/remoção. Os containers gerenciados não podem ser renomeados ou
apagados pelo editor; arquivos e subpastas internos continuam editáveis.

## 5. Criar Biblioteca a partir do código do Robô

A prévia lista pacotes Python próprios da raiz do projeto que possuem `__init__.py`.
Marque os pacotes que deseja disponibilizar como novas Bibliotecas e informe nome
e versão inicial. A publicação registra a Library, sua LibraryVersion de origem
`robot` e o vínculo ao projeto na mesma transação do Release.

Exemplo de pacote elegível: `financeiro/__init__.py`, junto a
`financeiro/pagamentos.py` na raiz do projeto.

Nesse projeto original o pacote permanece no local onde foi desenvolvido. O
empacotador reconhece essa cópia e não cria uma duplicata em `_libraries`.
Ao criar outro projeto a partir do Release, suas dependências são recuperadas em
`_libraries`. Os imports permanecem iguais.

Esta entrega promove pacotes da raiz com namespace próprio. Não converte
automaticamente um módulo isolado `.py` ou uma subpasta arbitrária em Biblioteca.
Um namespace já cadastrado precisa ser vinculado ao projeto como dependência;
não é criado um segundo cadastro com o mesmo namespace.

## 6. Permissões

A prévia requer `Development:publish`. A confirmação desta primeira implementação
centraliza Robô e Bibliotecas e exige estas permissões:

- `Development:publish`
- `Robots:create`
- `Libraries:publish`
- `Libraries:create`

Essas permissões são conferidas mesmo quando o Release não possui Bibliotecas
novas. A lista de Robôs de origem exige `Development:create` e `Robots:view`.
As permissões e o Checkout de edição de workspace/dependências são preservados.
Um HTTP 403 deve ser tratado na Role do usuário; não remova as verificações do código.

## 7. Preservação e limites

Os Releases usam caminhos exclusivos dentro de `storage/releases`, por ID e versão.
`Robot.file_path` aponta ao pacote atual, mantendo o contrato do executor existente.
O ZIP contém `duet-release.json` com origem, autor e versões das Bibliotecas.
Os uploads manuais também passam a gravar em caminhos exclusivos, em vez de
sobrescrever o arquivo anterior.

Não há tela de rollback ou histórico de Releases nesta entrega. Os snapshots e
manifestos ficam preservados; a tela Histórico existente não foi alterada.

Para Robôs legados, é preservado o pacote atual antes da primeira atualização via
Release. Versões que o upload antigo já sobrescreveu não podem ser recuperadas.
ZIP legado sem manifesto abre como código próprio: dependências não são adivinhadas
pelo nome da pasta. O Studio exige `main.py` na raiz; RAR precisa ser convertido
para ZIP antes de abrir como projeto de Desenvolvimento.

A prévia usa hash do conteúdo. Se código, dependências ou versão de PRD mudarem
após sua abertura, a publicação é bloqueada e a prévia deve ser reaberta.
Ela não certifica que o último teste aprovado usou esses mesmos bytes: execute o
projeto depois de salvar as alterações e faça Checkin antes de publicar.

As verificações de concorrência usam locks transacionais no PostgreSQL. Eles não
foram exercitados contra o PostgreSQL da sua instalação. Alterações feitas
externamente no filesystem, fora do Studio, não participam desses locks.

## 8. Verificação realizada

- Compilação sintática dos arquivos Python.
- Registro dos routers reais em FastAPI e geração de OpenAPI.
- 15 testes automatizados com os modelos enviados e SQLite temporário com FKs.
- Execução real de um pacote de teste confirmando import da Biblioteca modificada.
- Robô novo, pastas encadeadas, três Bibliotecas com só uma alterada.
- Recuperação de PRD e atualização do mesmo Robot com preservação do ZIP anterior.
- Nova Biblioteca publicada a partir do Robô.
- Prévia desatualizada, versão duplicada, base de PRD antiga, aprovação/Checkout.
- Falha de escrita e falha de commit, com rollback dos registros e artefatos novos.
- Upload manual posterior sem sobrescrever o pacote do Release.
- Proteção de caminhos ZIP e troca de dependência com rematerialização.
- TypeScript em modo strict com tipos reais do React e stubs de API, ícones e navegação.

Não foi executado o build completo do seu frontend, a interface no seu navegador,
o Scheduler ou o Agent Windows. A primeira validação na sua instalação deve ser
com um projeto de teste, antes de atualizar um Robô operacional.
