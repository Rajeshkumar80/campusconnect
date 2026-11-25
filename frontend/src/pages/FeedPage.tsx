// Feed Page - FR-16: posts from accepted connections, newest first.
// Composer supports one photo or video per post.

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ImagePlus, Inbox, Sparkles, UserPlus, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Avatar } from '../components/ui/Avatar';
import { Button } from '../components/ui/Button';
import { PageHeader } from '../components/ui/PageHeader';
import { Modal } from '../components/ui/Modal';
import { Composer } from '../components/feed/Composer';
import { PostCard } from '../components/feed/PostCard';
import type { Connection, ConnectionRequest, FeedPost, Suggestion } from '../types';

export function FeedPage() {
  const { user } = useAuth();
  const { error: showError, success: showSuccess } = useToastHelpers();

  const [posts, setPosts] = useState<FeedPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [composerOpen, setComposerOpen] = useState(false);
  const [deletingPostId, setDeletingPostId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [connections, setConnections] = useState<Connection[]>([]);
  const [incoming, setIncoming] = useState<ConnectionRequest[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  const loadFeed = useCallback(async () => {
    try {
      setPosts(await api.getFeed(30));
    } catch (err) {
      showError('Could not load the feed', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setIsLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadFeed();
    api.getConnections().then(setConnections).catch(() => setConnections([]));
    api.getIncomingRequests().then(setIncoming).catch(() => setIncoming([]));
    api.getSuggestions(3).then(setSuggestions).catch(() => setSuggestions([]));
  }, [loadFeed]);

  const removePost = async () => {
    if (!deletingPostId) return;
    setIsDeleting(true);
    try {
      await api.deletePost(deletingPostId);
      setPosts((current) => current.filter((post) => post.post_id !== deletingPostId));
      showSuccess('Post deleted', 'The post and its attachment are gone');
    } catch (err) {
      showError('Could not delete', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setIsDeleting(false);
      setDeletingPostId(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Chanakya University · Community"
        title="Campus feed"
        description="Notes, projects and moments from the people you are connected to."
        actions={
          <Button variant="primary" leftIcon={<ImagePlus className="h-4 w-4" />} onClick={() => setComposerOpen(true)}>
            New post
          </Button>
        }
      />

      <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0">
          <div className="mt-6 space-y-5" role="feed" aria-label="Posts feed">
            {isLoading ? (
              Array.from({ length: 3 }).map((_, index) => (
                <div key={index} className="card p-5 sm:p-6">
                  <div className="flex gap-3.5">
                    <div className="skeleton h-10 w-10 rounded-full" />
                    <div className="flex-1 space-y-2.5">
                      <div className="skeleton h-3.5 w-32" />
                      <div className="skeleton h-3 w-full" />
                      <div className="skeleton h-3 w-4/5" />
                    </div>
                  </div>
                </div>
              ))
            ) : posts.length === 0 ? (
              <EmptyFeed onCompose={() => setComposerOpen(true)} hasConnections={connections.length > 0} />
            ) : (
              posts.map((post) => (
                <PostCard
                  key={post.post_id}
                  post={post}
                  currentUserId={user?.user_id}
                  onDelete={() => setDeletingPostId(post.post_id)}
                />
              ))
            )}
          </div>
        </div>

        <aside className="hidden space-y-5 xl:block">
          <section className="card p-5">
            <p className="eyebrow">Your circle</p>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Link to="/connections" className="rounded-xl bg-surface-sunken p-3 transition-colors hover:bg-brand-light">
                <span className="font-display text-2xl font-semibold text-text">{connections.length}</span>
                <span className="mt-1 block text-caption text-text-muted">Connections</span>
              </Link>
              <Link to="/connections" className="rounded-xl bg-surface-sunken p-3 transition-colors hover:bg-accent-light">
                <span className="font-display text-2xl font-semibold text-text">{incoming.length}</span>
                <span className="mt-1 block text-caption text-text-muted">Requests</span>
              </Link>
            </div>
            <Link to="/discover" className="mt-4 inline-flex items-center gap-1.5 text-body-sm font-semibold text-brand hover:text-brand-hover">
              Discover people <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          </section>

          <section className="card p-5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" aria-hidden="true" />
              <p className="eyebrow">People you may know</p>
            </div>
            {suggestions.length === 0 ? (
              <p className="mt-3 text-body-sm text-text-muted">
                No suggestions right now — your circle already covers the campus graph.
              </p>
            ) : (
              <ul className="mt-4 space-y-4">
                {suggestions.map((person) => (
                  <li key={person.user_id}>
                    <Link to={`/profile/${person.user_id}`} className="group flex items-center gap-3">
                      <Avatar name={person.name} size="sm" />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-body-sm font-semibold text-text group-hover:text-brand">
                          {person.name}
                        </span>
                        <span className="block truncate text-caption text-text-muted">
                          {person.mutual_count > 0
                            ? `${person.mutual_count} mutual ${person.mutual_count === 1 ? 'connection' : 'connections'}`
                            : person.programme}
                        </span>
                      </span>
                      <UserPlus className="h-4 w-4 flex-shrink-0 text-text-muted" aria-hidden="true" />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <p className="px-1 text-caption leading-relaxed text-text-muted">
            Your feed only includes accepted connections. Requests and suggestions never leak into it.
          </p>
        </aside>
      </div>

      <Composer
        isOpen={composerOpen}
        onClose={() => setComposerOpen(false)}
        authorName={user?.profile?.name}
        onCreated={(post) =>
          setPosts((current) => [
            { ...post, author_name: user?.profile?.name, author_username: user?.username },
            ...current,
          ])
        }
      />

      <Modal
        isOpen={Boolean(deletingPostId)}
        onClose={() => setDeletingPostId(null)}
        title="Delete this post?"
        description="The text and any attached photo or video are removed permanently."
        size="sm"
      >
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={() => setDeletingPostId(null)}>
            Keep it
          </Button>
          <Button variant="danger" onClick={removePost} loading={isDeleting}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}

function EmptyFeed({ onCompose, hasConnections }: { onCompose: () => void; hasConnections: boolean }) {
  return (
    <div className="card px-6 py-14 text-center">
      <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand-light text-brand">
        {hasConnections ? <Inbox className="h-6 w-6" aria-hidden="true" /> : <Users className="h-6 w-6" aria-hidden="true" />}
      </span>
      <h2 className="mt-5 font-display text-heading-lg font-semibold text-text">
        {hasConnections ? 'Quiet in here' : 'Your feed starts with people'}
      </h2>
      <p className="mx-auto mt-2 max-w-sm text-body-md text-text-muted">
        {hasConnections
          ? 'Your connections have not posted yet. Start the conversation yourself.'
          : 'Connect with classmates to see their posts here. Your own posts stay on your profile.'}
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        <Button variant="primary" onClick={onCompose}>
          Write the first post
        </Button>
        {!hasConnections && (
          <Link to="/discover" className="btn btn-secondary btn-md">
            Find classmates
          </Link>
        )}
      </div>
    </div>
  );
}
