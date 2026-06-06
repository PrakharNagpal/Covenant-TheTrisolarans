// Lane: P3 frontend
export default function LedgerLoading() {
  return (
    <main className="min-h-screen bg-[#F1EFE8] px-6 py-8 text-[#1B1A22] sm:px-10">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-8">
        <div className="border-b border-[#D8D2C4] pb-7">
          <div className="h-4 w-24 rounded bg-[#D8D2C4]" />
          <div className="mt-4 h-10 w-72 rounded bg-[#D8D2C4]" />
          <div className="mt-4 h-5 w-full max-w-xl rounded bg-[#E5DFD0]" />
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              className="h-24 animate-pulse rounded-lg border border-[#D8D2C4] bg-white"
              key={index}
            />
          ))}
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              className="h-56 animate-pulse rounded-lg border border-[#D8D2C4] bg-white"
              key={index}
            />
          ))}
        </div>
      </section>
    </main>
  );
}
