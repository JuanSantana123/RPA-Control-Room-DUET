import {
  Children,
  Fragment,
  isValidElement,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactElement,
  type ReactNode,
  type SelectHTMLAttributes,
} from "react";
import { createPortal } from "react-dom";
import { Check, ChevronDown } from "lucide-react";

type NativeSelectProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "multiple" | "size">;

interface PremiumSelectProps extends NativeSelectProps {
  children: ReactNode;
  placeholder?: string;
}

interface SelectOption {
  value: string;
  label: string;
  disabled: boolean;
}

interface MenuPosition {
  left: number;
  top?: number;
  bottom?: number;
  width: number;
  maxHeight: number;
}

function textFromNode(node: ReactNode): string {
  return Children.toArray(node)
    .map((child) => typeof child === "string" || typeof child === "number" ? String(child) : "")
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

function readOptions(children: ReactNode): SelectOption[] {
  const options: SelectOption[] = [];

  function visit(nodes: ReactNode) {
    Children.forEach(nodes, (child) => {
      if (!isValidElement(child)) return;
      const element = child as ReactElement<{ value?: string | number; disabled?: boolean; children?: ReactNode }>;

      if (element.type === "option") {
        options.push({
          value: String(element.props.value ?? ""),
          label: textFromNode(element.props.children),
          disabled: Boolean(element.props.disabled),
        });
        return;
      }

      if (element.type === Fragment || element.props.children) visit(element.props.children);
    });
  }

  visit(children);
  return options;
}

export default function PremiumSelect({
  children,
  className = "",
  disabled,
  id,
  onChange,
  placeholder,
  value,
  ...nativeProps
}: PremiumSelectProps) {
  const generatedId = useId().replace(/:/g, "");
  const selectId = id ?? `premium-select-${generatedId}`;
  const menuId = `${selectId}-listbox`;
  const nativeRef = useRef<HTMLSelectElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [position, setPosition] = useState<MenuPosition | null>(null);
  const options = useMemo(() => readOptions(children), [children]);
  const selectedValue = String(value ?? "");
  const selectedIndex = options.findIndex((option) => option.value === selectedValue);
  const selectedOption = options[selectedIndex];

  useEffect(() => {
    if (nativeProps["aria-label"]) return;
    const associatedLabel = nativeRef.current?.labels?.[0]?.textContent?.trim();
    if (associatedLabel) triggerRef.current?.setAttribute("aria-label", associatedLabel);
  }, [nativeProps, selectId]);

  useEffect(() => {
    if (!open) return;

    const updatePosition = () => {
      const rect = triggerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const gap = 8;
      const availableBelow = window.innerHeight - rect.bottom - gap - 12;
      const availableAbove = rect.top - gap - 12;
      const openAbove = availableBelow < 220 && availableAbove > availableBelow;
      const maxHeight = Math.max(140, Math.min(320, openAbove ? availableAbove : availableBelow));
      setPosition({
        left: Math.max(12, Math.min(rect.left, window.innerWidth - rect.width - 12)),
        width: Math.min(rect.width, window.innerWidth - 24),
        maxHeight,
        ...(openAbove
          ? { bottom: window.innerHeight - rect.top + gap }
          : { top: rect.bottom + gap }),
      });
    };

    const closeFromOutside = (event: PointerEvent) => {
      const target = event.target as Node;
      if (!triggerRef.current?.contains(target) && !menuRef.current?.contains(target)) setOpen(false);
    };

    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    document.addEventListener("pointerdown", closeFromOutside);
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
      document.removeEventListener("pointerdown", closeFromOutside);
    };
  }, [open]);

  useEffect(() => {
    if (!open || activeIndex < 0) return;
    menuRef.current?.querySelector<HTMLElement>(`[data-option-index="${activeIndex}"]`)?.scrollIntoView({ block: "nearest" });
  }, [activeIndex, open]);

  const moveActive = (direction: 1 | -1) => {
    if (!options.length) return;
    let next = activeIndex >= 0 ? activeIndex : Math.max(selectedIndex, 0);
    for (let attempts = 0; attempts < options.length; attempts += 1) {
      next = (next + direction + options.length) % options.length;
      const nextOption = options[next];
      if (nextOption && !nextOption.disabled) break;
    }
    setActiveIndex(next);
  };

  const choose = (nextValue: string) => {
    const native = nativeRef.current;
    if (!native) return;
    const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value")?.set;
    setter?.call(native, nextValue);
    native.dispatchEvent(new Event("change", { bubbles: true }));
    setOpen(false);
    triggerRef.current?.focus();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!open) {
        setOpen(true);
        setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
      } else moveActive(event.key === "ArrowDown" ? 1 : -1);
    } else if ((event.key === "Enter" || event.key === " ") && open) {
      event.preventDefault();
      const activeOption = options[activeIndex];
      if (activeIndex >= 0 && activeOption && !activeOption.disabled) choose(activeOption.value);
    } else if (event.key === "Escape" && open) {
      event.preventDefault();
      setOpen(false);
    } else if (event.key === "Home" || event.key === "End") {
      if (!open) return;
      event.preventDefault();
      const candidates = options.map((option, index) => ({ option, index })).filter(({ option }) => !option.disabled);
      setActiveIndex(event.key === "Home" ? candidates[0]?.index ?? 0 : candidates.at(-1)?.index ?? 0);
    }
  };

  return (
    <div className={`premium-select ${className}`.trim()} data-open={open || undefined}>
      <select
        {...nativeProps}
        ref={nativeRef}
        id={selectId}
        value={value}
        disabled={disabled}
        className="premium-select__native"
        onChange={onChange}
        tabIndex={-1}
        aria-hidden="true"
        onFocus={() => triggerRef.current?.focus()}
      >
        {children}
      </select>

      <button
        ref={triggerRef}
        type="button"
        className="premium-select__trigger"
        disabled={disabled}
        role="combobox"
        aria-expanded={open}
        aria-controls={menuId}
        aria-haspopup="listbox"
        aria-label={nativeProps["aria-label"] ?? "Selecionar opção"}
        onClick={() => {
          setOpen((current) => !current);
          setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
        }}
        onKeyDown={handleKeyDown}
      >
        <span className={!selectedOption ? "premium-select__placeholder" : undefined}>
          {selectedOption?.label || placeholder || "Selecione"}
        </span>
        <ChevronDown size={16} strokeWidth={1.8} aria-hidden="true" />
      </button>

      {open && position && createPortal(
        <div
          ref={menuRef}
          id={menuId}
          className="premium-select__menu"
          role="listbox"
          aria-label={nativeProps["aria-label"] ?? "Opções"}
          style={{
            left: position.left,
            top: position.top,
            bottom: position.bottom,
            width: position.width,
            maxHeight: position.maxHeight,
          }}
        >
          {options.map((option, index) => (
            <button
              key={`${option.value}-${index}`}
              type="button"
              role="option"
              aria-selected={option.value === selectedValue}
              className="premium-select__option"
              data-active={index === activeIndex || undefined}
              data-option-index={index}
              disabled={option.disabled}
              onPointerMove={() => setActiveIndex(index)}
              onClick={() => choose(option.value)}
            >
              <span>{option.label}</span>
              {option.value === selectedValue && <Check size={16} strokeWidth={2} aria-hidden="true" />}
            </button>
          ))}
        </div>,
        document.body,
      )}
    </div>
  );
}
