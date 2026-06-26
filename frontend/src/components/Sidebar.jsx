import React from "react";
import { Clock3, Landmark, MessageSquareText, Search } from "lucide-react";

export function Sidebar({ history, examples, onExampleClick }) {
  return (
    <aside className="flex h-full w-full flex-col border-r border-white/10 bg-neutral-950/95 lg:w-80">
      <div className="border-b border-white/10 p-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-emerald-400 text-neutral-950">
            <Landmark size={21} aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white">Markets Copilot</h1>
            <p className="text-xs text-neutral-400">Trade lifecycle analytics</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <section>
          <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-neutral-500">
            <Search size={14} aria-hidden="true" />
            Examples
          </div>
          <div className="space-y-2">
            {examples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => onExampleClick(example)}
                className="w-full rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-left text-sm text-neutral-200 transition hover:border-emerald-300/40 hover:bg-emerald-300/10 focus:outline-none focus:ring-2 focus:ring-emerald-300"
              >
                {example}
              </button>
            ))}
          </div>
        </section>

        <section className="mt-7">
          <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-neutral-500">
            <Clock3 size={14} aria-hidden="true" />
            Query History
          </div>
          <div className="space-y-2">
            {history.length === 0 ? (
              <div className="rounded-md border border-dashed border-white/10 px-3 py-4 text-sm text-neutral-500">
                No saved queries yet.
              </div>
            ) : (
              history.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onExampleClick(item.question)}
                  className="w-full rounded-md border border-white/10 bg-neutral-900/80 px-3 py-2 text-left transition hover:border-cyan-300/40 hover:bg-cyan-300/10 focus:outline-none focus:ring-2 focus:ring-cyan-300"
                >
                  <div className="flex items-start gap-2">
                    <MessageSquareText className="mt-0.5 shrink-0 text-cyan-300" size={15} aria-hidden="true" />
                    <div className="min-w-0">
                      <p className="line-clamp-2 text-sm text-neutral-100">{item.question}</p>
                      <p className="mt-1 text-xs text-neutral-500">
                        {item.intent ? `${item.intent.replaceAll("_", " ")} · ` : ""}
                        {item.row_count} rows
                      </p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </section>
      </div>
    </aside>
  );
}
