// Network Panel - degree of connection, mutual connections and shortest path.
// All graph results come from the backend; the frontend only renders them.

import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { GitBranch, Users, UserCheck, UserPlus, Clock, Loader2 } from 'lucide-react';
import { api } from '../../lib/api';
import { useToastHelpers } from '../ui/Toast';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Avatar } from '../ui/Avatar';
import { Badge } from '../ui/Badge';
import type { ConnectionDegree, UserSummary } from '../../types';

type LinkState = 'connected' | 'pending' | 'available';

export function NetworkPanel({ targetUserId }: { targetUserId: string }) {
  const { error: showError, success: showSuccess } = useToastHelpers();

  const [degree, setDegree] = useState<ConnectionDegree | null>(null);
  const [mutual, setMutual] = useState<UserSummary[]>([]);
  const [pathNames, setPathNames] = useState<string[]>([]);
  const [linkState, setLinkState] = useState<LinkState>('available');
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [degreeData, mutualData, pathIds, connections, incoming, outgoing] = await Promise.all([
        api.getConnectionDegree(targetUserId),
        api.getMutualConnections(targetUserId),
        api.getShortestPath(targetUserId),
        api.getConnections(),
        api.getIncomingRequests(),
        api.getOutgoingRequests(),
      ]);

      setDegree(degreeData);
      setMutual(mutualData);

      if (pathIds?.length) {
        const users = await Promise.all(pathIds.map((id) => api.getUser(id).catch(() => null)));
        setPathNames(users.map((u, i) => u?.name || pathIds[i]));
      } else {
        setPathNames([]);
      }

      if (connections.some((c) => c.user_id === targetUserId)) {
        setLinkState('connected');
      } else if (
        incoming.some((r) => r.sender_id === targetUserId) ||
        outgoing.some((r) => r.recipient_id === targetUserId)
      ) {
        setLinkState('pending');
      } else {
        setLinkState('available');
      }
    } catch (err) {
      showError('Failed to load network info', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setLoading(false);
    }
  }, [targetUserId, showError]);

  useEffect(() => {
    load();
  }, [load]);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      await api.sendConnectionRequest(targetUserId);
      setLinkState('pending');
      showSuccess('Request sent', 'Your connection request is pending');
    } catch (err) {
      showError('Could not send request', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setConnecting(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6 flex items-center gap-3 text-text-muted body-md">
        <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
        Loading network details...
      </Card>
    );
  }

  return (
    <motion.div
      className="space-y-4"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Card className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="heading-md mb-1">Your connection</h2>
            <p className="body-md text-text-muted">
              {degree?.label || 'Not connected'}
            </p>
          </div>

          {linkState === 'available' ? (
            <Button
              variant="primary"
              onClick={handleConnect}
              loading={connecting}
              leftIcon={<UserPlus className="h-4 w-4" />}
            >
              Connect
            </Button>
          ) : linkState === 'pending' ? (
            <Badge variant="warning" className="gap-1">
              <Clock className="h-3 w-3" aria-hidden="true" />
              Request pending
            </Badge>
          ) : (
            <Badge variant="success" className="gap-1">
              <UserCheck className="h-3 w-3" aria-hidden="true" />
              Connected
            </Badge>
          )}
        </div>

        {degree?.path?.length ? (
          <div className="mt-4 pt-4 border-t border-border">
            <h3 className="heading-sm mb-2 flex items-center gap-2">
              <GitBranch className="h-4 w-4" aria-hidden="true" />
              Shortest path
            </h3>
            <ol className="flex flex-wrap items-center gap-2">
              {pathNames.map((name, index) => (
                <li key={`${name}-${index}`} className="flex items-center gap-2">
                  <span className="px-2.5 py-1 rounded-full bg-surface-sunken text-text body-sm">
                    {name}
                  </span>
                  {index < pathNames.length - 1 && (
                    <span className="text-text-muted" aria-hidden="true">
                      &rarr;
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </div>
        ) : null}
      </Card>

      <Card className="p-6">
        <h2 className="heading-md mb-1 flex items-center gap-2">
          <Users className="h-5 w-5" aria-hidden="true" />
          Mutual connections
        </h2>
        {mutual.length === 0 ? (
          <p className="body-md text-text-muted mt-2">
            You have no mutual connections yet.
          </p>
        ) : (
          <ul className="mt-4 space-y-3">
            {mutual.map((person) => (
              <li key={person.user_id}>
                <Link
                  to={`/profile/${person.user_id}`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-surface-sunken transition-colors"
                >
                  <Avatar name={person.name} size="md" />
                  <div className="min-w-0">
                    <p className="font-medium body-md text-text truncate">{person.name}</p>
                    <p className="text-text-muted body-sm truncate">
                      @{person.username}
                      {person.programme ? ` · ${person.programme}` : ''}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </motion.div>
  );
}
