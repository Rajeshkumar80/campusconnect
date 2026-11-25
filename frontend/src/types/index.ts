// CampusConnect TypeScript Types
// Shapes mirror the Flask API responses exactly (see backend/app/api).

/** Auth payload from /auth/register, /auth/login, /auth/me. */
export interface AuthUser {
  user_id: string;
  username: string;
  profile: Profile;
}

/** Profile document from /profiles/me and /profiles/<user_id>. */
export interface Profile {
  user_id: string;
  name: string;
  programme: string;
  year: number;
  bio: string;
  skills: string[];
  updated_at: string;
}

/** Public user summary from /users/search, /users/<id>, /connections. */
export interface UserSummary {
  user_id: string;
  username: string;
  name: string;
  programme: string;
  year: number;
}

/** Public user with bio and skills from /users/<id>. */
export interface UserDetail extends UserSummary {
  bio: string;
  skills: string[];
}

export interface ConnectionRequest {
  request_id: string;
  sender_id: string;
  recipient_id: string;
  status: 'pending' | 'accepted' | 'rejected' | 'cancelled';
  created_at: string;
  updated_at: string;
  sender?: UserSummary | null;
  recipient?: UserSummary | null;
}

export interface Connection extends UserSummary {}

export interface PostMedia {
  url: string;
  type: 'image' | 'video';
  mime: string;
  name: string;
  size: number;
}

export interface Post {
  post_id: string;
  author_id: string;
  author_username?: string;
  author_name?: string;
  text: string;
  media?: PostMedia | null;
  created_at: number;
  like_count?: number;
  comment_count?: number;
  liked_by_me?: boolean;
  likers?: Array<{ user_id: string; name: string; username: string }>;
}

export interface FeedPost extends Post {}

export interface Comment {
  comment_id: string;
  post_id: string;
  author_id: string;
  author_name: string;
  author_username: string;
  text: string;
  created_at: number;
}

export interface MessageMedia {
  url: string;
  type: 'image' | 'document' | 'audio';
  mime: string;
  name: string;
  size: number;
}

export interface SharedPost {
  post_id: string;
  text: string;
  media?: PostMedia | null;
  author_name: string;
  author_username: string;
}

export interface Message {
  message_id: string;
  sender_id: string;
  recipient_id: string;
  text: string;
  media?: MessageMedia | null;
  shared_post?: SharedPost | null;
  created_at: number;
  read_at?: number | null;
}

export interface MessageThread {
  user: UserSummary;
  last_message: Message | null;
  unread: number;
}

export interface NotificationItem {
  id: string;
  type: 'like' | 'comment' | 'connection_request';
  actor: UserSummary;
  post_id?: string;
  post_text?: string;
  text: string;
  created_at: number;
}

export interface NotificationFeed {
  notifications: NotificationItem[];
  unread: number;
}

export interface UnreadCounts {
  messages: number;
  notifications: number;
}

export interface Suggestion extends UserSummary {
  score: number;
  mutual_count: number;
  explanation: string;
}

export interface ConnectionDegree {
  degree: number | null;
  label: string;
  path: string[] | null;
  connected: boolean;
}

export interface ApiResponse<T> {
  data: T;
  meta?: Record<string, unknown>;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
  };
}

// Form types
export interface LoginForm {
  username: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  password: string;
  name: string;
  programme: string;
  year: number;
  bio: string;
  skills: string[];
}

export interface ProfileUpdateForm {
  name?: string;
  programme?: string;
  year?: number;
  bio?: string;
  skills?: string[];
}

// UI State types
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message?: string;
  duration?: number;
}
