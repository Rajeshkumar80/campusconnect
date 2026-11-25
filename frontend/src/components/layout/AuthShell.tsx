// Split-screen shell for the public auth pages. The left panel carries the
// product story; the right side holds the form.

import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { GraduationCap } from 'lucide-react';

const facts = [
  { title: 'Degrees of separation', body: 'BFS finds how close you are to anyone on campus.' },
  { title: 'Prefix search', body: 'A trie autocompletes names and usernames as you type.' },
  { title: 'A feed you chose', body: 'Only posts from accepted connections, merged newest first.' },
];

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-surface lg:grid lg:grid-cols-[1.05fr_1fr]">
      <aside className="relative hidden overflow-hidden bg-brand-light p-12 lg:flex lg:flex-col">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.08]"
          style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '22px 22px' }}
          aria-hidden="true"
        />
        <div className="relative z-10 flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-accent text-white">
            <GraduationCap className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="font-display text-heading-sm font-semibold text-text">CampusConnect</p>
            <p className="text-[0.625rem] font-semibold uppercase tracking-[0.2em] text-text-muted">
              Chanakya University
            </p>
          </div>
        </div>

        <div className="relative z-10 my-auto max-w-lg py-16">
          <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.22em] text-accent">
            The campus, mapped
          </p>
          <h1 className="mt-5 font-display text-[3.4rem] font-semibold leading-[1.03] tracking-tight text-text">
            Every classmate is a few edges away.
          </h1>
          <p className="mt-5 max-w-md text-body-lg leading-relaxed text-text-muted">
            A student network built on real data structures: graphs, BFS, tries and heaps under the hood.
          </p>

          <dl className="mt-10 space-y-5">
            {facts.map((fact) => (
              <div key={fact.title} className="border-l border-accent/40 pl-4">
                <dt className="text-body-sm font-semibold text-text">{fact.title}</dt>
                <dd className="mt-0.5 text-body-sm text-text-muted">{fact.body}</dd>
              </div>
            ))}
          </dl>
        </div>

        <p className="relative z-10 text-caption text-text-muted">
          DSA mini-project · Flask · React · MongoDB
        </p>
      </aside>

      <main className="flex min-h-screen flex-col justify-center px-5 py-12 sm:px-10">
        <div className="mx-auto w-full max-w-md">
          <Link to="/" className="mb-10 flex items-center gap-2.5 lg:hidden">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand text-surface">
              <GraduationCap className="h-4 w-4" aria-hidden="true" />
            </span>
            <span className="font-display text-heading-sm font-semibold text-text">CampusConnect</span>
          </Link>

          <p className="eyebrow">Chanakya University</p>
          <h2 className="mt-2 font-display text-display-sm font-semibold tracking-tight text-text">{title}</h2>
          <p className="mt-2 text-body-md text-text-muted">{subtitle}</p>

          <div className="mt-8">{children}</div>
          <div className="mt-6 text-body-sm text-text-muted">{footer}</div>
        </div>
      </main>
    </div>
  );
}
