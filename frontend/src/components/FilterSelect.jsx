export default function FilterSelect({ value, onChange, options, label }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label={label}
      className="h-9 rounded-md border border-border bg-card px-3 text-sm capitalize outline-none focus:border-primary"
    >
      {options.map((o) => (
        <option key={o} value={o}>
          {o === "all" ? `All ${label}` : o}
        </option>
      ))}
    </select>
  );
}