import { EllipsisVertical, type LucideIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { IconButton } from "./Button";

export interface ActionMenuItem {
  label: string;
  icon: LucideIcon;
  onSelect: () => void;
  tone?: "neutral" | "danger";
  disabled?: boolean;
  /** Shown on hover, e.g. why the item is disabled. */
  title?: string;
}

const MENU_GAP = 4;
// Roughly four items; past this from the bottom the menu opens upwards.
const MENU_HEIGHT_ESTIMATE = 180;

type MenuPosition = { right: number } & ({ top: number } | { bottom: number });

/**
 * A ⋮ button with a dropdown of actions. The menu is positioned against the
 * viewport so a scrolling table does not clip it.
 */
export function ActionMenu({
  items,
  label = "Thao tác",
}: {
  items: ActionMenuItem[];
  label?: string;
}) {
  const [position, setPosition] = useState<MenuPosition | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const isOpen = position !== null;

  useEffect(() => {
    if (!isOpen) return;

    const close = () => setPosition(null);
    const handlePointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        !menuRef.current?.contains(target) &&
        !buttonRef.current?.contains(target)
      ) {
        close();
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        close();
        buttonRef.current?.focus();
      }
    };

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    // A fixed menu would drift away from its button.
    window.addEventListener("scroll", close, true);
    window.addEventListener("resize", close);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("scroll", close, true);
      window.removeEventListener("resize", close);
    };
  }, [isOpen]);

  const toggle = () => {
    if (isOpen || !buttonRef.current) {
      setPosition(null);
      return;
    }

    const rect = buttonRef.current.getBoundingClientRect();
    const right = window.innerWidth - rect.right;
    const opensUp = rect.bottom + MENU_HEIGHT_ESTIMATE > window.innerHeight;

    setPosition(
      opensUp
        ? { right, bottom: window.innerHeight - rect.top + MENU_GAP }
        : { right, top: rect.bottom + MENU_GAP },
    );
  };

  return (
    <>
      <IconButton
        ref={buttonRef}
        onClick={toggle}
        title={label}
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        className={isOpen ? "bg-slate-100 text-slate-900" : ""}
      >
        <EllipsisVertical className="h-4 w-4" />
      </IconButton>

      {position && (
        <div
          ref={menuRef}
          role="menu"
          style={position}
          className="fixed z-40 min-w-48 rounded-md border border-slate-200 bg-white py-1 shadow-lg"
        >
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              disabled={item.disabled}
              title={item.title}
              onClick={() => {
                setPosition(null);
                item.onSelect();
              }}
              className={`flex w-full items-center gap-2 px-3 py-1.5 text-left text-sm disabled:opacity-50 ${
                item.tone === "danger"
                  ? "text-red-600 enabled:hover:bg-red-50"
                  : "text-slate-700 enabled:hover:bg-slate-100"
              }`}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </button>
          ))}
        </div>
      )}
    </>
  );
}
