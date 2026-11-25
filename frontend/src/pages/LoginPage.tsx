// Login Page

import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Lock, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { AuthShell } from '../components/layout/AuthShell';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ username?: string; password?: string; form?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const { error: showError } = useToastHelpers();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: string })?.from || '/';

  const validate = () => {
    const next: typeof errors = {};
    if (!username.trim()) next.username = 'Username is required';
    if (!password) next.password = 'Password is required';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed. Please try again.';
      setErrors({ form: message });
      showError('Login failed', message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to pick up where the campus left off."
      footer={
        <p>
          New here?{' '}
          <Link to="/register" className="link font-semibold">
            Create an account
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="card space-y-5 p-6 sm:p-7" noValidate>
        {errors.form && (
          <div
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-body-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300"
            role="alert"
          >
            {errors.form}
          </div>
        )}

        <Input
          label="Username"
          type="text"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          onBlur={() => setErrors((prev) => ({ ...prev, username: undefined }))}
          error={errors.username}
          placeholder="your_username"
          autoComplete="username"
          autoFocus
          disabled={isSubmitting}
          leftIcon={<User className="h-4 w-4" />}
        />

        <div className="relative">
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onBlur={() => setErrors((prev) => ({ ...prev, password: undefined }))}
            error={errors.password}
            placeholder="Your password"
            autoComplete="current-password"
            disabled={isSubmitting}
            leftIcon={<Lock className="h-4 w-4" />}
          />
          <button
            type="button"
            onClick={() => setShowPassword((visible) => !visible)}
            className="absolute right-3 top-[36px] text-text-muted transition-colors hover:text-text"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>

        <Button type="submit" size="lg" fullWidth loading={isSubmitting}>
          Sign in
        </Button>
      </form>
    </AuthShell>
  );
}
