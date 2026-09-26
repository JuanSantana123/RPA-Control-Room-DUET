import { useState } from "react";
import { ArrowRight, Download, Inbox, Plus, RefreshCw, Search, Trash2, X } from "lucide-react";
import { Button, IconButton } from "../components/ui/Button";
import FeedbackBanner from "../components/ui/FeedbackBanner";
import PremiumSelect from "../components/ui/PremiumSelect";
import { TextField } from "../components/ui/TextField";
import { CardGridSkeleton, TableSkeleton } from "../components/ui/Skeletons";
import { Switch } from "../components/ui/Switch";
import { TextAreaField } from "../components/ui/TextAreaField";
import CardCommentsSection from "../components/development/kanban/CardCommentsSection";
import EmptyState from "../components/ui/EmptyState";
import { useInteraction } from "../context/useInteraction";

export default function ComponentLab() {
  const { confirm, notify } = useInteraction();
  const [selectValue, setSelectValue] = useState("development");
  const [query, setQuery] = useState("");
  const [comment, setComment] = useState("");

  return (
    <div className="page-container component-lab">
      <header className="page-heading">
        <div>
          <div className="page-eyebrow">Catálogo de desenvolvimento</div>
          <h1>Componentes da interface</h1>
          <p>Estados estáticos e interativos sem dados operacionais. Esta rota existe somente no modo de desenvolvimento.</p>
        </div>
      </header>

      <section className="component-lab__section" aria-labelledby="lab-actions">
        <div className="component-lab__heading">
          <div><small>Primitivas</small><h2 id="lab-actions">Ações</h2></div>
          <span>4 variantes · 3 tamanhos · loading e disabled</span>
        </div>
        <div className="component-lab__matrix">
          <Button variant="primary"><Plus aria-hidden="true" />Criar automação</Button>
          <Button><Download aria-hidden="true" />Baixar pacote</Button>
          <Button variant="ghost">Ação discreta<ArrowRight aria-hidden="true" /></Button>
          <Button variant="danger"><Trash2 aria-hidden="true" />Excluir</Button>
          <Button size="sm">Compacto</Button>
          <Button size="lg" variant="primary">Ação destacada</Button>
          <Button variant="primary" busy loadingLabel="Publicando pacote">Publicar pacote</Button>
          <Button disabled>Indisponível</Button>
          <IconButton label="Atualizar dados" tooltip="Atualizar dados" icon={<RefreshCw aria-hidden="true" />} />
        </div>
      </section>

      <section className="component-lab__section" aria-labelledby="lab-fields">
        <div className="component-lab__heading">
          <div><small>Primitivas</small><h2 id="lab-fields">Campos e seleção</h2></div>
          <span>label, descrição, erro, ícone, disabled e conteúdo longo</span>
        </div>
        <div className="component-lab__fields">
          <TextField label="Nome do projeto" description="Utilize um nome reconhecível pela equipe." placeholder="Conciliação financeira" required />
          <TextField
            label="Pesquisar"
            labelHidden
            type="search"
            value={query}
            leadingIcon={<Search aria-hidden="true" />}
            trailingAction={query ? <IconButton label="Limpar pesquisa" size="sm" icon={<X aria-hidden="true" />} onClick={() => setQuery("")} /> : undefined}
            placeholder="Pesquisar componentes..."
            onChange={(event) => setQuery(event.target.value)}
          />
          <TextField label="Porta de comunicação" value="70000" error="Informe uma porta entre 1 e 65535." readOnly />
          <TextField label="Identificador gerenciado" value="AGENT-8F13AB2C" disabled readOnly />
          <TextAreaField label="Descrição da demanda" description="Registre contexto suficiente para a equipe." placeholder="Descreva o resultado esperado..." rows={3} />
          <div className="ui-field">
            <label className="ui-field__label" htmlFor="lab-environment">Ambiente</label>
            <PremiumSelect id="lab-environment" value={selectValue} onChange={(event) => setSelectValue(event.target.value)}>
              <option value="development">Desenvolvimento / Homologação</option>
              <option value="production">Produção</option>
            </PremiumSelect>
          </div>
          <Switch label="Atualização automática" description="Sincronizar dados em segundo plano." defaultChecked />
        </div>
      </section>

      <section className="component-lab__section" aria-labelledby="lab-comments">
        <div className="component-lab__heading">
          <div><small>Domínio</small><h2 id="lab-comments">Colaboração na demanda</h2></div>
          <span>vazio, histórico, rascunho e atalho de teclado</span>
        </div>
        <div className="component-lab__domain-preview">
          <CardCommentsSection
            comments={[{
              id: 1,
              project_id: 10,
              user_id: 1,
              user_name: "Equipe DUET",
              content: "A validação funcional foi concluída. Falta confirmar o arquivo de entrada com a área solicitante.",
              created_at: "2026-09-26T14:30:00Z",
              updated_at: null,
            }]}
            loading={false}
            canEdit
            addingComment={false}
            newComment={comment}
            onNewCommentChange={setComment}
            onAddComment={() => setComment("")}
          />
        </div>
      </section>

      <section className="component-lab__section" aria-labelledby="lab-feedback">
        <div className="component-lab__heading"><div><small>Compostos</small><h2 id="lab-feedback">Feedback e carregamento</h2></div></div>
        <div className="component-lab__feedback">
          <FeedbackBanner tone="info" title="Atualização disponível" message="Há dados mais recentes no servidor." hint="Atualize quando concluir a edição atual." />
          <FeedbackBanner tone="success" title="Configuração salva" message="As alterações já estão disponíveis para a equipe." />
          <FeedbackBanner tone="error" title="Não foi possível publicar" message="O pacote não possui um arquivo de entrada válido." hint="Defina o arquivo principal e tente novamente." action={{ label: "Tentar novamente", onClick: () => undefined }} />
          <EmptyState icon={<Inbox />} title="Nenhum item disponível" description="Novos itens aparecerão nesta área quando forem cadastrados." />
        </div>
        <div className="component-lab__skeletons">
          <CardGridSkeleton count={2} />
          <TableSkeleton columns={3} rows={3} />
        </div>
      </section>

      <section className="component-lab__section" aria-labelledby="lab-interactions">
        <div className="component-lab__heading">
          <div><small>Compostos</small><h2 id="lab-interactions">Confirmações e notificações</h2></div>
          <span>foco contido, teclado, contexto e retorno à ação de origem</span>
        </div>
        <div className="component-lab__matrix">
          <Button
            onClick={() => void confirm({
              title: "Publicar automação?",
              description: "A versão validada ficará disponível para novas execuções.",
              detail: "Execuções já iniciadas continuam usando a versão anterior.",
              confirmLabel: "Publicar versão",
            })}
          >
            Abrir confirmação
          </Button>
          <Button
            variant="danger"
            onClick={() => void confirm({
              title: "Excluir projeto permanentemente?",
              description: "Arquivos, comentários e histórico de desenvolvimento serão removidos.",
              detail: "Digite o nome do projeto para confirmar.",
              confirmLabel: "Excluir projeto",
              tone: "danger",
              requireText: {
                expected: "Conciliação Financeira",
              },
            })}
          >
            Confirmação crítica
          </Button>
          <Button
            variant="ghost"
            onClick={() => notify({
              title: "Sincronização concluída",
              message: "Os dados mais recentes já estão disponíveis.",
              tone: "success",
            })}
          >
            Exibir notificação
          </Button>
        </div>
      </section>
    </div>
  );
}
