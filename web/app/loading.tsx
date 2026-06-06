// Lane: P3 frontend
export default function LedgerLoading() {
  return (
    <main className="app-page px-6 py-8 sm:px-10">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-8">
        <div className="border-b border-[var(--border)] pb-7">
          <div className="skeleton h-4 w-24 rounded" />
          <div className="skeleton mt-4 h-10 w-72 rounded" />
          <div className="skeleton mt-4 h-5 w-full max-w-xl rounded" />
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              className="panel h-24 rounded-lg"
              key={index}
            />
          ))}
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              className="panel h-56 rounded-lg"
              key={index}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
