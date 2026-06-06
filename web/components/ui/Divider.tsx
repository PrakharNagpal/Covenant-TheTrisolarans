export function Divider() {
  return (
    <div
      aria-hidden="true"
      className="h-px w-full"
      style={{
        background:
          "linear-gradient(90deg, transparent, var(--violet), var(--mint), transparent)",
      }}
    />
  );
}
