import { useId } from "react";
import { Link } from "react-router-dom";
import { cn } from "../../lib/utils";

const FOLDED_CARD_CLIP_PATH =
  "polygon(0 8px, 8px 0, calc(100% - 40px) 0, 100% 40px, 100% calc(100% - 8px), calc(100% - 8px) 100%, 8px 100%, 0 calc(100% - 8px))";

function FoldedCard({ className, style, ...props }) {
  return (
    <div
      className={cn("relative mx-auto max-w-sm", className)}
      data-slot="folded-card"
      style={{ clipPath: FOLDED_CARD_CLIP_PATH, ...style }}
      {...props}
    />
  );
}

function FoldedCardFold({ className, ...props }) {
  const gradientId = useId().replace(/[^a-zA-Z0-9_-]/g, "");

  return (
    <div
      className={cn(
        "pointer-events-none absolute top-0 right-0 z-30 h-10 w-10",
        className
      )}
      data-slot="folded-card-fold"
      {...props}
    >
      <svg
        aria-hidden="true"
        className="h-full w-full"
        fill="none"
        focusable="false"
        viewBox="0 0 40 40"
      >
        <defs>
          <linearGradient id={gradientId} x1="100%" x2="0%" y1="0%" y2="100%">
            <stop offset="0%" stopColor="var(--card)" />
            <stop offset="40%" stopColor="var(--muted)" />
            <stop offset="100%" stopColor="var(--accent)" />
          </linearGradient>
        </defs>
        <path d="M0 0 L40 40 L40 0 Z" fill={`url(#${gradientId})`} />
        <line
          stroke="var(--border)"
          strokeWidth="1"
          x1="0"
          x2="40"
          y1="0"
          y2="40"
        />
        <path
          d="M36 18 L36 4 L22 4"
          fill="none"
          stroke="var(--border)"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="1"
        />
      </svg>
      <div className="absolute inset-0 border-b border-l bg-muted" />
    </div>
  );
}

function FoldedCardLink({ className, style, ...props }) {
  return (
    <Link
      className={cn(
        "group relative block overflow-hidden bg-card no-underline transition-shadow hover:shadow-lg",
        className
      )}
      data-slot="folded-card-link"
      style={{ clipPath: FOLDED_CARD_CLIP_PATH, ...style }}
      {...props}
    />
  );
}

function FoldedCardBorder({ className, style, ...props }) {
  return (
    <div
      className={cn(
        "pointer-events-none absolute inset-0 z-20 rounded-b-xl rounded-tl-xl",
        className
      )}
      data-slot="folded-card-border"
      style={{
        clipPath: FOLDED_CARD_CLIP_PATH,
        background: "var(--border)",
        padding: "1px",
        WebkitMask:
          "linear-gradient(#000,#000) content-box, linear-gradient(#000,#000)",
        WebkitMaskComposite: "xor",
        maskComposite: "exclude",
        ...style,
      }}
      {...props}
    />
  );
}

function FoldedCardPreview({ className, ...props }) {
  return (
    <div
      className={cn(
        "relative h-[228px] overflow-hidden rounded-b-xl rounded-tl-xl bg-muted/40",
        className
      )}
      data-slot="folded-card-preview"
      {...props}
    />
  );
}

function FoldedCardGrid({ className, rows = 4, columns = 4, ...props }) {
  const rowCount = Math.max(1, Math.floor(rows));
  const columnCount = Math.max(1, Math.floor(columns));

  return (
    <div
      className={cn("absolute inset-0", className)}
      data-slot="folded-card-grid"
      {...props}
    >
      {Array.from({ length: rowCount - 1 }, (_, index) => (
        <hr
          className="absolute w-full border border-t border-dashed border-border/30"
          key={`row-${index + 1}`}
          style={{ top: `${((index + 1) / rowCount) * 100}%` }}
        />
      ))}

      {Array.from({ length: columnCount - 1 }, (_, index) => (
        <hr
          className="absolute h-full border border-l border-dashed border-border/30"
          key={`column-${index + 1}`}
          style={{ left: `${((index + 1) / columnCount) * 100}%` }}
        />
      ))}
    </div>
  );
}

function FoldedCardFooter({ className, ...props }) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 border-t border-border bg-card px-4 py-3",
        className
      )}
      data-slot="folded-card-footer"
      {...props}
    />
  );
}

function FoldedCardHeading({ className, ...props }) {
  return (
    <div
      className={cn("flex items-center gap-2", className)}
      data-slot="folded-card-heading"
      {...props}
    />
  );
}

function FoldedCardTitle({ className, ...props }) {
  return (
    <h3
      className={cn("text-sm font-medium text-foreground", className)}
      data-slot="folded-card-title"
      {...props}
    />
  );
}

function FoldedCardBadge({ className, ...props }) {
  return (
    <span
      className={cn(
        "rounded-full bg-primary px-2 py-0.5 text-xs font-medium text-primary-foreground",
        className
      )}
      data-slot="folded-card-badge"
      {...props}
    />
  );
}

function FoldedCardDescription({ className, ...props }) {
  return (
    <p
      className={cn(
        "line-clamp-3 text-sm leading-relaxed text-muted-foreground",
        className
      )}
      data-slot="folded-card-description"
      {...props}
    />
  );
}

export {
  FoldedCard,
  FoldedCardFold,
  FoldedCardLink,
  FoldedCardBorder,
  FoldedCardPreview,
  FoldedCardGrid,
  FoldedCardFooter,
  FoldedCardHeading,
  FoldedCardTitle,
  FoldedCardBadge,
  FoldedCardDescription,
};