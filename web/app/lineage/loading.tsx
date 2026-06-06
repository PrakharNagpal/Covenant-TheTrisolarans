// Lane: P3 frontend
export default function LineageLoading() {
  return (
    <main className="min-h-screen bg-[#F1EFE8] px-6 py-8 text-[#1B1A22] sm:px-10">
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-8">
        <div className="border-b border-[#D8D2C4] pb-7">
          <div className="h-4 w-28 rounded bg-[#D8D2C4]" />
          <div className="mt-4 h-10 w-full max-w-3xl rounded bg-[#D8D2C4]" />
        </div>
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <div className="h-56 animate-pulse rounded-lg border border-[#D8D2C4] bg-white" />
          <div className="h-56 animate-pulse rounded-lg border border-[#D8D2C4] bg-white" />
        </div>
        <div className="h-72 animate-pulse rounded-lg border border-[#D8D2C4] bg-white" />
      </section>
    </main>
  );
}
