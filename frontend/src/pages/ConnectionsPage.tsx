// Connections Page - accepted connections + pending requests

import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Tab, TabList, TabPanels, TabPanel } from '@headlessui/react';
import {
  UserPlus,
  UserCheck,
  UserMinus,
  Clock,
  X,
  Check,
  Send,
  GraduationCap,
  Users,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Avatar } from '../components/ui/Avatar';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { PageHeader } from '../components/ui/PageHeader';
import type { Connection, ConnectionRequest } from '../types';

export function ConnectionsPage() {
  const { error: showError, success: showSuccess } = useToastHelpers();

  const [connections, setConnections] = useState<Connection[]>([]);
  const [incomingRequests, setIncomingRequests] = useState<ConnectionRequest[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<ConnectionRequest[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [removing, setRemoving] = useState<Connection | null>(null);
  const [isRemoving, setIsRemoving] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [conns, incoming, outgoing, suggs] = await Promise.all([
        api.getConnections(),
        api.getIncomingRequests(),
        api.getOutgoingRequests(),
        api.getSuggestions(10),
      ]);
      setConnections(conns);
      setIncomingRequests(incoming);
      setOutgoingRequests(outgoing);
      setSuggestions(suggs);
    } catch (err) {
      showError('Failed to load connections', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleAccept = async (requestId: string) => {
    try {
      await api.acceptRequest(requestId);
      showSuccess('Request accepted', 'You are now connected');
      fetchAll();
    } catch (err) {
      showError('Failed to accept request', err instanceof Error ? err.message : 'Please try again');
    }
  };

  const handleReject = async (requestId: string) => {
    try {
      await api.rejectRequest(requestId);
      showSuccess('Request rejected', 'Connection request declined');
      fetchAll();
    } catch (err) {
      showError('Failed to reject request', err instanceof Error ? err.message : 'Please try again');
    }
  };

  const handleCancel = async (requestId: string) => {
    try {
      await api.cancelRequest(requestId);
      showSuccess('Request cancelled', 'Connection request cancelled');
      fetchAll();
    } catch (err) {
      showError('Failed to cancel request', err instanceof Error ? err.message : 'Please try again');
    }
  };

  const handleSendRequest = async (userId: string) => {
    try {
      await api.sendConnectionRequest(userId);
      showSuccess('Request sent', 'They will see it in Connections');
      fetchAll();
    } catch (err) {
      showError('Failed to send request', err instanceof Error ? err.message : 'Please try again');
    }
  };

  const handleRemove = async () => {
    if (!removing) return;
    setIsRemoving(true);
    try {
      await api.removeConnection(removing.user_id);
      showSuccess('Connection removed', `You are no longer connected with ${removing.name}`);
      setRemoving(null);
      fetchAll();
    } catch (err) {
      showError('Failed to remove connection', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setIsRemoving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="animate-pulse space-y-4">
          <div className="h-12 bg-surface-elevated rounded-xl" />
          <div className="h-40 bg-surface-elevated rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Your network"
        title="Connections"
        description="Accepted classmates, plus every request waiting in either direction."
      />

      <Tab.Group defaultIndex={activeTab} onChange={setActiveTab}>
        <TabList className="mt-8 flex w-full rounded-full border border-border bg-surface-elevated p-1 sm:w-auto">
          <Tab
            className={({ selected }) =>
              `flex-1 px-4 py-2 rounded-full text-body-sm font-semibold transition-colors ${
                selected
                  ? 'bg-brand text-surface shadow-sm'
                  : 'text-text-muted hover:text-text'
              }`
            }
          >
            <span className="flex items-center justify-center gap-2">
              <UserCheck className="h-4 w-4" aria-hidden="true" />
              Connections
              <Badge variant={activeTab === 0 ? 'primary' : 'secondary'}>{connections.length}</Badge>
            </span>
          </Tab>
          <Tab
            className={({ selected }) =>
              `flex-1 px-4 py-2 rounded-full text-body-sm font-semibold transition-colors ${
                selected
                  ? 'bg-brand text-surface shadow-sm'
                  : 'text-text-muted hover:text-text'
              }`
            }
          >
            <span className="flex items-center justify-center gap-2">
              <Clock className="h-4 w-4" aria-hidden="true" />
              Pending
              <Badge variant={activeTab === 1 ? 'primary' : 'secondary'}>
                {incomingRequests.length + outgoingRequests.length}
              </Badge>
            </span>
          </Tab>
          <Tab
            className={({ selected }) =>
              `flex-1 px-4 py-2 rounded-full text-body-sm font-semibold transition-colors ${
                selected
                  ? 'bg-brand text-surface shadow-sm'
                  : 'text-text-muted hover:text-text'
              }`
            }
          >
            <span className="flex items-center justify-center gap-2">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Suggestions
              <Badge variant={activeTab === 2 ? 'primary' : 'secondary'}>{suggestions.length}</Badge>
            </span>
          </Tab>
        </TabList>

        <TabPanels className="mt-4">
          <TabPanel className="space-y-3">
            {connections.length === 0 ? (
              <Card className="p-8 text-center">
                <UserCheck className="h-12 w-12 mx-auto mb-4 text-text-muted" aria-hidden="true" />
                <h3 className="heading-md mb-2">No connections yet</h3>
                <p className="body-md text-text-muted mb-4">
                  Start building your network by connecting with other students.
                </p>
                <Link to="/discover" className="btn btn-primary btn-md">
                  <UserPlus className="h-4 w-4" aria-hidden="true" />
                  Find people
                </Link>
              </Card>
            ) : (
              connections.map((conn) => (
                <motion.div
                  key={conn.user_id}
                  className="card flex items-center gap-4 p-4"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <Link to={`/profile/${conn.user_id}`} className="flex-shrink-0">
                    <Avatar name={conn.name} size="md" />
                  </Link>
                  <div className="flex-1 min-w-0">
                    <Link
                      to={`/profile/${conn.user_id}`}
                      className="truncate font-semibold text-text transition-colors hover:text-brand"
                    >
                      {conn.name}
                    </Link>
                    <p className="text-caption text-text-muted truncate">@{conn.username}</p>
                    <span className="mt-0.5 flex items-center gap-1 text-caption text-text-muted">
                      <GraduationCap className="h-3 w-3" aria-hidden="true" />
                      {conn.programme}
                      {conn.year ? ` · Year ${conn.year}` : ''}
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setRemoving(conn)}
                    leftIcon={<UserMinus className="h-4 w-4" />}
                    aria-label={`Remove ${conn.name}`}
                  >
                    Remove
                  </Button>
                </motion.div>
              ))
            )}
          </TabPanel>

          <TabPanel className="space-y-4">
            {incomingRequests.length > 0 && (
              <div className="space-y-3">
                <h3 className="heading-sm flex items-center gap-2">
                  <Send className="h-4 w-4" aria-hidden="true" />
                  Incoming Requests ({incomingRequests.length})
                </h3>
                {incomingRequests.map((req) => {
                  const sender = req.sender;
                  return (
                    <motion.div
                      key={req.request_id}
                      className="card flex flex-wrap items-center gap-4 p-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <Avatar name={sender?.name || 'User'} size="md" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium body-md text-text">{sender?.name || 'Unknown'}</p>
                        <p className="text-text-muted body-sm">@{sender?.username || 'unknown'}</p>
                        {sender?.programme ? (
                          <p className="text-text-muted body-sm">
                            {sender.programme}
                            {sender.year ? ` · Year ${sender.year}` : ''}
                          </p>
                        ) : null}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleAccept(req.request_id)}
                          leftIcon={<Check className="h-4 w-4" />}
                        >
                          Accept
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleReject(req.request_id)}
                          leftIcon={<X className="h-4 w-4" />}
                        >
                          Reject
                        </Button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}

            {outgoingRequests.length > 0 && (
              <div className="space-y-3">
                <h3 className="heading-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" aria-hidden="true" />
                  Sent Requests ({outgoingRequests.length})
                </h3>
                {outgoingRequests.map((req) => {
                  const recipient = req.recipient;
                  return (
                    <motion.div
                      key={req.request_id}
                      className="card flex flex-wrap items-center gap-4 p-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <Avatar name={recipient?.name || 'User'} size="md" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium body-md text-text">{recipient?.name || 'Unknown'}</p>
                        <p className="text-text-muted body-sm">@{recipient?.username || 'unknown'}</p>
                        <span className="badge-warning">Pending</span>
                      </div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleCancel(req.request_id)}
                        leftIcon={<X className="h-4 w-4" />}
                      >
                        Cancel
                      </Button>
                    </motion.div>
                  );
                })}
              </div>
            )}

            {incomingRequests.length === 0 && outgoingRequests.length === 0 && (
              <Card className="p-8 text-center">
                <Clock className="h-12 w-12 mx-auto mb-4 text-text-muted" aria-hidden="true" />
                <h3 className="heading-md mb-2">No pending requests</h3>
                <p className="body-md text-text-muted">All caught up!</p>
              </Card>
            )}
          </TabPanel>

          <TabPanel className="space-y-4">
            {suggestions.length === 0 ? (
              <Card className="p-8 text-center">
                <Users className="h-12 w-12 mx-auto mb-4 text-text-muted" aria-hidden="true" />
                <h3 className="heading-md mb-2">No suggestions right now</h3>
                <p className="body-md text-text-muted mb-4">
                  Your network already covers the campus graph.
                </p>
                <Link to="/discover" className="btn btn-primary btn-md">
                  <UserPlus className="h-4 w-4" aria-hidden="true" />
                  Discover people
                </Link>
              </Card>
            ) : (
              <div className="space-y-4">
                <section>
                  <h3 className="heading-sm flex items-center gap-2 mb-3">
                    <Users className="h-4 w-4 text-brand" aria-hidden="true" />
                    People you know ({suggestions.filter(s => s.mutual_count > 0).length})
                  </h3>
                  {suggestions.filter(s => s.mutual_count > 0).map((sugg) => (
                    <motion.div
                      key={sugg.user_id}
                      className="card flex flex-wrap items-center gap-4 p-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <Link to={`/profile/${sugg.user_id}`} className="flex-shrink-0">
                        <Avatar name={sugg.name} size="md" />
                      </Link>
                      <div className="flex-1 min-w-0">
                        <Link
                          to={`/profile/${sugg.user_id}`}
                          className="truncate font-semibold text-text transition-colors hover:text-brand"
                        >
                          {sugg.name}
                        </Link>
                        <p className="text-caption text-text-muted truncate">@{sugg.username}</p>
                        <p className="mt-0.5 flex items-center gap-1 text-caption text-text-muted">
                          <GraduationCap className="h-3 w-3" aria-hidden="true" />
                          {sugg.programme}
                          {sugg.year ? ` · Year ${sugg.year}` : ''}
                        </p>
                        <span className="mt-1 badge-primary">{sugg.mutual_count} mutual connections</span>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleSendRequest(sugg.user_id)}
                        leftIcon={<UserPlus className="h-3.5 w-3.5" />}
                      >
                        Connect
                      </Button>
                    </motion.div>
                  ))}
                </section>

                <section>
                  <h3 className="heading-sm flex items-center gap-2 mb-3">
                    <Sparkles className="h-4 w-4 text-accent" aria-hidden="true" />
                    Other people ({suggestions.filter(s => s.mutual_count === 0).length})
                  </h3>
                  {suggestions.filter(s => s.mutual_count === 0).map((sugg) => (
                    <motion.div
                      key={sugg.user_id}
                      className="card flex flex-wrap items-center gap-4 p-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                    >
                      <Link to={`/profile/${sugg.user_id}`} className="flex-shrink-0">
                        <Avatar name={sugg.name} size="md" />
                      </Link>
                      <div className="flex-1 min-w-0">
                        <Link
                          to={`/profile/${sugg.user_id}`}
                          className="truncate font-semibold text-text transition-colors hover:text-brand"
                        >
                          {sugg.name}
                        </Link>
                        <p className="text-caption text-text-muted truncate">@{sugg.username}</p>
                        <p className="mt-0.5 flex items-center gap-1 text-caption text-text-muted">
                          <GraduationCap className="h-3 w-3" aria-hidden="true" />
                          {sugg.programme}
                          {sugg.year ? ` · Year ${sugg.year}` : ''}
                        </p>
                        <span className="mt-1 text-caption text-text-muted">{sugg.explanation}</span>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleSendRequest(sugg.user_id)}
                        leftIcon={<UserPlus className="h-3.5 w-3.5" />}
                      >
                        Connect
                      </Button>
                    </motion.div>
                  ))}
                </section>
              </div>
            )}
          </TabPanel>
        </TabPanels>
      </Tab.Group>

      <Modal
        isOpen={removing !== null}
        onClose={() => setRemoving(null)}
        title="Remove connection"
        description="This removes the connection from both profiles and your network graph."
      >
        <p className="body-md">
          Remove your connection with <strong>{removing?.name}</strong>?
        </p>
        <div className="flex justify-end gap-2 pt-4">
          <Button variant="secondary" onClick={() => setRemoving(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleRemove} loading={isRemoving}>
            Remove
          </Button>
        </div>
      </Modal>
    </div>
  );
}
