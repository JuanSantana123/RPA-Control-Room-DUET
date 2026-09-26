import { MessageSquare, MessageSquarePlus } from "lucide-react";

import type { CardComment } from "../../../types/development";
import { parseApiDateTime } from "../../../utils/dateTime";
import { Button } from "../../ui/Button";
import { PanelSkeleton } from "../../ui/Skeletons";
import { TextAreaField } from "../../ui/TextAreaField";

interface CardCommentsSectionProps {
  comments: CardComment[];
  loading: boolean;
  canEdit: boolean;
  addingComment: boolean;
  newComment: string;
  onNewCommentChange: (value: string) => void;
  onAddComment: () => void | Promise<void>;
}

export default function CardCommentsSection({
  comments,
  loading,
  canEdit,
  addingComment,
  newComment,
  onNewCommentChange,
  onAddComment,
}: CardCommentsSectionProps) {
  const draftLength = newComment.length;

  return (
    <section className="card-details-section card-details-comments" aria-labelledby="card-comments-title">
      <header className="card-comments-header">
        <div className="card-comments-heading">
          <span className="card-comments-heading__icon" aria-hidden="true"><MessageSquare size={16} /></span>
          <div>
            <h3 id="card-comments-title">Comentários</h3>
            <p>Contexto e decisões registradas nesta demanda.</p>
          </div>
        </div>
        <span className="card-comments-count" aria-label={`${comments.length} comentários`}>{comments.length}</span>
      </header>

      {loading ? <PanelSkeleton lines={3} /> : comments.length === 0 ? (
        <div className="card-comments-empty">
          <MessageSquare size={20} aria-hidden="true" />
          <strong>Comece o histórico desta demanda</strong>
          <span>Registre uma decisão, dependência ou informação útil para o time.</span>
        </div>
      ) : (
        <div className="card-comments-list">
          {comments.map((comment) => (
            <article className="card-comment" key={comment.id}>
              <header>
                <span className="card-comment__avatar" aria-hidden="true">
                  {(comment.user_name || `U${comment.user_id}`).trim().charAt(0).toLocaleUpperCase("pt-BR")}
                </span>
                <div><strong>{comment.user_name || `Usuário #${comment.user_id}`}</strong>
                  <time dateTime={comment.created_at || undefined}>
                    {comment.created_at ? parseApiDateTime(comment.created_at)?.toLocaleString("pt-BR") || "" : ""}
                  </time>
                </div>
              </header>
              <p>{comment.content}</p>
            </article>
          ))}
        </div>
      )}

      <div className="card-comment-composer">
        <TextAreaField
          id="card-new-comment"
          label="Novo comentário"
          labelHidden
          value={newComment}
          rows={3}
          placeholder={canEdit ? "Compartilhe uma atualização com o time..." : "Você não possui permissão para comentar."}
          disabled={!canEdit || addingComment}
          counter={draftLength ? `${draftLength} caracteres` : undefined}
          onChange={(event) => onNewCommentChange(event.target.value)}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && newComment.trim() && canEdit && !addingComment) {
              event.preventDefault();
              void onAddComment();
            }
          }}
        />
        <div className="card-comment-composer__actions">
          <span>{newComment.trim() ? "Ctrl + Enter para enviar" : "Escreva uma mensagem para habilitar o envio"}</span>
          <Button variant="primary" busy={addingComment} loadingLabel="Adicionando comentário"
            disabled={!canEdit || !newComment.trim()} onClick={() => void onAddComment()}>
            <MessageSquarePlus size={15} aria-hidden="true" />Adicionar comentário
          </Button>
        </div>
      </div>
    </section>
  );
}
