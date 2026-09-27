import { LockKeyhole } from "lucide-react";

interface AccessModeBadgeProps {
    label?: string;
    title?: string;
}

export default function AccessModeBadge({
    label = "Somente leitura",
    title = "Você pode consultar estes dados, mas não possui permissão para alterá-los.",
}: AccessModeBadgeProps) {
    return (
        <span className="access-mode-badge" title={title}>
            <LockKeyhole size={12} strokeWidth={2} aria-hidden="true" />
            {label}
        </span>
    );
}
