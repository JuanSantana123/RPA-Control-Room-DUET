import {
  Bold,
  Code2,
  Image as ImageIcon,
  Italic,
  Link2,
  Paperclip,
  Trash2,
} from "lucide-react";
import { useRef, useState, type KeyboardEvent } from "react";
import type { CardCommentAttachment } from "../../types/development";
import { Button, IconButton } from "./Button";
import { TextAreaField } from "./TextAreaField";
import { TextField } from "./TextField";

type InsertMode = "link" | "image" | null;

interface RichTextEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  busy?: boolean;
  uploading?: boolean;
  attachments: CardCommentAttachment[];
  onUploadImage: (file: File) => void | Promise<void>;
  onRemoveAttachment: (attachmentId: number) => void | Promise<void>;
  onSubmit: () => void | Promise<void>;
}

function isSafeWebUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}

export function RichTextEditor({
  value,
  onChange,
  disabled = false,
  busy = false,
  uploading = false,
  attachments,
  onUploadImage,
  onRemoveAttachment,
  onSubmit,
}: RichTextEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [insertMode, setInsertMode] = useState<InsertMode>(null);
  const [linkLabel, setLinkLabel] = useState("");
  const [linkUrl, setLinkUrl] = useState("");
  const [insertError, setInsertError] = useState("");

  const wrapSelection = (before: string, after = before, fallback = "texto") => {
    const input = textareaRef.current;
    if (!input) return;
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const selected = value.slice(start, end) || fallback;
    const next = `${value.slice(0, start)}${before}${selected}${after}${value.slice(end)}`;
    onChange(next.slice(0, 5000));
    requestAnimationFrame(() => {
      input.focus();
      input.setSelectionRange(start + before.length, start + before.length + selected.length);
    });
  };

  const openInsert = (mode: Exclude<InsertMode, null>) => {
    const input = textareaRef.current;
    const selected = input ? value.slice(input.selectionStart, input.selectionEnd) : "";
    setLinkLabel(selected);
    setLinkUrl("");
    setInsertError("");
    setInsertMode((current) => current === mode ? null : mode);
  };

  const insertLink = () => {
    const url = linkUrl.trim();
    if (!isSafeWebUrl(url)) {
      setInsertError("Informe uma URL completa iniciada por http:// ou https://.");
      return;
    }
    const label = linkLabel.trim() || (insertMode === "image" ? "Imagem" : url);
    const snippet = insertMode === "image" ? `![${label}](${url})` : `[${label}](${url})`;
    const separator = value && !value.endsWith(" ") && !value.endsWith("\n") ? " " : "";
    onChange(`${value}${separator}${snippet}`.slice(0, 5000));
    setInsertMode(null);
    setLinkLabel("");
    setLinkUrl("");
    setInsertError("");
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && value.trim() && !busy) {
      event.preventDefault();
      void onSubmit();
    }
  };

  return (
    <div className="rich-text-editor">
      <div className="rich-text-editor__toolbar" role="toolbar" aria-label="Formatação do comentário">
        <IconButton label="Negrito" tooltip="Negrito" size="sm" icon={<Bold />} disabled={disabled} onClick={() => wrapSelection("**")} />
        <IconButton label="Itálico" tooltip="Itálico" size="sm" icon={<Italic />} disabled={disabled} onClick={() => wrapSelection("*")} />
        <IconButton label="Código" tooltip="Código" size="sm" icon={<Code2 />} disabled={disabled} onClick={() => wrapSelection("`")} />
        <span className="rich-text-editor__divider" aria-hidden="true" />
        <IconButton label="Inserir link" tooltip="Inserir link" size="sm" icon={<Link2 />} disabled={disabled} aria-pressed={insertMode === "link"} onClick={() => openInsert("link")} />
        <IconButton label="Inserir imagem por URL" tooltip="Imagem por URL" size="sm" icon={<ImageIcon />} disabled={disabled} aria-pressed={insertMode === "image"} onClick={() => openInsert("image")} />
        <IconButton label="Anexar imagem" tooltip="Anexar imagem (máx. 5 MB)" size="sm" busy={uploading} icon={<Paperclip />} disabled={disabled || attachments.length >= 5} onClick={() => fileRef.current?.click()} />
        <input
          ref={fileRef}
          className="sr-only"
          type="file"
          aria-label="Selecionar imagem para anexar"
          accept="image/png,image/jpeg,image/gif,image/webp"
          tabIndex={-1}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void onUploadImage(file);
            event.target.value = "";
          }}
        />
        <span className="rich-text-editor__hint">Markdown simples</span>
      </div>

      {insertMode && (
        <div className="rich-text-editor__insert" role="group" aria-label={insertMode === "image" ? "Inserir imagem por URL" : "Inserir link"}>
          <TextField
            label={insertMode === "image" ? "Descrição da imagem" : "Texto do link"}
            value={linkLabel}
            placeholder={insertMode === "image" ? "Ex.: Fluxo aprovado" : "Ex.: Documentação"}
            onChange={(event) => setLinkLabel(event.target.value)}
          />
          <TextField
            label="URL"
            type="url"
            value={linkUrl}
            placeholder="https://..."
            error={insertError || undefined}
            onChange={(event) => { setLinkUrl(event.target.value); setInsertError(""); }}
          />
          <div className="rich-text-editor__insert-actions">
            <Button size="sm" variant="ghost" onClick={() => setInsertMode(null)}>Cancelar</Button>
            <Button size="sm" onClick={insertLink}>Inserir</Button>
          </div>
        </div>
      )}

      <TextAreaField
        ref={textareaRef}
        id="card-new-comment"
        label="Novo comentário"
        labelHidden
        value={value}
        rows={4}
        maxLength={5000}
        placeholder={disabled ? "Você não possui permissão para comentar." : "Compartilhe uma atualização, decisão ou link com o time..."}
        disabled={disabled || busy}
        counter={`${value.length}/5000`}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
      />

      {attachments.length > 0 && (
        <div className="rich-text-editor__attachments" aria-label="Imagens anexadas">
          {attachments.map((attachment) => (
            <div key={attachment.id} className="rich-text-editor__attachment">
              <ImageIcon size={15} aria-hidden="true" />
              <span title={attachment.name}>{attachment.name}</span>
              <small>{Math.max(1, Math.round(attachment.size_bytes / 1024))} KB</small>
              <IconButton
                label={`Remover ${attachment.name}`}
                size="sm"
                variant="ghost"
                icon={<Trash2 />}
                onClick={() => void onRemoveAttachment(attachment.id)}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
