// Settings Page - only features that work end to end.

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { User, Palette, LogOut, Moon, Sun, GraduationCap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Avatar } from '../components/ui/Avatar';
import { PageHeader } from '../components/ui/PageHeader';
import { clsx } from 'clsx';

const THEME_KEY = 'campusconnect.darkMode';

export function SettingsPage() {
  const { user, logout } = useAuth();
  const { info: showInfo } = useToastHelpers();
  const [darkMode, setDarkMode] = useState(false);

  // Restore the saved theme before first paint of this screen.
  useEffect(() => {
    const saved = localStorage.getItem(THEME_KEY) === 'true';
    setDarkMode(saved);
    document.documentElement.classList.toggle('dark', saved);
  }, []);

  const toggleTheme = () => {
    const next = !darkMode;
    setDarkMode(next);
    document.documentElement.classList.toggle('dark', next);
    localStorage.setItem(THEME_KEY, String(next));
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Account"
        title="Settings"
        description="Profile shortcuts, appearance and the current session."
      />

      <motion.div
        className="mt-8 space-y-4"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <Card className="p-6">
          <div className="flex items-center gap-4 flex-wrap">
            <Avatar name={user?.profile?.name} size="lg" />
            <div className="flex-1 min-w-0">
              <p className="font-medium body-lg text-text">{user?.profile?.name}</p>
              <p className="text-text-muted body-sm">@{user?.username}</p>
              {user?.profile?.programme ? (
                <span className="flex items-center gap-1 text-text-muted body-sm mt-1">
                  <GraduationCap className="h-3 w-3" aria-hidden="true" />
                  {user.profile.programme}
                  {user.profile.year ? ` · Year ${user.profile.year}` : ''}
                </span>
              ) : null}
            </div>
            <Link to="/profile" className="btn btn-secondary btn-md">
              <User className="h-4 w-4" aria-hidden="true" />
              Edit profile
            </Link>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="heading-md mb-1 flex items-center gap-2">
            <Palette className="h-5 w-5" aria-hidden="true" />
            Appearance
          </h2>
          <p className="body-md text-text-muted">Customize how CampusConnect looks</p>

          <div className="mt-4 flex items-center justify-between py-3 border-t border-border">
            <div>
              <p className="font-medium body-md">Dark mode</p>
              <p className="body-sm text-text-muted">Switch between light and dark theme</p>
            </div>
            <button
              type="button"
              onClick={toggleTheme}
              className={clsx(
                'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                darkMode ? 'bg-brand' : 'bg-surface-sunken'
              )}
              role="switch"
              aria-checked={darkMode}
              aria-label="Toggle dark mode"
            >
              <span
                className={clsx(
                  'inline-flex h-4 w-4 items-center justify-center rounded-full bg-white text-text transition-transform',
                  darkMode ? 'translate-x-6' : 'translate-x-1'
                )}
              >
                {darkMode ? (
                  <Moon className="h-2.5 w-2.5" aria-hidden="true" />
                ) : (
                  <Sun className="h-2.5 w-2.5" aria-hidden="true" />
                )}
              </span>
            </button>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="heading-md mb-1">Session</h2>
          <p className="body-md text-text-muted">Sign out of CampusConnect on this device</p>
          <div className="mt-4 flex justify-end">
            <Button
              variant="secondary"
              onClick={async () => {
                await logout();
                showInfo('Signed out', 'You have been logged out');
              }}
              leftIcon={<LogOut className="h-4 w-4" />}
            >
              Log out
            </Button>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
