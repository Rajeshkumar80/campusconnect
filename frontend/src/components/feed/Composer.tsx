// Create-post dialog: text plus one photo or video. The preview uses an object
// URL and is revoked when the dialog closes or the file changes.

import { useEffect, useRef, useState } from 'react';
import { Film, ImagePlus, X } from 'lucide-react';
import { api } from '../../lib/api';
import { useToastHelpers } from '../ui/Toast';
import { Button } from '../ui/Button';
import { Textarea } from '../ui/Input';
import { Modal } from '../ui/Modal';
import { Avatar } from '../ui/Avatar';
import { MediaPreview } from './PostMedia';
import type { Post } from '../../types';

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/quicktime'];
const IMAGE_LIMIT = 10 * 1024 * 1024;
const VIDEO_LIMIT = 50 * 1024 * 1024;

function validateFile(file: File): string | null {
  if (IMAGE_TYPES.includes(file.type)) {
    return file.size > IMAGE_LIMIT ? 'Images must be 10 MB or smaller.' : null;
  }
  if (VIDEO_TYPES.includes(file.type)) {
    return file.size > VIDEO_LIMIT ? 'Videos must be 50 MB or smaller.' : null;
  }
  return 'Choose a JPG, PNG, GIF, WebP, MP4, WebM or MOV file.';
}

export function Composer({
  isOpen,
  onClose,
  authorName,
  onCreated,
}: {
  isOpen: boolean;
  onClose: () => void;
  authorName?: string;
  onCreated: (post: Post) => void;
}) {
  const { error: showError, success: showSuccess } = useToastHelpers();
  const inputRef = useRef<HTMLInputElement>(null);

  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState<'image' | 'video' | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dragging, setDragging] = useState(false);

  // Revoke the previous object URL whenever it changes or the dialog unmounts.
  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const reset = () => {
    setText('');
    setFile(null);
    setKind(null);
    setIsSubmitting(false);
  };

  const close = () => {
    if (isSubmitting) return;
    reset();
    onClose();
  };

  const pickFile = (next: File | null) => {
    if (!next) return;
    const problem = validateFile(next);
    if (problem) {
      showError('Attachment not added', problem);
      return;
    }
    setFile(next);
    setKind(IMAGE_TYPES.includes(next.type) ? 'image' : 'video');
  };

  const submit = async () => {
    if (!text.trim() && !file) return;
    setIsSubmitting(true);
    try {
      const post = await api.createPost(text.trim(), file ?? undefined);
      onCreated(post);
      showSuccess('Posted', file ? 'Your post and attachment are live' : 'Your post is live');
      reset();
      onClose();
    } catch (err) {
      showError('Could not publish', err instanceof Error ? err.message : 'Please try again');
      setIsSubmitting(false);
    }
  };

  const canPost = Boolean(text.trim() || file) && !isSubmitting;

  return (
    <Modal isOpen={isOpen} onClose={close} title="Share something" size="lg">
      <div className="flex flex-col h-[65vh] max-h-[90vh]">
        <div className="flex-shrink-0 flex items-center gap-3 p-4 border-b border-border">
          <Avatar name={authorName} size="md" />
          <div>
            <p className="text-body-sm font-semibold text-text">{authorName || 'You'}</p>
            <p className="text-caption text-text-muted">Visible to your accepted connections</p>
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0 overflow-hidden p-4">
          <div className="flex-1 min-h-0 flex flex-col">
            <Textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === ' ') {
                  event.stopPropagation();
                }
              }}
              placeholder="A project, a question, a moment from campus…"
              maxLength={5000}
              autoFocus
              className="flex-1 min-h-[120px] resize-none"
            />
          </div>

          {file && (
            <div className="mt-3 flex-shrink-0">
              <MediaPreview url={preview!} kind={kind!} name={file.name} onRemove={() => setFile(null)} />
            </div>
          )}

          {!file && (
            <div className="mt-3 flex-shrink-0">
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                onDragOver={(event) => {
                  event.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(event) => {
                  event.preventDefault();
                  setDragging(false);
                  pickFile(event.dataTransfer.files?.[0] ?? null);
                }}
                className={`flex w-full items-center justify-center gap-2 rounded-xl border border-dashed px-4 py-4 text-body-sm font-medium transition-colors ${
                  dragging
                    ? 'border-brand bg-brand-light text-brand'
                    : 'border-border bg-surface-sunken text-text-muted hover:border-brand/50 hover:text-brand'
                }`}
              >
                <ImagePlus className="h-4 w-4" aria-hidden="true" />
                {dragging ? 'Drop it here' : 'Add a photo or video'}
                <span className="text-caption font-normal">(image ≤ 10 MB, video ≤ 50 MB)</span>
              </button>
            </div>
          )}

          {file && (
            <div className="mt-2 flex-shrink-0 flex items-center gap-2 text-caption text-text-muted">
              {kind === 'video' ? (
                <Film className="h-3.5 w-3.5" aria-hidden="true" />
              ) : (
                <ImagePlus className="h-3.5 w-3.5" aria-hidden="true" />
              )}
              <span className="min-w-0 flex-1 truncate">{file.name}</span>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="inline-flex items-center gap-1 rounded-full px-2 py-1 hover:bg-surface-sunken hover:text-text"
              >
                <X className="h-3 w-3" aria-hidden="true" /> Remove
              </button>
            </div>
          )}

          <input
            ref={inputRef}
            type="file"
            accept={[...IMAGE_TYPES, ...VIDEO_TYPES].join(',')}
            className="hidden"
            onChange={(event) => {
              pickFile(event.target.files?.[0] ?? null);
              event.target.value = '';
            }}
          />
        </div>

        <div className="flex-shrink-0 border-t border-border px-4 py-3 bg-surface/50 backdrop-blur-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="text-caption text-text-muted">{text.length}/5000</span>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={close} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="primary" onClick={submit} loading={isSubmitting} disabled={!canPost}>
                {isSubmitting ? 'Publishing…' : 'Publish'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}
