// Lane: P3 frontend
export default function LineageLoading() {
  return (
    <main className="app-page px-6 py-8 sm:px-10">
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8">
        <div className="border-b border-[var(--border)] pb-7">
          <div className="skeleton h-4 w-28 rounded" />
          <div className="skeleton mt-4 h-10 w-full max-w-3xl rounded" />
        </div>
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <div className="panel h-56 rounded-lg" />
          <div className="panel h-56 rounded-lg" />
        </div>
        <div className="panel h-72 rounded-lg" />
      </section>
    </main>
  );
}
