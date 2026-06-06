// Lane: P3 frontend
export default function ArchaeologyLoading() {
  return (
    <main className="app-page px-6 py-8 sm:px-10">
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <div className="border-b border-[var(--border)] pb-7">
          <div className="skeleton h-4 w-32 rounded" />
          <div className="skeleton mt-4 h-10 w-80 rounded" />
        </div>
        <div className="flex gap-2">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              className="skeleton h-10 w-44 rounded-full"
              key={index}
            />
          ))}
        </div>
        <div className="panel min-h-[420px] rounded-lg" />
      </section>
    </main>
  );
}
