import { Search, X } from "lucide-react";
import type { InputHTMLAttributes } from "react";
import { IconButton } from "./Button";
import { TextField } from "./TextField";

interface SearchFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "value" | "onChange"> {
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  containerClassName?: string;
  clearLabel?: string;
}

export default function SearchField({
  label,
  value,
  onValueChange,
  containerClassName,
  clearLabel = "Limpar pesquisa",
  ...props
}: SearchFieldProps) {
  return (
    <TextField
      {...props}
      label={label}
      labelHidden
      type="search"
      value={value}
      containerClassName={["ui-search-field", containerClassName].filter(Boolean).join(" ")}
      leadingIcon={<Search size={16} strokeWidth={1.8} />}
      trailingAction={value ? (
        <IconButton
          size="sm"
          label={clearLabel}
          icon={<X size={14} aria-hidden="true" />}
          onClick={() => onValueChange("")}
        />
      ) : undefined}
      onChange={(event) => onValueChange(event.target.value)}
    />
  );
}
