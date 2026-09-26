# Reconstrução integral do frontend — inventário e evidências

Atualizado em 26/09/2026. Este registro separa implementação, integração real local e limites de validação. A stack usada para os testes é dedicada e sintética; nenhuma automação foi publicada ou executada.

## Arquitetura e direção

O frontend continua em React, TypeScript e Vite, preservando rotas, hooks de domínio, contratos HTTP, sessão por cookie HttpOnly e RBAC recebido do backend. A reconstrução adotou base grafite/neutra, violeta como ação e verde apenas para saúde/sucesso. Marca e favicon DUET são vetoriais e locais; não há CDN, analytics ou serviço visual externo.

O design system está em `frontend/src/styles/tokens.css`, com cores semânticas, superfícies, texto, bordas, tipografia, espaçamento, raios, elevação, movimento, camadas, shell e breakpoints. `theme-overrides.css` fecha a cobertura dos módulos legados. A escolha claro/escuro/sistema é persistida e resolvida antes do React para evitar flash.

`motion.css`, `controls.css`, `skeletons.css` e `refinements.css` formam a camada transversal de interação. Ela aplica transições de rota sem alterar o referencial dos overlays, feedback de hover/press/busy, entradas graduais, fundo ambiente, menus contextuais, selects acessíveis do design system e toggles animados preservando foco e semântica. `prefers-reduced-motion` desativa o movimento não essencial. Skeletons distintos para dashboard, tabelas, cards e painéis substituem spinners genéricos nas superfícies assíncronas.

O shell compartilhado organiza Operação, Construção e Administração, preserva RBAC, fornece skip link, foco visível, cabeçalho adaptativo e drawer móvel com fechamento por Escape/backdrop. A topbar foi reduzida às ações globais: removeu título/subtítulo duplicados e o controle de tema passou a usar exclusivamente ícones acessíveis para claro, escuro e sistema. Páginas são carregadas sob demanda; Monaco/Studio fica fora do bundle inicial. Busca e notificações sem implementação real foram removidas para não expor controles fictícios.

## Matriz rastreável

| Entrada | Finalidade, superfícies e permissões | Integrações preservadas | Implementação e validação |
|---|---|---|---|
| `/login` | Autenticação pública; formulário, envio, erro e ajuda | `POST /auth/login`, `GET /auth/me` | Reconstruída; login real, sessão, claro/escuro e 320/390/768/1440 validados. |
| `/` | `Dashboard:view`; indicadores, saúde, resumo, loading/erro/vazio | `/dashboard/stats`, `/executions` | Reconstruída e integrada; desktop/tablet/mobile e ambos os temas validados. |
| `/agents` | `Agents:view`; dispositivos, cadastro, nome, ambiente, download e exclusão | `/agents`, `/agents/{id}/display`, `/environment`, `/download` | Reconstruída e integrada para leitura; porta validada entre 1 e 65535 e falhas usam banner persistente com causa e orientação. A causa da tentativa na porta 3001 foi identificada e tratada no contrato do backend. |
| `/development` | `Development:view`; projetos, busca, criação, Kanban e ciclo de aprovação | `/development/projects`, `/workflow/board`, preview/publish | Reconstruída; ganhou resumo de capacidade/planejamento, filtros combináveis de situação e origem, ordenação e alternância consistente entre Projetos, Kanban e Lixeira. A criação virou um fluxo guiado, responsivo e sem perda de rascunho, com origem explícita, seleção navegável de robô existente, validação contextual e ações estáveis. Comentários usam compositor compartilhado, histórico legível e atalho Ctrl/Cmd+Enter. Projeto sintético criado pela UI e Kanban validado; publicação/execução não disparadas. |
| `/development/:projectId/studio` | Edição; checkout/checkin, explorer, Monaco, terminal, arquivos e bibliotecas | `/workspace/*`, `/checkout`, `/checkin`, bibliotecas, WebSocket | Reconstruída; desktop e 390 px validados. Checkout, arquivo temporário, salvar, excluir e checkin exercitados; terminal real não acionado. |
| `/robots` | `Robots:view`; pastas, cards, upload/download, bibliotecas e ações | `/robot-folders`, `/robots/*`, execução, abrir como projeto | Reconstruída com visão operacional, localização atual, métricas, workspace contextual, busca, ordenação, visualização grade/lista, upload direto e catálogo de bibliotecas reorganizado. A Raiz de Robôs agora é carregada automaticamente e aceita upload sem exigir uma pasta artificial; criação de pasta pode ser cancelada. Alertas nativos foram substituídos por feedback integrado e explícito. Árvore, vazio, biblioteca e layouts validados; nenhuma mutação operacional foi disparada. |
| `/executions` | `Executions:view`; resumo, filtros, detalhes, polling, cancelar/parar | `/executions`, `/cancel`, `/execution/stop` | Reconstruída; leitura/polling, vazio e layouts validados. Cancelamento/parada não testados sem execução real. |
| `/history` | `History:view`; filtros, resultado e rastreabilidade | `/executions/history` | Reconstruída e integrada; vazio e tabela responsiva validados. |
| `/schedules` | `Schedules:view`; lista, criar/editar, opções, status e excluir | `/schedules`, `/options`, `/status` | Reconstruída e integrada para leitura; modal portaled, responsivo e dividido por intenção, com skeleton de opções, erro recuperável no próprio diálogo, preservação do rascunho, validação antes do envio, foco/rolagem contidos e ações sempre alcançáveis. Gravação exige robô publicado e não foi disparada. |
| `/logs` | `Logs:view`; atualização, falha parcial, níveis, vazio e timestamp | `GET /logs?limit=500` | Módulos ausentes restaurados; página reconstruída e integrada. Conteúdo permanece texto, sem HTML injetado. |
| `/vault` | `Vault:view`; pastas, credenciais e credenciais de dispositivo | `/vault/folders`, `/vault/credentials`, device credentials | Reconstruída e integrada para leitura; formulário de pasta e layouts validados. Segredos não foram criados nem alterados. |
| `/roles` | `Roles:view`; criação, permissões, contagens e exclusão | `/roles`, `/roles/permissions`, `/roles/{id}/permissions` | Reconstruída e integrada; formulários de criação/permissões e RBAC real validados sem alterar perfis. |
| `/users` | `Users:view`; criação, perfis, senha, status e exclusão | `/auth/users`, `/roles`, `/password`, `/status` | Reconstruída e integrada; edição de perfis/senha aberta e validada sem mutar a conta administrativa. |
| `*` | Estado 404 autenticado e retorno | Nenhuma | Implementada e compilada. |

Cobertura verificável: 13 entradas funcionais e o estado 404 inventariados; 13 entradas reconstruídas; 13 conectadas aos contratos existentes; login, 11 rotas do shell e Studio navegados contra o backend real local. Ações que poderiam executar robôs, publicar pacotes, cancelar trabalho, alterar segredos ou comprometer a conta administrativa foram deliberadamente excluídas da execução, mas seus controles e contratos foram preservados.

## Estados, acessibilidade e responsividade

- Reflow dedicado em 390, 768 e 1440 px; base compartilhada também verificada em 320 px. Tabelas operacionais viram cartões rotulados no celular, sem perder ações essenciais.
- Tema claro, escuro e sistema; superfícies, formulários, tabelas, modais, Studio e estados vazios cobertos nos dois temas.
- Skip link, landmarks, títulos, labels programáticos, foco visível, `role=status`/`role=alert`, Escape no drawer, semântica de botões e preferência por movimento reduzido.
- Estados de sessão, módulos, envio, vazio, erro, sucesso, 404 e falhas parciais preservados. O servidor continua autoridade para autorização.
- O Dashboard ganhou um Centro de Comando responsivo com disponibilidade calculada, capacidade operacional e atalhos contextuais, usando exclusivamente dados e permissões já retornados pelo backend.
- Os 21 pontos com `select` usam `PremiumSelect`: combobox/listbox com portal, navegação por teclado, seleção marcada, reposicionamento no viewport e integração preservada com os handlers existentes. Checkboxes funcionais são apresentados como toggles animados. A auditoria de workflows falha se esses controles regredirem para aparência nativa não padronizada.
- Emojis e glifos decorativos foram removidos da interface. Ícones estruturais e de ação usam Lucide, traço consistente e superfícies monocromáticas; cor permanece reservada a estado semântico e ação primária.
- Contadores, barras de busca, grids, tabelas e ações foram normalizados. O drawer de detalhes do Kanban ganhou grid responsivo, labels programáticos, transição e formulários consistentes. No Vault, a ausência de `DeviceCredentials:view` apresenta estado restrito e evita a requisição proibida, preservando o backend como autoridade.
- O modal de agendamento usa `role=dialog`, associação de título, enquadramento por `dvh`, rolagem contida e cabeçalho/ações fixos. A transição de rota não cria um novo containing block que desloque overlays `fixed`.
- A auditoria automatizada é uma proteção contra regressões, não uma declaração de conformidade integral WCAG 2.2 AA; revisão assistiva/manual continua sendo um gate de aceitação.

## Ajustes mínimos de backend

### Estágios do fluxo de Desenvolvimento

1. **Problema:** em banco novo, `POST /development/projects` retornava 500 porque o estágio estrutural `BACKLOG` não existia.
2. **Alternativa somente no frontend:** não é válida; inventar o estágio no navegador deixaria o registro sem a referência exigida pelo domínio e pelo banco.
3. **Justificativa:** `development/bootstrap.py` cria somente códigos ausentes, preserva códigos/posições existentes e é chamado após a criação das tabelas. Nenhum endpoint, payload ou regra de autorização mudou.
4. **Impacto:** na inicialização, podem ser inseridos até sete estágios canônicos em uma instalação vazia: Backlog, Em desenvolvimento, Pronto para testes, Em testes, Homologação, Aprovado e Publicado.
5. **Testes:** banco PostgreSQL sintético dedicado; bootstrap idempotente; sete estágios consultados; criação real de projeto, Kanban, Studio, checkout/checkin e ciclo de arquivo aprovados.
6. **Reversão:** remover a chamada em `main.py` e `development/bootstrap.py`. Linhas já referenciadas não devem ser apagadas; em banco dedicado vazio, podem ser removidas antes de criar projetos.

### Dependências de execução

`cryptography==50.0.1` e `psycopg2-binary==2.9.13` foram registradas em `requirements.txt`, pois são imports necessários para iniciar a aplicação com PostgreSQL. A alteração não muda contratos e pode ser revertida removendo essas duas linhas caso o empacotamento externo volte a fornecê-las explicitamente.

### Erro explícito no cadastro de dispositivos

A tentativa de criar o dispositivo na porta 3001 falhou porque `DUET_AGENT_TOKEN_KEY` não estava configurada no processo do Control Room. O serviço agora distingue essa falha de segurança, executa rollback, registra `agent_creation_security_configuration_missing` e retorna `error_code: agent_token_key_unavailable` com orientação explícita para configurar a chave e reiniciar o backend. A chave não é criada, persistida ou exibida pelo frontend; continua sendo segredo operacional externo obrigatório.

## Verificações e evidências

- A matriz por família, consumidores e estados está em `docs/frontend-component-audit.md`; ela distingue auditado, implementado, aplicado, validado e bloqueado.
- O catálogo local de desenvolvimento está em `/component-lab` e não entra no build de produção. `npm run test:components` aprovou 390 px escuro, 1440 px claro e 320 px com movimento reduzido, inclusive foco, nomes acessíveis, labels, overflow e tamanho mínimo de ação.
- TypeScript passou a exigir `strict` e `noUncheckedIndexedAccess`. `exactOptionalPropertyTypes` foi avaliado e permaneceu fora desta rodada até a migração controlada dos 21 contratos opcionais encontrados.
- `npm run build`: aprovado com 2.107 módulos. CSS compartilhado: 193,25 kB (28,21 kB gzip); Robots: 65,06 kB; Development: 68,91 kB; Studio/Monaco isolado: 402,42 kB (102,07 kB gzip).
- `npm run lint`: aprovado sem erros e sem avisos. Ciclos de efeitos, dependências de callbacks, polling e separação do contexto de autenticação foram corrigidos sem relaxar regras.
- `npm audit --omit=dev`: zero vulnerabilidades conhecidas após a atualização compatível do Monaco.
- `npm run test:visual`: 31 cenários aprovados em 320/390/768/1440, claro/escuro e movimento reduzido, com labels, idioma, drawer, console, alvos, overflow e upload na raiz. A matriz inclui o formulário de pasta aberto, Execuções vazia, Histórico e Agendamentos vazios, modal de agendamento em 390/768 e novo projeto em 390/1440. Também bloqueia regressões para buscas locais, vazios legados e ícones decorativos no cabeçalho.
- `npm run test:live-ui`: 66 combinações (11 rotas × 3 larguras × 2 temas) contra backend real, verificando acesso direto, título, tema, campos/botões nomeados, erros visíveis, rede, console e overflow.
- `npm run test:workflow-ui`: 21 checkpoints reais e seguros, incluindo skeleton contextual com 49 blocos, controles de tema somente por ícones, ambiente do dispositivo, workspace de Robôs, resumo/filtros de Desenvolvimento, modal de agendamento, selects/toggles, perfil, permissões, Vault e credenciais de dispositivo, usuário, projeto, Kanban, drawer de detalhes, Studio desktop/mobile, arquivo, bibliotecas, checkin e navegação móvel.
- A reexecução autenticada de `test:workflow-ui` nesta passagem ficou bloqueada pela ausência de `DUET_TEST_ADMIN_PASSWORD`; nenhuma credencial foi inferida ou persistida. A validação desta rodada usa os 31 cenários isolados, o catálogo e as evidências reais já registradas acima.
- `npm run test:performance`: medição laboratorial local do Dashboard em desktop/mobile; LCP de 1116/588 ms, CLS 0 e interação sintética de 13,6/11,2 ms. É proxy local sem throttling, não INP de campo nem percentil 75.
- `python -m compileall`: aprovado; `pip check`: nenhuma dependência quebrada; `git diff --check`: aprovado.

Na passagem atômica final, os modais extraídos de bibliotecas foram efetivamente integrados ao Studio, 16 ações de Libraries migraram para `Button`/`IconButton`, e as famílias genéricas legadas de botões foram removidas após conferência de consumidores. Os módulos operacionais deixaram de carregar cores literais concorrentes; valores privados permanecem apenas nas fundações e nas paletas encapsuladas de Login/Studio. A camada de erros recebe `unknown`, valida estruturas externas em runtime e não contém `any`, dupla coerção ou supressões TypeScript. Logs distingue falha inicial de atualização interrompida, preserva dados anteriores quando disponíveis e nunca anuncia conexão saudável durante erro.

Capturas e relatórios locais ficam em `.e2e/frontend-rebuild`, `.e2e/frontend-live`, `.e2e/frontend-workflows` e `.e2e/performance`. A pasta é ignorada pelo Git porque pode conter logs do ambiente e evidências transitórias.

## Execução local

Frontend: `npm run dev -- --host 0.0.0.0`, dentro de `frontend`. Backend: `.venv\\Scripts\\python.exe main.py`, com `DATABASE_URL` apontando para PostgreSQL dedicado. Neste ambiente, a interface está em `http://localhost:5173/login` e a documentação da API em `http://localhost:9000/docs`.

## Limites de conclusão

O escopo de reconstrução e validação local do frontend está concluído sem regressão conhecida introduzida. Isso não equivale a homologação comercial ou produção. Permanecem gates externos: testes assistivos manuais e zoom/teclado virtual em dispositivos reais, Web Vitals de campo no percentil 75, matriz completa de navegadores, carga prolongada de logs/tabelas, assinatura do agente Windows e aceite operacional em ambiente homologado. Operações reais de RPA continuam exigindo autorização específica.
