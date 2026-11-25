// Search Page - trie-backed prefix search with debounce and recent searches.

import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, GraduationCap, Search, Users, X } from 'lucide-react';
import { api } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Avatar } from '../components/ui/Avatar';
import { PageHeader } from '../components/ui/PageHeader';
import type { UserSummary } from '../types';

const RECENT_KEY = 'campusconnect.recentSearches';
const DEBOUNCE_MS = 300;

export function SearchPage() {
  const { error: showError } = useToastHelpers();
  const navigate = useNavigate();

  const [query, setQuery] = useState('');
  const [results, setResults] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const timerRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(RECENT_KEY);
      if (saved) setRecentSearches(JSON.parse(saved));
    } catch {
      setRecentSearches([]);
    }
    return () => window.clearTimeout(timerRef.current);
  }, []);

  const saveRecentSearch = useCallback((term: string) => {
    const clean = term.trim();
    if (!clean) return;
    setRecentSearches((previous) => {
      const updated = [clean, ...previous.filter((item) => item !== clean)].slice(0, 5);
      localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const runSearch = useCallback(
    async (term: string) => {
      const trimmed = term.trim();
      if (!trimmed) {
        setResults([]);
        setShowResults(false);
        return;
      }
      setLoading(true);
      try {
        setResults(await api.searchUsers(trimmed, 20));
        setShowResults(true);
      } catch (err) {
        showError('Search failed', err instanceof Error ? err.message : 'Please try again');
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [showError]
  );

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setQuery(value);
    window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => runSearch(value), DEBOUNCE_MS);
  };

  const openProfile = (result: UserSummary) => {
    saveRecentSearch(result.username);
    setShowResults(false);
    navigate(`/profile/${result.user_id}`);
  };

  const clear = () => {
    window.clearTimeout(timerRef.current);
    setQuery('');
    setResults([]);
    setShowResults(false);
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Prefix search · Trie"
        title="Find someone"
        description="Type a name or username. Results update as you type — no full-table scan."
      />

      <div className="relative mt-8">
        <div className="card p-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-text-muted" aria-hidden="true" />
            <input
              type="text"
              value={query}
              onChange={handleChange}
              onFocus={() => setShowResults(true)}
              onBlur={() => window.setTimeout(() => setShowResults(false), 180)}
              placeholder="Try “asha”, “dev”, “mira”…"
              className="w-full rounded-xl border border-transparent bg-surface-sunken py-3 pl-11 pr-11 text-body-md text-text placeholder:text-text-muted focus:border-brand focus:bg-surface-elevated focus:outline-none focus:ring-2 focus:ring-brand/15"
              autoComplete="off"
              aria-autocomplete="list"
              aria-controls="search-results"
              aria-expanded={showResults}
              autoFocus
            />
            {query && (
              <button
                type="button"
                onClick={clear}
                className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-1 text-text-muted transition-colors hover:bg-surface-sunken hover:text-text"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            )}
          </div>
        </div>

        {showResults && (
          <motion.div
            id="search-results"
            className="absolute inset-x-0 top-full z-40 mt-2 overflow-hidden rounded-2xl border border-border bg-surface-elevated shadow-lift"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            role="listbox"
          >
            {loading && (
              <p className="flex items-center gap-2 px-4 py-5 text-body-sm text-text-muted" role="status">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
                Searching the trie…
              </p>
            )}

            {!loading && query.trim() && results.length === 0 && (
              <div className="px-6 py-10 text-center">
                <Users className="mx-auto h-8 w-8 text-text-muted" aria-hidden="true" />
                <p className="mt-3 text-body-md text-text-muted">No students start with “{query.trim()}”.</p>
              </div>
            )}

            {!loading && results.length > 0 && (
              <ul className="divide-y divide-border">
                {results.map((result, index) => (
                  <motion.li
                    key={result.user_id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.02 }}
                  >
                    <button
                      type="button"
                      onClick={() => openProfile(result)}
                      className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-surface-sunken"
                      role="option"
                      aria-selected="false"
                    >
                      <Avatar name={result.name} size="sm" />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-body-sm font-semibold text-text">{result.name}</span>
                        <span className="block truncate text-caption text-text-muted">
                          @{result.username}
                          {result.programme ? ` · ${result.programme}` : ''}
                        </span>
                      </span>
                      <ArrowRight className="h-4 w-4 flex-shrink-0 text-text-muted" aria-hidden="true" />
                    </button>
                  </motion.li>
                ))}
              </ul>
            )}

            {!loading && !query.trim() && recentSearches.length > 0 && (
              <div className="border-t border-border p-4">
                <p className="eyebrow mb-3">Recent searches</p>
                <div className="flex flex-wrap gap-2">
                  {recentSearches.map((term) => (
                    <button
                      key={term}
                      type="button"
                      className="rounded-full border border-border px-3 py-1.5 text-body-sm text-text-muted transition-colors hover:border-brand/40 hover:text-text"
                      onClick={() => {
                        setQuery(term);
                        runSearch(term);
                      }}
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {!showResults && results.length > 0 && (
        <div className="mt-8 space-y-3" role="list" aria-label="Search results">
          {results.map((result, index) => (
            <motion.article
              key={result.user_id}
              className="card flex items-center gap-4 p-4"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
              role="listitem"
            >
              <Avatar name={result.name} size="lg" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-semibold text-text">{result.name}</p>
                <p className="text-caption text-text-muted">@{result.username}</p>
                <p className="mt-1 flex flex-wrap items-center gap-x-3 text-caption text-text-muted">
                  {result.programme && (
                    <span className="inline-flex items-center gap-1">
                      <GraduationCap className="h-3.5 w-3.5" aria-hidden="true" />
                      {result.programme}
                    </span>
                  )}
                  {result.year ? <span>Year {result.year}</span> : null}
                </p>
              </div>
              <Button size="sm" variant="secondary" onClick={() => openProfile(result)}>
                View profile
              </Button>
            </motion.article>
          ))}
        </div>
      )}
    </div>
  );
}
