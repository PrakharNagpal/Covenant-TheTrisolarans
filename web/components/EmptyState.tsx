type EmptyStateProps = {
  icon: string;
  title: string;
  subtitle: string;
};

export function EmptyState({ icon, title, subtitle }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[var(--radius-lg)] border-[1.5px] border-[#E8E8F0] bg-white px-6 py-5 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-[var(--violet-lt)] text-xl">
        {icon}
      </span>
      <h2 className="mt-2.5 text-base font-extrabold text-[var(--ink)]">{title}</h2>
      <p className="mt-1.5 max-w-sm text-sm font-medium leading-6 text-[var(--ink-3)]">
        {subtitle}
      </p>
    </div>
  );
}
