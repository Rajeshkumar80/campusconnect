// Renders a post's photo or video. Photos open in an in-page lightbox so the
// viewer stays inside the app. Falls back to a quiet notice if the file cannot
// be loaded (deleted file, expired session, unsupported codec).

import { useState } from 'react';
import { Film, ImageOff, X } from 'lucide-react';
import { mediaSrc } from '../../lib/api';
import type { PostMedia } from '../../types';

export function PostMedia({ media }: { media: PostMedia }) {
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState(false);

  if (failed) {
    return (
      <div className="mt-3 flex items-center gap-2 rounded-xl border border-border bg-surface-sunken px-4 py-3 text-body-sm text-text-muted">
        <ImageOff className="h-4 w-4" aria-hidden="true" />
        This attachment could not be loaded.
      </div>
    );
  }

  if (media.type === 'video') {
    return (
      <video
        className="mt-3 w-full rounded-xl border border-border bg-black"
        controls
        preload="metadata"
        playsInline
        aria-label={media.name}
        onError={() => setFailed(true)}
        crossOrigin="use-credentials"
      >
        <source src={mediaSrc(media.url)} type={media.mime} />
      </video>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 block w-full overflow-hidden rounded-xl border border-border bg-surface-sunken text-left"
        aria-label={`Open ${media.name || 'photo'} full size`}
      >
        <img
          src={mediaSrc(media.url)}
          alt={media.name || 'Post attachment'}
          className="max-h-[520px] w-full object-cover transition-transform duration-300 hover:scale-[1.01]"
          loading="lazy"
          onError={() => setFailed(true)}
          crossOrigin="use-credentials"
        />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/85 p-4"
          role="dialog"
          aria-modal="true"
          aria-label={media.name || 'Photo'}
          onClick={() => setOpen(false)}
        >
          <button
            type="button"
            className="absolute right-5 top-5 rounded-full bg-white/15 p-2 text-white hover:bg-white/25"
            aria-label="Close photo"
            onClick={() => setOpen(false)}
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
          <img
            src={mediaSrc(media.url)}
            alt={media.name || 'Post attachment'}
            className="max-h-[88vh] max-w-full rounded-lg object-contain"
            crossOrigin="use-credentials"
            onClick={(event) => event.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}

/** Small composer preview used before the post is published. */
export function MediaPreview({
  url,
  kind,
  name,
  onRemove,
}: {
  url: string;
  kind: 'image' | 'video';
  name: string;
  onRemove: () => void;
}) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-surface-sunken">
      {kind === 'video' ? (
        <video src={url} className="max-h-48 w-full object-cover" controls playsInline />
      ) : (
        <img src={url} alt={name} className="max-h-48 w-full object-cover" />
      )}
      <div className="absolute inset-x-0 bottom-0 flex items-center gap-2 bg-black/55 px-3 py-2 text-white backdrop-blur-sm">
        <Film className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
        <span className="min-w-0 flex-1 truncate text-caption">{name}</span>
        <button
          type="button"
          onClick={onRemove}
          className="rounded-full px-2 py-1 text-caption font-semibold hover:bg-white/20"
        >
          Remove
        </button>
      </div>
    </div>
  );
}
