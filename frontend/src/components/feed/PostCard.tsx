// A single feed card: author row, media, and LinkedIn-style like / comment /
// share actions. Comments load on demand; sharing sends the post into a
// connection's message thread.

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import {
  Loader2,
  MessageCircle,
  MoreHorizontal,
  Send,
  Share2,
  ThumbsUp,
  Trash2,
} from 'lucide-react';
import { Avatar } from '../ui/Avatar';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { useToastHelpers } from '../ui/Toast';
import { PostMedia } from './PostMedia';
import { api } from '../../lib/api';
import type { Comment, Connection, FeedPost } from '../../types';

function timeAgo(seconds: number) {
  try {
    return formatDistanceToNow(new Date(seconds * 1000), { addSuffix: true });
  } catch {
    return 'Just now';
  }
}

function formatLikers(
  likers: Array<{ user_id: string; name: string; username: string }>,
  total: number,
  likedByMe: boolean
) {
  if (!likers.length) return `${total} like${total === 1 ? '' : 's'}`;
  const names = likers.map((l) => l.name);
  const meIndex = likedByMe ? names.indexOf('You') : -1;
  // If current user is in likers but not in the first few, add "You" at start
  if (likedByMe && meIndex === -1 && names.length > 0) {
    names.unshift('You');
  }
  if (names.length === 1) {
    return `${names[0]} ${total === 1 ? 'likes' : 'like'} this`;
  }
  if (names.length === 2) {
    return `${names[0]} and ${names[1]} ${total === 2 ? 'like' : 'like'} this`;
  }
  return `${names[0]}, ${names[1]} and ${total - 2} other${total - 2 === 1 ? '' : 's'} like this`;
}

export function PostCard({
  post,
  currentUserId,
  onDelete,
}: {
  post: FeedPost;
  currentUserId?: string;
  onDelete: () => void;
}) {
  const { error: showError, success: showSuccess } = useToastHelpers();
  const [menuOpen, setMenuOpen] = useState(false);
  const isOwnPost = post.author_id === currentUserId;

  const [liked, setLiked] = useState(Boolean(post.liked_by_me));
  const [likeCount, setLikeCount] = useState(post.like_count ?? 0);
  const [commentCount, setCommentCount] = useState(post.comment_count ?? 0);

  const [commentsOpen, setCommentsOpen] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [postingComment, setPostingComment] = useState(false);

  const [shareOpen, setShareOpen] = useState(false);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [shareNote, setShareNote] = useState('');
  const [sharing, setSharing] = useState(false);

  const toggleLike = async () => {
    const next = !liked;
    setLiked(next);
    setLikeCount((count) => Math.max(0, count + (next ? 1 : -1)));
    try {
      const result = await api.toggleLike(post.post_id);
      setLiked(result.liked);
      setLikeCount(result.like_count);
    } catch (err) {
      setLiked(!next);
      setLikeCount((count) => Math.max(0, count + (next ? -1 : 1)));
      showError('Could not update like', err instanceof Error ? err.message : 'Try again');
    }
  };

  const openComments = useCallback(async () => {
    setCommentsOpen((open) => !open);
    if (comments.length || commentsLoading) return;
    setCommentsLoading(true);
    try {
      setComments(await api.getComments(post.post_id));
    } catch {
      showError('Could not load comments', 'Please try again');
    } finally {
      setCommentsLoading(false);
    }
  }, [comments.length, commentsLoading, post.post_id, showError]);

  const submitComment = async () => {
    const text = commentText.trim();
    if (!text) return;
    setPostingComment(true);
    try {
      const comment = await api.addComment(post.post_id, text);
      setComments((current) => [...current, comment]);
      setCommentCount((count) => count + 1);
      setCommentText('');
    } catch (err) {
      showError('Could not comment', err instanceof Error ? err.message : 'Try again');
    } finally {
      setPostingComment(false);
    }
  };

  useEffect(() => {
    if (!shareOpen) return;
    api
      .getConnections()
      .then(setConnections)
      .catch(() => showError('Could not load connections', 'Please try again'));
  }, [shareOpen, showError]);

  const toggleRecipient = (userId: string) => {
    setSelectedIds((current) =>
      current.includes(userId)
        ? current.filter((id) => id !== userId)
        : [...current, userId]
    );
  };

  const submitShare = async () => {
    if (!selectedIds.length) return;
    setSharing(true);
    try {
      const sent = await api.sharePost(post.post_id, selectedIds, shareNote.trim());
      showSuccess('Post shared', `Sent to ${sent} connection${sent === 1 ? '' : 's'}`);
      setShareOpen(false);
      setSelectedIds([]);
      setShareNote('');
    } catch (err) {
      showError('Could not share', err instanceof Error ? err.message : 'Try again');
    } finally {
      setSharing(false);
    }
  };

  return (
    <article className="card p-5 sm:p-6">
      <div className="flex items-start gap-3.5">
        <Link to={`/profile/${post.author_id}`} className="flex-shrink-0" aria-label={`${post.author_name} profile`}>
          <Avatar name={post.author_name} size="md" />
        </Link>

        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <Link
                to={`/profile/${post.author_id}`}
                className="block truncate font-semibold text-text hover:text-brand transition-colors"
              >
                {post.author_name || post.author_username}
              </Link>
              <p className="mt-0.5 text-caption text-text-muted">
                @{post.author_username}
                <span aria-hidden="true"> · </span>
                <time dateTime={new Date(post.created_at * 1000).toISOString()}>
                  {timeAgo(post.created_at)}
                </time>
              </p>
            </div>

            {isOwnPost && (
              <div className="relative flex-shrink-0">
                <button
                  type="button"
                  onClick={() => setMenuOpen((open) => !open)}
                  className="rounded-full p-1.5 text-text-muted transition-colors hover:bg-surface-sunken hover:text-text"
                  aria-label="Post options"
                  aria-expanded={menuOpen}
                >
                  <MoreHorizontal className="h-5 w-5" aria-hidden="true" />
                </button>
                {menuOpen && (
                  <>
                    <button
                      type="button"
                      className="fixed inset-0 z-10 cursor-default"
                      onClick={() => setMenuOpen(false)}
                      aria-label="Close post options"
                      tabIndex={-1}
                    />
                    <div className="absolute right-0 top-full z-20 mt-1 w-40 overflow-hidden rounded-xl border border-border bg-surface-elevated py-1 shadow-lift">
                      <button
                        type="button"
                        onClick={() => {
                          setMenuOpen(false);
                          onDelete();
                        }}
                        className="flex w-full items-center gap-2 px-3.5 py-2.5 text-left text-body-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                      >
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                        Delete post
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {post.text && (
            <p className="mt-3 whitespace-pre-wrap text-body-md leading-relaxed text-text">{post.text}</p>
          )}
          {post.media && <PostMedia media={post.media} />}

          {(likeCount > 0 || commentCount > 0) && (
            <div className="mt-3 flex flex-col gap-2">
              {likeCount > 0 && (
                <button
                  type="button"
                  onClick={openComments}
                  className="flex items-center gap-1.5 text-caption font-semibold text-text hover:text-brand transition-colors"
                >
                  <ThumbsUp className={`h-3.5 w-3.5 ${liked ? 'fill-current text-brand' : 'text-text-muted'}`} aria-hidden="true" />
                  {formatLikers(post.likers || [], likeCount, liked)}
                </button>
              )}
              {commentCount > 0 && (
                <button
                  type="button"
                  onClick={openComments}
                  className="flex items-center gap-1.5 text-caption text-text-muted hover:text-brand hover:underline"
                >
                  <MessageCircle className="h-3.5 w-3.5" aria-hidden="true" />
                  {commentCount} comment{commentCount === 1 ? '' : 's'}
                </button>
              )}
            </div>
          )}

          <div className="mt-3 flex items-center justify-between gap-1 border-t border-border pt-2">
            <button
              type="button"
              onClick={toggleLike}
              aria-pressed={liked}
              className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-body-sm font-semibold transition-colors ${
                liked ? 'text-brand' : 'text-text-muted hover:bg-surface-sunken hover:text-text'
              }`}
            >
              <ThumbsUp className={`h-4 w-4 ${liked ? 'fill-current' : ''}`} aria-hidden="true" />
              Like
            </button>
            <button
              type="button"
              onClick={openComments}
              className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-body-sm font-semibold text-text-muted transition-colors hover:bg-surface-sunken hover:text-text"
            >
              <MessageCircle className="h-4 w-4" aria-hidden="true" />
              Comment
            </button>
            <button
              type="button"
              onClick={() => setShareOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-body-sm font-semibold text-text-muted transition-colors hover:bg-surface-sunken hover:text-text"
            >
              <Share2 className="h-4 w-4" aria-hidden="true" />
              Share
            </button>
          </div>

          {commentsOpen && (
            <div className="mt-2 space-y-3 border-t border-border pt-3">
              {commentsLoading ? (
                <p className="flex items-center gap-2 text-caption text-text-muted">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> Loading comments…
                </p>
              ) : (
                comments.map((comment) => (
                  <div key={comment.comment_id} className="flex items-start gap-2.5">
                    <Avatar name={comment.author_name} size="sm" />
                    <div className="min-w-0 flex-1 rounded-xl bg-surface-sunken px-3 py-2">
                      <p className="text-caption font-semibold text-text">
                        {comment.author_name}{' '}
                        <span className="font-normal text-text-muted">
                          · {timeAgo(comment.created_at)}
                        </span>
                      </p>
                      <p className="whitespace-pre-wrap text-body-sm text-text">{comment.text}</p>
                    </div>
                  </div>
                ))
              )}
              <div className="flex items-start gap-2.5">
                <Avatar name="You" size="sm" />
                <input
                  value={commentText}
                  onChange={(event) => setCommentText(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === ' ') {
                      event.stopPropagation();
                    }
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      submitComment();
                    }
                  }}
                  placeholder="Write a comment…"
                  maxLength={1000}
                  className="input py-2 text-body-sm"
                  aria-label="Write a comment"
                />
                <Button
                  size="sm"
                  onClick={submitComment}
                  loading={postingComment}
                  disabled={!commentText.trim()}
                  aria-label="Post comment"
                >
                  <Send className="h-3.5 w-3.5" aria-hidden="true" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={shareOpen}
        onClose={() => setShareOpen(false)}
        title="Share post"
        description="Send this post to a connection's messages."
        size="md"
      >
        <div className="space-y-4">
          {connections.length === 0 ? (
            <p className="text-body-sm text-text-muted">
              You need an accepted connection before you can share a post.
            </p>
          ) : (
            <div className="max-h-56 space-y-1 overflow-y-auto">
              {connections.map((connection) => (
                <label
                  key={connection.user_id}
                  className="flex cursor-pointer items-center gap-3 rounded-xl px-2 py-2 hover:bg-surface-sunken"
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(connection.user_id)}
                    onChange={() => toggleRecipient(connection.user_id)}
                    className="h-4 w-4 rounded border-border text-brand focus:ring-brand"
                  />
                  <Avatar name={connection.name} size="sm" />
                  <span className="min-w-0 flex-1 truncate text-body-sm font-medium text-text">
                    {connection.name}
                  </span>
                </label>
              ))}
            </div>
          )}
          <input
            value={shareNote}
            onChange={(event) => setShareNote(event.target.value)}
            placeholder="Add a note (optional)"
            maxLength={500}
            className="input text-body-sm"
            aria-label="Share note"
          />
          <div className="flex justify-end gap-2 border-t border-border pt-3">
            <Button variant="secondary" onClick={() => setShareOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitShare} loading={sharing} disabled={!selectedIds.length}>
              Send
            </Button>
          </div>
        </div>
      </Modal>
    </article>
  );
}
