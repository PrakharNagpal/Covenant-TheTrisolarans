// Lane: P3 frontend
export default function ArchaeologyLoading() {
  return (
    <main className="min-h-screen bg-[#F1EFE8] px-6 py-8 text-[#1B1A22] sm:px-10">
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <div className="border-b border-[#D8D2C4] pb-7">
          <div className="h-4 w-32 rounded bg-[#D8D2C4]" />
          <div className="mt-4 h-10 w-80 rounded bg-[#D8D2C4]" />
        </div>
        <div className="flex gap-2">
          {Array.from({ length: 3 }).map((_, index) => (
            <div
              className="h-10 w-44 animate-pulse rounded-full bg-white"
              key={index}
            />
          ))}
        </div>
        <div className="min-h-[420px] animate-pulse rounded-lg border border-[#D8D2C4] bg-white" />
      </section>
    </main>
  );
}
