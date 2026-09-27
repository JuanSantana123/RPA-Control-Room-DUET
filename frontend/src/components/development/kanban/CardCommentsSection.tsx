import { ArrowRight, GitCommitHorizontal, MessageSquare, MessageSquarePlus } from "lucide-react";

import type { CardComment, CardCommentAttachment } from "../../../types/development";
import { parseApiDateTime } from "../../../utils/dateTime";
import { Button } from "../../ui/Button";
import { PanelSkeleton } from "../../ui/Skeletons";
import { RichTextContent } from "../../ui/RichTextContent";
import { RichTextEditor } from "../../ui/RichTextEditor";

interface CardCommentsSectionProps {
  comments: CardComment[];
  loading: boolean;
  canEdit: boolean;
  addingComment: boolean;
  uploadingAttachment: boolean;
  newComment: string;
  pendingAttachments: CardCommentAttachment[];
  onNewCommentChange: (value: string) => void;
  onAddComment: () => void | Promise<void>;
  onUploadAttachment: (file: File) => void | Promise<void>;
  onRemoveAttachment: (attachmentId: number) => void | Promise<void>;
}

export default function CardCommentsSection({
  comments,
  loading,
  canEdit,
  addingComment,
  uploadingAttachment,
  newComment,
  pendingAttachments,
  onNewCommentChange,
  onAddComment,
  onUploadAttachment,
  onRemoveAttachment,
}: CardCommentsSectionProps) {
  const commentCount = comments.filter((comment) => comment.kind !== "stage_movement").length;
  const movementCount = comments.length - commentCount;

  return (
    <section className="card-details-section card-details-comments" aria-labelledby="card-comments-title">
      <header className="card-comments-header">
        <div className="card-comments-heading">
          <span className="card-comments-heading__icon" aria-hidden="true"><MessageSquare size={16} /></span>
          <div>
            <h3 id="card-comments-title">Atividade e comentários</h3>
            <p>Decisões do time e movimentações auditáveis do workflow.</p>
          </div>
        </div>
        <span className="card-comments-count" aria-label={`${commentCount} comentários e ${movementCount} movimentações`}>{comments.length}</span>
      </header>

      {loading ? <PanelSkeleton lines={3} /> : comments.length === 0 ? (
        <div className="card-comments-empty">
          <MessageSquare size={20} aria-hidden="true" />
          <strong>A atividade desta demanda aparecerá aqui</strong>
          <span>Comentários e mudanças de etapa serão organizados cronologicamente.</span>
        </div>
      ) : (
        <div className="card-comments-list">
          {comments.map((comment) => (
            <article className={`card-comment${comment.kind === "stage_movement" ? " card-comment--movement" : ""}`} key={comment.event_key || `${comment.kind || "comment"}-${comment.id}`}>
              <header>
                <span className="card-comment__avatar" aria-hidden="true">
                  {comment.kind === "stage_movement" ? <GitCommitHorizontal size={15} /> : (comment.user_name || `U${comment.user_id}`).trim().charAt(0).toLocaleUpperCase("pt-BR")}
                </span>
                <div><strong>{comment.user_name || `Usuário #${comment.user_id}`}</strong>
                  <time dateTime={comment.created_at || undefined}>
                    {comment.created_at ? parseApiDateTime(comment.created_at)?.toLocaleString("pt-BR") || "" : ""}
                  </time>
                </div>
              </header>
              {comment.kind === "stage_movement" ? (
                <div className="card-comment__movement">
                  <span>moveu o projeto</span>
                  <strong>{comment.from_stage?.name || "Etapa inicial"}</strong>
                  <ArrowRight size={14} aria-hidden="true" />
                  <strong>{comment.to_stage?.name || "Nova etapa"}</strong>
                </div>
              ) : (
                <RichTextContent
                  content={comment.content || ""}
                  projectId={comment.project_id}
                  attachments={comment.attachments}
                />
              )}
            </article>
          ))}
        </div>
      )}

      <div className="card-comment-composer">
        <RichTextEditor
          value={newComment}
          onChange={onNewCommentChange}
          disabled={!canEdit}
          busy={addingComment}
          uploading={uploadingAttachment}
          attachments={pendingAttachments}
          onUploadImage={onUploadAttachment}
          onRemoveAttachment={onRemoveAttachment}
          onSubmit={onAddComment}
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
