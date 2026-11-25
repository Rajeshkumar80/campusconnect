// Shared page heading used across the signed-in screens.

import type { ReactNode } from 'react';

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
        <h1 className="font-display text-display-sm font-semibold tracking-tight text-text">{title}</h1>
        {description && <p className="mt-1.5 max-w-xl body-md text-text-muted">{description}</p>}
      </div>
      {actions}
    </header>
  );
}
