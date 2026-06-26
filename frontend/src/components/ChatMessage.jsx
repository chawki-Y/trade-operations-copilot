import React from "react";
import { Bot, ChevronDown, Code2, TriangleAlert, UserRound } from "lucide-react";

function ResultTable({ columns, rows }) {
  if (!rows?.length) {
    return null;
  }

  return (
    <div className="w-full overflow-hidden rounded-md border border-white/10">
      <div className="max-h-80 overflow-auto">
        <table className="min-w-max divide-y divide-white/10 text-sm">
          <thead className="sticky top-0 bg-neutral-900">
            <tr>
              {columns.map((column) => (
                <th key={column} className="whitespace-nowrap px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-neutral-400">
                  {column.replaceAll("_", " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10 bg-neutral-950/70">
            {rows.map((row, index) => (
              <tr key={index} className="hover:bg-white/[0.03]">
                {columns.map((column) => (
                  <td key={column} className="whitespace-nowrap px-3 py-2 text-neutral-200">
                    {String(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ChatMessage({ message }) {
  const isUser = message.role === "user";
  const isError = message.type === "error";
  const generatedSql = message.generatedSql || message.generated_sql || message.sql;
  const rows = message.rows || [];
  const columns = message.columns || [];
  const shouldShowResults = rows.length > 0 && columns.length > 0;
  const shouldShowSql = Boolean(generatedSql);

  return (
    <article className={`flex w-full min-w-0 gap-0 sm:gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="mt-1 hidden h-9 w-9 shrink-0 place-items-center rounded-md bg-emerald-400 text-neutral-950 sm:grid">
          <Bot size={19} aria-hidden="true" />
        </div>
      )}

      <div
        className={`min-w-0 overflow-hidden ${
          isUser ? "order-first max-w-[min(85%,56rem)]" : "max-w-4xl flex-1"
        }`}
      >
        <div
          className={
            isUser
              ? "rounded-md bg-emerald-300 px-4 py-3 text-sm font-medium text-neutral-950"
              : `overflow-hidden rounded-md border p-4 text-neutral-100 shadow-glow ${
                  isError ? "border-rose-400/40 bg-rose-950/40" : "border-white/10 bg-neutral-900/95"
                }`
          }
        >
          <p className="flex min-w-0 items-start gap-2 text-sm leading-6">
            {isError && <TriangleAlert className="mt-0.5 shrink-0 text-rose-300" size={16} aria-hidden="true" />}
            <span className="min-w-0 break-words">{message.content}</span>
          </p>

          {!isUser && message.intent && (
            <span className="mt-3 inline-flex rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[11px] font-medium uppercase tracking-wide text-neutral-400">
              {message.intent.replaceAll("_", " ")}
            </span>
          )}

          {(shouldShowSql || shouldShowResults) && (
            <div className="mt-4 space-y-4">
              {shouldShowSql && (
                <details className="group rounded-md border border-white/10 bg-neutral-950">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-sm font-medium text-neutral-200">
                    <span className="flex items-center gap-2">
                      <Code2 size={16} aria-hidden="true" />
                      Generated SQL
                    </span>
                    <ChevronDown className="transition group-open:rotate-180" size={16} aria-hidden="true" />
                  </summary>
                  <pre className="overflow-x-auto border-t border-white/10 p-3 text-xs leading-5 text-emerald-200">
                    <code>{generatedSql}</code>
                  </pre>
                </details>
              )}

              {shouldShowResults && (
                <div className="min-w-0">
                  <ResultTable columns={columns} rows={rows} />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="mt-1 hidden h-9 w-9 shrink-0 place-items-center rounded-md border border-emerald-200/40 bg-neutral-900 text-emerald-200 sm:grid">
          <UserRound size={18} aria-hidden="true" />
        </div>
      )}
    </article>
  );
}
