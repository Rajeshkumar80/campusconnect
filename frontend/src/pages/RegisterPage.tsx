// Register Page

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, Eye, EyeOff, User, GraduationCap, Calendar, Tag } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { AuthShell } from '../components/layout/AuthShell';
import { clsx } from 'clsx';

const programmes = [
  'B.Tech Computer Science',
  'B.Tech Electronics',
  'B.Tech Mechanical',
  'B.Tech Civil',
  'B.Tech Electrical',
  'M.Tech Computer Science',
  'M.Tech Data Science',
  'PhD Computer Science',
];

export function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    name: '',
    programme: '',
    year: '',
    bio: '',
    skills: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register } = useAuth();
  const { error: showError } = useToastHelpers();
  const navigate = useNavigate();

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      newErrors.username = 'Username can only contain letters, numbers, and underscores';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/[A-Z]/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one uppercase letter';
    } else if (!/[a-z]/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one lowercase letter';
    } else if (!/[0-9]/.test(formData.password)) {
      newErrors.password = 'Password must contain at least one number';
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (formData.name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    if (!formData.programme) {
      newErrors.programme = 'Please select your programme';
    }

    if (!formData.year) {
      newErrors.year = 'Please select your year';
    } else if (parseInt(formData.year) < 1 || parseInt(formData.year) > 10) {
      newErrors.year = 'Year must be between 1 and 10';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const clearError = (field: string) => {
    setErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[field];
      return newErrors;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await register({
        username: formData.username.trim(),
        password: formData.password,
        name: formData.name.trim(),
        programme: formData.programme,
        year: parseInt(formData.year),
        bio: formData.bio.trim(),
        skills: formData.skills.split(',').map(s => s.trim()).filter(Boolean),
      });
      navigate('/');
    } catch (err: any) {
      if (err.message?.includes('Username')) {
        setErrors({ username: err.message });
      } else {
        showError('Registration failed', err.message || 'Please try again');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const passwordStrength = () => {
    const pw = formData.password;
    let strength = 0;
    if (pw.length >= 8) strength++;
    if (/[A-Z]/.test(pw)) strength++;
    if (/[a-z]/.test(pw)) strength++;
    if (/[0-9]/.test(pw)) strength++;
    if (/[^A-Za-z0-9]/.test(pw)) strength++;
    return strength;
  };

  const strengthLabels = ['Very weak', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-lime-500', 'bg-green-500'];

  return (
    <AuthShell
      title="Create your account"
      subtitle="Join the campus graph in under a minute."
      footer={
        <p>
          Already have an account?{' '}
          <Link to="/login" className="link font-semibold">
            Sign in
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="card space-y-5 p-6 sm:p-7" noValidate>
            <Input
              label="Username"
              type="text"
              value={formData.username}
              onChange={e => handleChange('username', e.target.value)}
              onBlur={() => clearError('username')}
              error={errors.username}
              placeholder="Choose a username"
              autoComplete="username"
              autoFocus
              disabled={isSubmitting}
              leftIcon={<Mail className="h-5 w-5" />}
              helperText="Letters, numbers, and underscores only"
            />

            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={e => handleChange('password', e.target.value)}
                onBlur={() => clearError('password')}
                error={errors.password}
                placeholder="Create a password"
                autoComplete="new-password"
                disabled={isSubmitting}
                leftIcon={<Lock className="h-5 w-5" />}
                helperText="At least 8 characters with upper, lower, and number"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-text-muted hover:text-text transition-colors"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>

            {/* Password strength */}
            {formData.password && (
              <div className="space-y-1">
                <div className="h-1.5 rounded-full overflow-hidden bg-surface-sunken">
                  <motion.div
                    className={strengthColors[Math.min(passwordStrength() - 1, 4)] || 'bg-transparent'}
                    style={{ width: `${(Math.min(passwordStrength(), 5) / 5) * 100}%` }}
                    initial={{ width: 0 }}
                    animate={{ width: `${(Math.min(passwordStrength(), 5) / 5) * 100}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <p className="caption text-text-muted">
                  {strengthLabels[Math.min(passwordStrength() - 1, 4)] || ''}
                </p>
              </div>
            )}

            <Input
              label="Confirm Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={e => handleChange('confirmPassword', e.target.value)}
              onBlur={() => clearError('confirmPassword')}
              error={errors.confirmPassword}
              placeholder="Confirm your password"
              autoComplete="new-password"
              disabled={isSubmitting}
              leftIcon={<Lock className="h-5 w-5" />}
            />

            <Input
              label="Full Name"
              type="text"
              value={formData.name}
              onChange={e => handleChange('name', e.target.value)}
              onBlur={() => clearError('name')}
              error={errors.name}
              placeholder="Your full name"
              autoComplete="name"
              disabled={isSubmitting}
              leftIcon={<User className="h-5 w-5" />}
            />

            <div className="relative">
              <label className="label">Programme</label>
              <select
                value={formData.programme}
                onChange={e => handleChange('programme', e.target.value)}
                onBlur={() => clearError('programme')}
                className={clsx('input appearance-none pr-10', errors.programme && 'input-error')}
                disabled={isSubmitting}
                aria-invalid={errors.programme ? 'true' : 'false'}
              >
                <option value="">Select your programme</option>
                {programmes.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
              <GraduationCap className="absolute right-3 top-[38px] h-5 w-5 text-text-muted pointer-events-none" />
              {errors.programme && (
                <p className="text-caption text-red-500 mt-1" role="alert">{errors.programme}</p>
              )}
            </div>

            <div className="relative">
              <label className="label">Year</label>
              <select
                value={formData.year}
                onChange={e => handleChange('year', e.target.value)}
                onBlur={() => clearError('year')}
                className={clsx('input appearance-none pr-10', errors.year && 'input-error')}
                disabled={isSubmitting}
                aria-invalid={errors.year ? 'true' : 'false'}
              >
                <option value="">Select your year</option>
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(y => (
                  <option key={y} value={y.toString()}>{y}{y === 1 ? 'st' : y === 2 ? 'nd' : y === 3 ? 'rd' : 'th'} Year</option>
                ))}
              </select>
              <Calendar className="absolute right-3 top-[38px] h-5 w-5 text-text-muted pointer-events-none" />
              {errors.year && (
                <p className="text-caption text-red-500 mt-1" role="alert">{errors.year}</p>
              )}
            </div>

            <Input
              label="Bio (optional)"
              type="text"
              value={formData.bio}
              onChange={e => handleChange('bio', e.target.value)}
              placeholder="Tell us about yourself"
              disabled={isSubmitting}
              leftIcon={<Tag className="h-5 w-5" />}
            />

            <Input
              label="Skills (comma separated)"
              type="text"
              value={formData.skills}
              onChange={e => handleChange('skills', e.target.value)}
              placeholder="e.g., Python, React, Machine Learning"
              disabled={isSubmitting}
              leftIcon={<Tag className="h-5 w-5" />}
              helperText="Separate skills with commas"
            />

            <Button type="submit" variant="primary" size="lg" fullWidth loading={isSubmitting}>
              Create Account
            </Button>
      </form>
    </AuthShell>
  );
}

