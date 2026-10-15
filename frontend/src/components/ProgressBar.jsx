export default function ProgressBar({ value }) {
  return (
    <div className="h-2 w-full rounded-full bg-muted">
      <div
        className={`h-2 rounded-full ${value > 80 ? "bg-white" : "bg-primary"}`}
        style={{ width: `${value}%` }}
      />
    </div>
  );
}