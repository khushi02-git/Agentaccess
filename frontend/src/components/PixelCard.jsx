export default function PixelCard({
  label,
  value,
  sub,
  percent,
  danger,
  soft,
  icon: Icon,
  children,
  className = "",
}) {
  return (
    <div
      className={`pixel-card ${danger ? "danger" : ""} ${soft ? "soft" : ""} ${className}`}
    >
      {label && (
        <div className="flex items-center justify-between">
          <p className="pixel-font text-[10px] text-white/60">{label}</p>
          {Icon && <Icon className="h-4 w-4 text-white/60" />}
        </div>
      )}
      {value != null && (
        <p className={`pixel-font mt-4 text-white ${soft ? "text-[16px]" : "text-[24px]"}`}>
          {value}
        </p>
      )}
      {percent != null && (
        <div className="pixel-bar mt-4" style={{ "--w": `${percent}%` }} />
      )}
      {sub && <p className="mt-3 text-sm text-white/60">{sub}</p>}
      {children}
    </div>
  );
}