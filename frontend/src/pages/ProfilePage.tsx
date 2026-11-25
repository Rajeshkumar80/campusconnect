// Profile Page - own profile (edit) and other users' profiles (network detail)

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Edit, GraduationCap, Calendar, MessageCircle, NotebookPen } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Button } from '../components/ui/Button';
import { Input, Textarea } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { Avatar } from '../components/ui/Avatar';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { NetworkPanel } from '../components/profile/NetworkPanel';
import { PostCard } from '../components/feed/PostCard';
import type { Post, UserDetail } from '../types';

export function ProfilePage() {
  const { userId } = useParams<{ userId?: string }>();
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();
  const { error: showError, success: showSuccess } = useToastHelpers();

  const isOwnProfile = !userId || userId === currentUser?.user_id;
  const targetUserId = userId || currentUser?.user_id || '';

  const [profile, setProfile] = useState<UserDetail | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [postsLoading, setPostsLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    programme: '',
    year: '',
    bio: '',
    skills: '',
  });

  const fetchProfile = useCallback(async () => {
    if (!targetUserId) return;
    setLoading(true);
    try {
      const data = await api.getUser(targetUserId);
      setProfile(data);
      setFormData({
        name: data.name,
        programme: data.programme,
        year: data.year ? String(data.year) : '',
        bio: data.bio ?? '',
        skills: (data.skills ?? []).join(', '),
      });
      // Check connection status for other profiles
      if (!isOwnProfile && currentUser?.user_id) {
        const connections = await api.getConnections();
        setIsConnected(connections.some((c) => c.user_id === targetUserId));
      }
    } catch {
      showError('Failed to load profile', 'This user could not be loaded.');
      if (!isOwnProfile) navigate('/');
    } finally {
      setLoading(false);
    }
  }, [targetUserId, isOwnProfile, navigate, showError, currentUser?.user_id]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const fetchPosts = useCallback(async () => {
    if (!targetUserId) return;
    setPostsLoading(true);
    try {
      setPosts(await api.getUserPosts(targetUserId, 30));
    } catch {
      setPosts([]);
    } finally {
      setPostsLoading(false);
    }
  }, [targetUserId]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const handleDeletePost = async (postId: string) => {
    try {
      await api.deletePost(postId);
      setPosts((current) => current.filter((post) => post.post_id !== postId));
      showSuccess('Post deleted', 'The post and its attachment are gone');
    } catch (err) {
      showError('Could not delete', err instanceof Error ? err.message : 'Please try again');
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await api.updateProfile({
        name: formData.name.trim(),
        programme: formData.programme.trim(),
        year: Number(formData.year) || 0,
        bio: formData.bio.trim(),
        skills: formData.skills
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      });
      showSuccess('Profile updated', 'Your changes have been saved');
      setEditing(false);
      fetchProfile();
    } catch (err) {
      showError('Failed to update profile', err instanceof Error ? err.message : 'Please try again');
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        <div className="animate-pulse space-y-6">
          <div className="h-32 bg-surface-elevated rounded-xl" />
          <div className="h-40 bg-surface-elevated rounded-xl" />
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <Card className="p-8 text-center">
          <h3 className="heading-md mb-2">Profile not found</h3>
          <p className="body-md text-text-muted mb-4">
            This user doesn't exist or has been removed.
          </p>
          <Button variant="primary" onClick={() => navigate('/')}>
            Go Home
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <Card className="overflow-hidden" padding="none">
          <div className="relative h-24 overflow-hidden bg-brand">
            <div
              className="absolute inset-0 opacity-[0.12]"
              style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '18px 18px' }}
              aria-hidden="true"
            />
            <p className="absolute left-6 top-5 text-[0.625rem] font-semibold uppercase tracking-[0.22em] text-brand-light">
              {isOwnProfile ? 'Your profile' : 'Student profile'}
            </p>
          </div>

          <div className="relative z-10 px-6 pb-6 sm:px-8 sm:pb-8">
            <div className="-mt-9 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
              <div className="flex items-end gap-4">
                <div className="rounded-full bg-surface-elevated p-1.5 shadow-paper">
                  <Avatar name={profile.name} size="xl" />
                </div>
                <div className="min-w-0 pb-1">
                  <h1 className="font-display text-display-sm font-semibold tracking-tight text-text">{profile.name}</h1>
                  <p className="text-body-sm text-text-muted">@{profile.username}</p>
                </div>
              </div>
              {isOwnProfile && !editing && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setEditing(true)}
                  leftIcon={<Edit className="h-4 w-4" />}
                >
                  Edit profile
                </Button>
              )}
              {!isOwnProfile && targetUserId && isConnected && (
                <Link
                  to={`/messages/${targetUserId}`}
                  className="btn btn-primary btn-sm"
                >
                  <MessageCircle className="h-4 w-4" aria-hidden="true" />
                  Message
                </Link>
              )}
            </div>

            <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-body-sm text-text-muted">
              {profile.programme && (
                <span className="inline-flex items-center gap-1.5">
                  <GraduationCap className="h-4 w-4" aria-hidden="true" />
                  {profile.programme}
                </span>
              )}
              {profile.year ? (
                <span className="inline-flex items-center gap-1.5">
                  <Calendar className="h-4 w-4" aria-hidden="true" />
                  Year {profile.year}
                </span>
              ) : null}
            </div>

            {profile.bio ? (
              <div className="mt-6 border-t border-border pt-5">
                <p className="eyebrow mb-2">About</p>
                <p className="whitespace-pre-wrap text-body-md leading-relaxed text-text">{profile.bio}</p>
              </div>
            ) : null}

            {profile.skills?.length ? (
              <div className="mt-6 border-t border-border pt-5">
                <p className="eyebrow mb-3">Skills</p>
                <div className="flex flex-wrap gap-2">
                  {profile.skills.map((skill) => (
                    <Badge key={skill} variant="secondary">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </Card>
      </motion.div>

      {!isOwnProfile && targetUserId && (
        <div className="mt-6">
          <NetworkPanel targetUserId={targetUserId} />
        </div>
      )}

      <section className="mt-6" aria-label={isOwnProfile ? 'Your posts' : `${profile.name}'s posts`}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="heading-md flex items-center gap-2">
            <NotebookPen className="h-4 w-4 text-brand" aria-hidden="true" />
            {isOwnProfile ? 'Your posts' : 'Posts'}
          </h2>
          <span className="text-caption text-text-muted">{posts.length} total</span>
        </div>

        {postsLoading ? (
          <div className="space-y-4">
            {Array.from({ length: 2 }).map((_, index) => (
              <div key={index} className="card p-5">
                <div className="skeleton h-10 w-10 rounded-full" />
                <div className="mt-3 space-y-2">
                  <div className="skeleton h-3.5 w-40" />
                  <div className="skeleton h-3 w-full" />
                </div>
              </div>
            ))}
          </div>
        ) : posts.length === 0 ? (
          <Card className="p-8 text-center">
            <NotebookPen className="mx-auto mb-3 h-10 w-10 text-text-muted" aria-hidden="true" />
            <p className="heading-sm mb-1">No posts yet</p>
            <p className="body-sm text-text-muted">
              {isOwnProfile
                ? 'Share a note or a campus moment from the feed.'
                : `${profile.name} has not posted yet.`}
            </p>
            {isOwnProfile && (
              <Link to="/" className="btn btn-primary btn-md mt-4 inline-flex">
                Go to feed
              </Link>
            )}
          </Card>
        ) : (
          <div className="space-y-4">
            {posts.map((post) => (
              <PostCard
                key={post.post_id}
                post={post}
                currentUserId={currentUser?.user_id}
                onDelete={() => handleDeletePost(post.post_id)}
              />
            ))}
          </div>
        )}
      </section>

      <Modal
        isOpen={editing}
        onClose={() => {
          setEditing(false);
          fetchProfile();
        }}
        title="Edit Profile"
        size="lg"
      >
        <div className="space-y-4">
          <Input
            label="Full Name"
            value={formData.name}
            onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
            required
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Programme"
              value={formData.programme}
              onChange={(e) => setFormData((prev) => ({ ...prev, programme: e.target.value }))}
              placeholder="Your programme"
            />
            <Input
              label="Year"
              type="number"
              value={formData.year}
              onChange={(e) => setFormData((prev) => ({ ...prev, year: e.target.value }))}
              min={1}
              max={10}
            />
          </div>
          <Textarea
            label="Bio"
            value={formData.bio}
            onChange={(e) => setFormData((prev) => ({ ...prev, bio: e.target.value }))}
            rows={3}
            placeholder="Tell us about yourself..."
          />
          <Input
            label="Skills (comma separated)"
            value={formData.skills}
            onChange={(e) => setFormData((prev) => ({ ...prev, skills: e.target.value }))}
            placeholder="Python, React, Machine Learning"
          />
          <div className="flex justify-end gap-2 pt-2 border-t border-border">
            <Button
              variant="secondary"
              onClick={() => {
                setEditing(false);
                fetchProfile();
              }}
            >
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSave} loading={isSaving}>
              Save Changes
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
