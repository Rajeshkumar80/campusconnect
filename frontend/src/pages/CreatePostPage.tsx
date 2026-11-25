// Create Post Page - dedicated page for composing new posts

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, ImagePlus, X, ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Textarea } from '../components/ui/Input';
import { Avatar } from '../components/ui/Avatar';
import { MediaPreview } from '../components/feed/PostMedia';
import { PageHeader } from '../components/ui/PageHeader';
import { useAuth } from '../context/AuthContext';

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

export function CreatePostPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { error: showError, success: showSuccess } = useToastHelpers();
  const inputRef = useRef<HTMLInputElement>(null);

  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState<'image' | 'video' | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

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
      await api.createPost(text.trim(), file ?? undefined);
      showSuccess('Posted', file ? 'Your post and attachment are live' : 'Your post is live');
      navigate('/', { replace: true });
    } catch (err) {
      showError('Could not publish', err instanceof Error ? err.message : 'Please try again');
      setIsSubmitting(false);
    }
  };

  const canPost = Boolean(text.trim() || file) && !isSubmitting;

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Chanakya University · Community"
        title="New post"
        description="Share a note, project, or moment with your connections."
        actions={
          <Button variant="ghost" leftIcon={<ArrowLeft className="h-4 w-4" />} onClick={() => navigate('/')}>
            Back to feed
          </Button>
        }
      />

      <div className="mt-8 space-y-6">
        <div className="card p-6">
          <div className="flex items-start gap-4">
            <Avatar name={user?.profile?.name} size="lg" />
            <div className="flex-1 min-w-0">
              <p className="text-body-sm font-semibold text-text">{user?.profile?.name || 'You'}</p>
              <p className="text-caption text-text-muted">Visible to your accepted connections</p>
            </div>
          </div>

          <Textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event: React.KeyboardEvent) => {
              if (event.key === ' ') {
                event.stopPropagation();
              }
            }}
            placeholder="A project, a question, a moment from campus…"
            maxLength={5000}
            autoFocus
            className="mt-6 resize-none min-h-[160px]"
          />

          {file && preview && kind && (
            <div className="mt-4">
              <MediaPreview url={preview} kind={kind} name={file.name} onRemove={() => setFile(null)} />
            </div>
          )}

          {!file && (
            <div className="mt-4">
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

          {file && (
            <div className="mt-3 flex items-center gap-2 text-caption text-text-muted">
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

          <div className="mt-6 border-t border-border pt-4 flex items-center justify-between">
            <span className="text-caption text-text-muted">{text.length}/5000</span>
            <div className="flex gap-3">
              <Button variant="secondary" onClick={() => navigate('/')} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="primary" onClick={submit} loading={isSubmitting} disabled={!canPost}>
                {isSubmitting ? 'Publishing…' : 'Publish'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}