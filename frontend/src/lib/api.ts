// CampusConnect API Client
// Typed wrappers around the Flask REST API at /api/v1.

import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type {
  ApiErrorBody,
  ApiResponse,
  AuthUser,
  Comment,
  Connection,
  ConnectionDegree,
  ConnectionRequest,
  FeedPost,
  Message,
  MessageThread,
  NotificationFeed,
  Post,
  Profile,
  Suggestion,
  UnreadCounts,
  UserDetail,
  UserSummary,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

/** Turn the API's relative media path into an absolute URL for <img>/<video>. */
export function mediaSrc(url: string): string {
  return new URL(url, API_BASE_URL).toString();
}

export class ApiError extends Error {
  code: string;
  status?: number;

  constructor(message: string, code = 'UNKNOWN_ERROR', status?: number) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

class ApiClient {
  private client: AxiosInstance;
  private csrfToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      withCredentials: true, // cookie-based session
      timeout: 60000,
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const method = (config.method || 'get').toLowerCase();
        if (this.csrfToken && ['post', 'put', 'patch', 'delete'].includes(method)) {
          config.headers['X-CSRFToken'] = this.csrfToken;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => {
        const token = response.headers['x-csrftoken'];
        if (token) this.csrfToken = token;
        return response;
      },
      async (error: AxiosError<ApiErrorBody>) => {
        const status = error.response?.status;
        const code = error.response?.data?.error?.code;

        if (status === 401) {
          window.dispatchEvent(new CustomEvent('auth:unauthorized'));
        }

        // Flask-WTF answers a missing token with 400, so retry on the error code.
        if (code === 'CSRF_TOKEN_MISSING') {
          try {
            await this.refreshCsrfToken();
            if (error.config && this.csrfToken) {
              error.config.headers['X-CSRFToken'] = this.csrfToken;
              return this.client.request(error.config);
            }
          } catch {
            window.dispatchEvent(new CustomEvent('auth:unauthorized'));
          }
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  private async refreshCsrfToken() {
    try {
      // Read the token from the JSON body: CORS does not expose X-CSRFToken to JS.
      const response = await this.client.get<ApiResponse<{ csrf_token: string }>>('/auth/csrf');
      this.csrfToken = response.data.data.csrf_token || null;
    } catch {
      this.csrfToken = null;
    }
  }

  private formatError(error: AxiosError<ApiErrorBody>): ApiError {
    const message =
      error.response?.data?.error?.message || error.message || 'An unexpected error occurred';
    const code = error.response?.data?.error?.code || 'UNKNOWN_ERROR';
    return new ApiError(message, code, error.response?.status);
  }

  // ---- Auth ----
  async register(data: {
    username: string;
    password: string;
    name: string;
    programme: string;
    year: number;
    bio: string;
    skills: string[];
  }): Promise<AuthUser> {
    const response = await this.client.post<ApiResponse<{ user: AuthUser }>>('/auth/register', data);
    return response.data.data.user;
  }

  async login(username: string, password: string): Promise<AuthUser> {
    const response = await this.client.post<ApiResponse<{ user: AuthUser }>>('/auth/login', {
      username,
      password,
    });
    return response.data.data.user;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  async getCurrentUser(): Promise<AuthUser> {
    const response = await this.client.get<ApiResponse<{ user: AuthUser }>>('/auth/me');
    return response.data.data.user;
  }

  // ---- Profiles ----
  async getProfile(userId?: string): Promise<Profile> {
    const url = userId ? `/profiles/${userId}` : '/profiles/me';
    const response = await this.client.get<ApiResponse<{ profile: Profile }>>(url);
    return response.data.data.profile;
  }

  async updateProfile(data: Partial<Profile>): Promise<Profile> {
    const response = await this.client.patch<ApiResponse<{ profile: Profile }>>('/profiles/me', data);
    return response.data.data.profile;
  }

  // ---- Users / search ----
  async searchUsers(query: string, limit = 10): Promise<UserSummary[]> {
    const response = await this.client.get<ApiResponse<{ users: UserSummary[] }>>('/users/search', {
      params: { q: query, limit },
    });
    return response.data.data.users;
  }

  async getUser(userId: string): Promise<UserDetail> {
    const response = await this.client.get<ApiResponse<{ user: UserDetail }>>(`/users/${userId}`);
    return response.data.data.user;
  }

  // ---- Connections ----
  async getConnections(): Promise<Connection[]> {
    const response = await this.client.get<ApiResponse<{ connections: Connection[] }>>('/connections');
    return response.data.data.connections;
  }

  async sendConnectionRequest(recipientId: string): Promise<ConnectionRequest> {
    const response = await this.client.post<ApiResponse<{ request: ConnectionRequest }>>(
      '/connections/requests',
      { recipient_id: recipientId }
    );
    return response.data.data.request;
  }

  async getIncomingRequests(): Promise<ConnectionRequest[]> {
    const response = await this.client.get<ApiResponse<{ requests: ConnectionRequest[] }>>(
      '/connections/requests/incoming'
    );
    return response.data.data.requests;
  }

  async getOutgoingRequests(): Promise<ConnectionRequest[]> {
    const response = await this.client.get<ApiResponse<{ requests: ConnectionRequest[] }>>(
      '/connections/requests/outgoing'
    );
    return response.data.data.requests;
  }

  async acceptRequest(requestId: string): Promise<ConnectionRequest> {
    const response = await this.client.post<ApiResponse<{ request: ConnectionRequest }>>(
      `/connections/requests/${requestId}/accept`
    );
    return response.data.data.request;
  }

  async rejectRequest(requestId: string): Promise<ConnectionRequest> {
    const response = await this.client.post<ApiResponse<{ request: ConnectionRequest }>>(
      `/connections/requests/${requestId}/reject`
    );
    return response.data.data.request;
  }

  async cancelRequest(requestId: string): Promise<ConnectionRequest> {
    const response = await this.client.post<ApiResponse<{ request: ConnectionRequest }>>(
      `/connections/requests/${requestId}/cancel`
    );
    return response.data.data.request;
  }

  async removeConnection(userId: string): Promise<void> {
    await this.client.delete(`/connections/${userId}`);
  }

  async getMutualConnections(userId: string): Promise<UserSummary[]> {
    const response = await this.client.get<ApiResponse<{ mutual_connections: UserSummary[] }>>(
      `/connections/${userId}/mutual`
    );
    return response.data.data.mutual_connections;
  }

  async getConnectionDegree(userId: string): Promise<ConnectionDegree> {
    const response = await this.client.get<ApiResponse<{ degree: ConnectionDegree }>>(
      `/connections/${userId}/degree`
    );
    return response.data.data.degree;
  }

  async getShortestPath(userId: string): Promise<string[] | null> {
    const response = await this.client.get<ApiResponse<{ path: string[] | null }>>(
      `/connections/${userId}/path`
    );
    return response.data.data.path;
  }

  async getSuggestions(limit = 10): Promise<Suggestion[]> {
    const response = await this.client.get<ApiResponse<{ suggestions: Suggestion[] }>>(
      '/connections/suggestions',
      { params: { limit } }
    );
    return response.data.data.suggestions;
  }

  // ---- Posts ----
  async createPost(text: string, media?: File): Promise<Post> {
    let payload: FormData | { text: string } = { text };
    if (media) {
      const form = new FormData();
      form.append('text', text);
      form.append('media', media);
      payload = form;
    }
    const response = await this.client.post<ApiResponse<{ post: Post }>>('/posts', payload);
    return response.data.data.post;
  }

  async getOwnPosts(limit = 20): Promise<Post[]> {
    const response = await this.client.get<ApiResponse<{ posts: Post[] }>>('/posts/mine', {
      params: { limit },
    });
    return response.data.data.posts;
  }

  async deletePost(postId: string): Promise<void> {
    await this.client.delete(`/posts/${postId}`);
  }

  async getFeed(limit = 20): Promise<FeedPost[]> {
    const response = await this.client.get<ApiResponse<{ feed: FeedPost[] }>>('/posts/feed', {
      params: { limit },
    });
    return response.data.data.feed;
  }

  async getUserPosts(userId: string, limit = 20): Promise<Post[]> {
    const response = await this.client.get<ApiResponse<{ posts: Post[] }>>(
      `/posts/user/${userId}`,
      { params: { limit } }
    );
    return response.data.data.posts;
  }

  async toggleLike(postId: string): Promise<{ liked: boolean; like_count: number }> {
    const response = await this.client.post<
      ApiResponse<{ liked: boolean; like_count: number }>
    >(`/posts/${postId}/like`);
    return response.data.data;
  }

  async getComments(postId: string): Promise<Comment[]> {
    const response = await this.client.get<ApiResponse<{ comments: Comment[] }>>(
      `/posts/${postId}/comments`
    );
    return response.data.data.comments;
  }

  async addComment(postId: string, text: string): Promise<Comment> {
    const response = await this.client.post<ApiResponse<{ comment: Comment }>>(
      `/posts/${postId}/comments`,
      { text }
    );
    return response.data.data.comment;
  }

  async sharePost(postId: string, recipientIds: string[], note = ''): Promise<number> {
    const response = await this.client.post<ApiResponse<{ sent: number }>>(
      `/posts/${postId}/share`,
      { recipient_ids: recipientIds, note }
    );
    return response.data.data.sent;
  }

  // ---- Notifications ----
  async getNotifications(): Promise<NotificationFeed> {
    const response = await this.client.get<ApiResponse<NotificationFeed>>('/notifications');
    return response.data.data;
  }

  async getUnreadCounts(): Promise<UnreadCounts> {
    const response = await this.client.get<ApiResponse<UnreadCounts>>('/notifications/count');
    return response.data.data;
  }

  async markNotificationsRead(): Promise<void> {
    await this.client.post('/notifications/read');
  }

  // ---- Messages ----
  async getThreads(): Promise<MessageThread[]> {
    const response = await this.client.get<ApiResponse<{ threads: MessageThread[] }>>(
      '/messages/threads'
    );
    return response.data.data.threads;
  }

  async getConversation(
    userId: string
  ): Promise<{ user: UserSummary; messages: Message[] }> {
    const response = await this.client.get<
      ApiResponse<{ user: UserSummary; messages: Message[] }>
    >(`/messages/${userId}`);
    return response.data.data;
  }

  async sendMessage(
    userId: string,
    payload: { text?: string; media?: File; sharedPostId?: string }
  ): Promise<Message> {
    const form = new FormData();
    form.append('text', payload.text ?? '');
    if (payload.media) form.append('media', payload.media);
    if (payload.sharedPostId) form.append('shared_post_id', payload.sharedPostId);
    const response = await this.client.post<ApiResponse<{ message: Message }>>(
      `/messages/${userId}`,
      form
    );
    return response.data.data.message;
  }

  // ---- Health ----
  async healthCheck(): Promise<unknown> {
    const response = await this.client.get('/health/live');
    return response.data;
  }
}

export const api = new ApiClient();
