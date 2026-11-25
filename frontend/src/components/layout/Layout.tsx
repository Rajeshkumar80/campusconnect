// Layout Component - branded campus shell

import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../lib/api';
import { Avatar } from '../ui/Avatar';
import {
  Menu,
  X,
  User,
  Users,
  Compass,
  Search,
  Settings,
  LogOut,
  Home,
  GraduationCap,
  Bell,
  MessageCircle,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useState, useEffect } from 'react';

type NavBadge = 'notifications' | 'messages' | null;

const navigation: {
  name: string;
  href: string;
  icon: typeof Home;
  end?: boolean;
  badge?: NavBadge;
}[] = [
  { name: 'Feed', href: '/', icon: Home, end: true },
  { name: 'Connections', href: '/connections', icon: Users },
  { name: 'Messages', href: '/messages', icon: MessageCircle, badge: 'messages' },
  { name: 'Notifications', href: '/notifications', icon: Bell, badge: 'notifications' },
  { name: 'Discover', href: '/discover', icon: Compass },
  { name: 'Search', href: '/search', icon: Search },
];

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <NavLink to="/" className="flex items-center gap-3 group">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-white shadow-sm transition-transform group-hover:-rotate-3">
        <GraduationCap className="h-5 w-5" aria-hidden="true" />
      </span>
      <span className="min-w-0">
        <span className="block font-display text-[1.15rem] font-semibold leading-tight text-text">
          CampusConnect
        </span>
        {!compact && (
          <span className="block text-[0.625rem] font-semibold uppercase tracking-[0.18em] text-text-muted">
            Chanakya University
          </span>
        )}
      </span>
    </NavLink>
  );
}

function NavItems({
  onNavigate,
  counts,
}: {
  onNavigate?: () => void;
  counts: { notifications: number; messages: number };
}) {
  return (
    <nav className="space-y-1" aria-label="Main">
      {navigation.map((item) => {
        const count = item.badge ? counts[item.badge] : 0;
        return (
          <NavLink
            key={item.name}
            to={item.href}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              clsx(
                'group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-body-md font-medium transition-all',
                isActive
                  ? 'bg-brand-light text-brand'
                  : 'text-text-muted hover:bg-surface-sunken hover:text-text'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={clsx('h-[1.15rem] w-[1.15rem] flex-shrink-0', isActive && 'text-brand')}
                  aria-hidden="true"
                />
                <span className="flex-1">{item.name}</span>
                {count > 0 && (
                  <span className="grid h-5 min-w-5 place-items-center rounded-full bg-accent px-1 text-[0.625rem] font-bold text-white">
                    {count > 9 ? '9+' : count}
                  </span>
                )}
                {isActive && count === 0 && (
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
                )}
              </>
            )}
          </NavLink>
        );
      })}
    </nav>
  );
}

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [counts, setCounts] = useState({ notifications: 0, messages: 0 });

  useEffect(() => {
    let active = true;
    const load = () => {
      api
        .getUnreadCounts()
        .then((next) => {
          if (active) setCounts(next);
        })
        .catch(() => {
          /* badge is optional; a failed poll should stay quiet */
        });
    };
    load();
    const timer = window.setInterval(load, 30000);
    window.addEventListener('messages:read', load);
    window.addEventListener('notifications:read', load);
    window.addEventListener('focus', load);
    return () => {
      active = false;
      window.clearInterval(timer);
      window.removeEventListener('messages:read', load);
      window.removeEventListener('notifications:read', load);
      window.removeEventListener('focus', load);
    };
  }, []);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [sidebarOpen]);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const userCard = (
    <div className="rounded-2xl border border-border bg-surface-sunken p-3">
      <div className="flex items-center gap-3">
        <NavLink to="/profile" aria-label="Your profile" className="flex-shrink-0">
          <Avatar name={user?.profile?.name} size="md" />
        </NavLink>
        <NavLink to="/profile" className="min-w-0 flex-1">
          <p className="truncate text-body-sm font-semibold text-text">
            {user?.profile?.name || 'Your profile'}
          </p>
          <p className="truncate text-caption text-text-muted">@{user?.username}</p>
        </NavLink>
        <button
          onClick={handleLogout}
          className="rounded-full p-2 text-text-muted transition-colors hover:bg-surface-sunken hover:text-text"
          aria-label="Log out"
          title="Log out"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-surface lg:flex">
      {/* Mobile header */}
      <header className="fixed left-0 right-0 top-0 z-40 lg:hidden">
        <div className="flex h-16 items-center justify-between border-b border-border bg-surface/90 px-4 backdrop-blur-md">
          <button
            onClick={() => setSidebarOpen(true)}
            className="btn-ghost -ml-2 p-2"
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
          <NavLink to="/" className="font-display text-heading-sm font-semibold text-text">
            CampusConnect
          </NavLink>
          <NavLink to="/profile" aria-label="Your profile">
            <Avatar name={user?.profile?.name} size="sm" />
          </NavLink>
        </div>
      </header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-[2px] lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
              aria-hidden="true"
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 w-72 overflow-hidden border-r border-border bg-surface-elevated p-4 lg:hidden"
              initial={{ x: -288 }}
              animate={{ x: 0 }}
              exit={{ x: -288 }}
              transition={{ type: 'spring', damping: 28, stiffness: 320 }}
            >
              <div className="flex h-full flex-col">
                <div className="mb-8 flex items-center justify-between">
                  <Brand />
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="rounded-full p-2 text-text-muted hover:bg-surface-sunken hover:text-text"
                    aria-label="Close menu"
                  >
                    <X className="h-5 w-5" aria-hidden="true" />
                  </button>
                </div>
                <NavItems onNavigate={() => setSidebarOpen(false)} counts={counts} />
                <div className="mt-auto space-y-2 pt-6">
                  <NavLink
                    to="/profile"
                    className="flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-body-md text-text-muted hover:bg-surface-sunken hover:text-text"
                  >
                    <User className="h-4 w-4" aria-hidden="true" /> Profile
                  </NavLink>
                  <NavLink
                    to="/settings"
                    className="flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-body-md text-text-muted hover:bg-surface-sunken hover:text-text"
                  >
                    <Settings className="h-4 w-4" aria-hidden="true" /> Settings
                  </NavLink>
                  {userCard}
                </div>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-[268px] flex-shrink-0 flex-col overflow-hidden border-r border-border bg-surface-elevated p-5 lg:flex">
        <div className="mb-9 mt-1">
          <Brand />
        </div>
        <div>
          <p className="mb-3 px-3 text-[0.625rem] font-semibold uppercase tracking-[0.2em] text-text-muted">
            Explore
          </p>
          <NavItems counts={counts} />
        </div>
        <div className="mt-auto space-y-2 pt-6">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-body-md transition-colors',
                isActive
                  ? 'bg-brand-light text-brand'
                  : 'text-text-muted hover:bg-surface-sunken hover:text-text'
              )
            }
          >
            <Settings className="h-4 w-4" aria-hidden="true" /> Settings
          </NavLink>
          {userCard}
          <p className="px-1 pt-1 text-[0.625rem] leading-relaxed text-text-muted">
            A campus network built for Chanakya University students.
          </p>
        </div>
      </aside>

      {/* Main content */}
      <main className="min-w-0 flex-1">
        <div className="pt-16 lg:pt-0">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
