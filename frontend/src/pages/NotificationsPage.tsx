// Notifications - likes, comments and connection requests aimed at you.

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { Bell, Heart, MessageCircle, UserPlus } from 'lucide-react';
import { api } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Avatar } from '../components/ui/Avatar';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import type { NotificationItem } from '../types';

const icons = {
  like: Heart,
  comment: MessageCircle,
  connection_request: UserPlus,
};

const labels = {
  like: 'Like',
  comment: 'Comment',
  connection_request: 'Connection request',
};

export function NotificationsPage() {
  const { error: showError } = useToastHelpers();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications();
      setItems(data.notifications);
      await api.markNotificationsRead();
      window.dispatchEvent(new CustomEvent('notifications:read'));
    } catch (err) {
      showError('Could not load notifications', err instanceof Error ? err.message : 'Try again');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Activity"
        title="Notifications"
        description="Likes, comments and connection requests from your campus network."
      />

      <div className="mt-8 space-y-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="card flex items-center gap-4 p-4">
              <div className="skeleton h-10 w-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="skeleton h-3.5 w-48" />
                <div className="skeleton h-3 w-32" />
              </div>
            </div>
          ))
        ) : items.length === 0 ? (
          <Card className="p-10 text-center">
            <Bell className="mx-auto mb-4 h-10 w-10 text-text-muted" aria-hidden="true" />
            <h2 className="heading-md mb-1">Nothing yet</h2>
            <p className="body-sm text-text-muted">
              When someone likes or comments on your posts, it shows up here.
            </p>
          </Card>
        ) : (
          items.map((item) => {
            const Icon = icons[item.type];
            return (
              <article key={`${item.type}-${item.id}`} className="card flex items-start gap-4 p-4">
                <Link to={`/profile/${item.actor.user_id}`} className="flex-shrink-0">
                  <Avatar name={item.actor.name} size="md" />
                </Link>
                <div className="min-w-0 flex-1">
                  <p className="text-body-sm text-text">
                    <Link
                      to={`/profile/${item.actor.user_id}`}
                      className="font-semibold hover:text-brand"
                    >
                      {item.actor.name}
                    </Link>{' '}
                    {item.text}
                  </p>
                  {item.post_text && (
                    <p className="mt-1 truncate rounded-lg bg-surface-sunken px-2.5 py-1.5 text-caption text-text-muted">
                      “{item.post_text}”
                    </p>
                  )}
                  <p className="mt-1 text-caption text-text-muted">
                    {formatDistanceToNow(new Date(item.created_at * 1000), { addSuffix: true })}
                  </p>
                </div>
                <span className="flex flex-shrink-0 items-center gap-1 rounded-full bg-surface-sunken px-2.5 py-1 text-[0.625rem] font-semibold uppercase tracking-wide text-text-muted">
                  <Icon className="h-3 w-3" aria-hidden="true" />
                  {labels[item.type]}
                </span>
              </article>
            );
          })
        )}
      </div>
    </div>
  );
}
