// Discover Page - People You May Know (common-neighbour scoring from the API)

import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { GraduationCap, Search, UserPlus, Users } from 'lucide-react';
import { api } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Avatar } from '../components/ui/Avatar';
import { Badge } from '../components/ui/Badge';
import { PageHeader } from '../components/ui/PageHeader';
import type { Suggestion } from '../types';

export function DiscoverPage() {
  const { error: showError, success: showSuccess } = useToastHelpers();

  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [sendingRequestId, setSendingRequestId] = useState<string | null>(null);

  const fetchSuggestions = useCallback(async () => {
    setLoading(true);
    try {
      setSuggestions(await api.getSuggestions(20));
    } catch (err) {
      showError('Could not load suggestions', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  const connect = async (suggestion: Suggestion) => {
    setSendingRequestId(suggestion.user_id);
    try {
      await api.sendConnectionRequest(suggestion.user_id);
      showSuccess('Request sent', `${suggestion.name} will see it in Connections`);
      setSuggestions((current) => current.filter((item) => item.user_id !== suggestion.user_id));
    } catch (err) {
      showError('Could not send request', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setSendingRequestId(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Recommendations"
        title="People you may know"
        description="Ranked by shared connections in the campus graph. Closer mutuals rise first."
        actions={
          <Link to="/search" className="btn btn-secondary btn-md">
            <Search className="h-4 w-4" aria-hidden="true" />
            Search instead
          </Link>
        }
      />

      <div className="mt-8">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="card flex items-center gap-4 p-5">
                <div className="skeleton h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-3.5 w-40" />
                  <div className="skeleton h-3 w-56" />
                </div>
              </div>
            ))}
          </div>
        ) : suggestions.length === 0 ? (
          <div className="card px-6 py-16 text-center">
            <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand-light text-brand">
              <Users className="h-6 w-6" aria-hidden="true" />
            </span>
            <h2 className="mt-5 font-display text-heading-lg font-semibold text-text">No suggestions right now</h2>
            <p className="mx-auto mt-2 max-w-sm text-body-md text-text-muted">
              Recommendations come from mutual connections. Search for classmates directly or invite someone to connect.
            </p>
            <Link to="/search" className="btn btn-primary btn-md mt-6 inline-flex">
              Find classmates
            </Link>
          </div>
        ) : (
          <div className="space-y-3" role="list" aria-label="Suggested connections">
            {suggestions.map((suggestion, index) => (
              <motion.article
                key={suggestion.user_id}
                className="card flex flex-wrap items-center gap-4 p-4 transition-shadow hover:shadow-lift sm:p-5"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: Math.min(index * 0.04, 0.3) }}
                role="listitem"
              >
                <Link to={`/profile/${suggestion.user_id}`} className="flex-shrink-0">
                  <Avatar name={suggestion.name} size="lg" />
                </Link>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline gap-x-2">
                    <Link
                      to={`/profile/${suggestion.user_id}`}
                      className="truncate font-semibold text-text transition-colors hover:text-brand"
                    >
                      {suggestion.name}
                    </Link>
                    <span className="text-caption text-text-muted">@{suggestion.username}</span>
                  </div>
                  <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-caption text-text-muted">
                    {suggestion.programme && (
                      <span className="inline-flex items-center gap-1">
                        <GraduationCap className="h-3.5 w-3.5" aria-hidden="true" />
                        {suggestion.programme}
                      </span>
                    )}
                    {suggestion.year ? <span>Year {suggestion.year}</span> : null}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <Badge variant="secondary" size="sm">
                      {suggestion.mutual_count} mutual
                    </Badge>
                    <span className="text-caption text-text-muted">{suggestion.explanation}</span>
                  </div>
                </div>
                <Button
                  size="sm"
                  onClick={() => connect(suggestion)}
                  loading={sendingRequestId === suggestion.user_id}
                  leftIcon={<UserPlus className="h-3.5 w-3.5" />}
                >
                  Connect
                </Button>
              </motion.article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
