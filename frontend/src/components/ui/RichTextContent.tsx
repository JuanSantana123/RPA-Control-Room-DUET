import { useEffect, useState, type ReactNode } from "react";
import type { CardCommentAttachment } from "../../types/development";
import api from "../../services/api";

function safeWebUrl(value: string): string | null {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

function renderInline(value: string): ReactNode[] {
  const pattern = /(!?\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  return value.split(pattern).filter(Boolean).map((part, index) => {
    const image = part.match(/^!\[([^\]]+)\]\(([^)]+)\)$/);
    if (image) {
      const url = safeWebUrl(image[2] ?? "");
      return url ? <img className="rich-text-content__external-image" key={index} src={url} alt={image[1] ?? "Imagem"} loading="lazy" referrerPolicy="no-referrer" /> : part;
    }
    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) {
      const url = safeWebUrl(link[2] ?? "");
      return url ? <a key={index} href={url} target="_blank" rel="noopener noreferrer">{link[1] ?? url}</a> : part;
    }
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
    if (part.startsWith("*") && part.endsWith("*")) return <em key={index}>{part.slice(1, -1)}</em>;
    return part;
  });
}

function ProtectedAttachmentImage({ projectId, attachment }: { projectId: number; attachment: CardCommentAttachment }) {
  const [source, setSource] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;
    api.get(
      `/development/projects/${projectId}/comment-attachments/${attachment.id}`,
      { responseType: "blob" },
    ).then((response) => {
      if (!active) return;
      objectUrl = URL.createObjectURL(response.data);
      setSource(objectUrl);
    }).catch(() => {
      if (active) setSource(null);
    });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attachment.id, projectId]);

  return (
    <figure className="rich-text-content__attachment">
      {source ? <img src={source} alt={attachment.name} loading="lazy" /> : <div aria-label={`Não foi possível carregar ${attachment.name}`} />}
      <figcaption>{attachment.name}</figcaption>
    </figure>
  );
}

export function RichTextContent({ content, projectId, attachments = [] }: { content: string; projectId: number; attachments?: CardCommentAttachment[] }) {
  return (
    <div className="rich-text-content">
      {content.split(/\r?\n/).map((line, index) => <p key={index}>{line ? renderInline(line) : <br />}</p>)}
      {attachments.length > 0 && (
        <div className="rich-text-content__attachments">
          {attachments.map((attachment) => <ProtectedAttachmentImage key={attachment.id} projectId={projectId} attachment={attachment} />)}
        </div>
      )}
    </div>
  );
}
