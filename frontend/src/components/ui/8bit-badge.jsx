import { cn } from "../../lib/utils";

const variants = {
  success: { box: "border-primary bg-accent/40 text-primary", bar: "bg-primary" },
  danger: { box: "border-red-500 bg-red-500/10 text-red-400", bar: "bg-red-500" },
  critical: { box: "border-red-500 bg-red-500 text-white", bar: "bg-red-500" },
  warning: { box: "border-white bg-white/10 text-white", bar: "bg-white" },
  muted: {
    box: "border-muted-foreground/50 bg-muted text-muted-foreground",
    bar: "bg-muted-foreground/50",
  },
};

export function Badge({ children, className, variant = "success", ...props }) {
  const v = variants[variant] ?? variants.muted;

  return (
    <div className={cn("relative mx-[3px] inline-flex items-stretch", className)}>
      <span
        {...props}
        className={cn(
          "inline-flex items-center border-y-[3px] px-2 py-0.5 font-pixel-square text-[11px] uppercase leading-none tracking-wide",
          v.box
        )}
      >
        {children}
      </span>
      {/* Left and right pixel bars */}
      <span className={cn("absolute -left-[3px] inset-y-[3px] w-[3px]", v.bar)} />
      <span className={cn("absolute -right-[3px] inset-y-[3px] w-[3px]", v.bar)} />
    </div>
  );
}

export default Badge;