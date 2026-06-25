"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/backtests", label: "Backtests" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Navegação principal"
      className="border-b border-slate-800 bg-slate-950 px-4 py-3"
    >
      <div className="mx-auto flex max-w-7xl items-center gap-6">
        <span className="text-sm font-semibold tracking-tight text-teal-400">
          Stock Intelligence
        </span>
        <ul role="list" className="flex gap-1">
          {LINKS.map(({ href, label }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`rounded px-3 py-1.5 text-sm transition-colors ${
                    active
                      ? "bg-slate-800 text-slate-100"
                      : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                  }`}
                >
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
