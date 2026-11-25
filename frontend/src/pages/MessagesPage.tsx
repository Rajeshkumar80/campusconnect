// Messages - WhatsApp-style conversation with connections. Supports text,
// photos, PDFs, voice notes and shared posts. Polls while a thread is open.

import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import {
  ArrowLeft,
  FileText,
  ImagePlus,
  Loader2,
  Mic,
  Send,
  Square,
} from 'lucide-react';
import { api, mediaSrc } from '../lib/api';
import { useToastHelpers } from '../components/ui/Toast';
import { Avatar } from '../components/ui/Avatar';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import type { Message, MessageThread, UserSummary } from '../types';

function timeAgo(seconds: number) {
  try {
    return formatDistanceToNow(new Date(seconds * 1000), { addSuffix: true });
  } catch {
    return '';
  }
}

function MessageBody({ message }: { message: Message }) {
  return (
    <>
      {message.shared_post && (
        <div className="mb-2 rounded-xl border border-border bg-surface p-3">
          <p className="text-caption font-semibold text-brand">
            {message.shared_post.author_name}'s post
          </p>
          {message.shared_post.text && (
            <p className="mt-1 line-clamp-3 whitespace-pre-wrap text-body-sm text-text">
              {message.shared_post.text}
            </p>
          )}
          {message.shared_post.media?.type === 'image' && (
            <img
              src={mediaSrc(message.shared_post.media.url)}
              alt={message.shared_post.media.name}
              className="mt-2 max-h-40 w-full rounded-lg object-cover"
              crossOrigin="use-credentials"
            />
          )}
        </div>
      )}

      {message.media && (
        <div className="mb-1">
          {message.media.type === 'image' && (
            <img
              src={mediaSrc(message.media.url)}
              alt={message.media.name}
              className="max-h-64 w-full rounded-xl object-cover"
              crossOrigin="use-credentials"
            />
          )}
          {message.media.type === 'audio' && (
            <audio controls src={mediaSrc(message.media.url)} className="w-full min-w-[220px]" />
          )}
          {message.media.type === 'document' && (
            <a
              href={mediaSrc(message.media.url)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 text-body-sm font-medium text-brand hover:bg-surface-sunken"
            >
              <FileText className="h-4 w-4" aria-hidden="true" />
              {message.media.name}
            </a>
          )}
        </div>
      )}

      {message.text && <p className="whitespace-pre-wrap break-words">{message.text}</p>}
    </>
  );
}

export function MessagesPage() {
  const { userId } = useParams<{ userId?: string }>();
  const navigate = useNavigate();
  const { error: showError } = useToastHelpers();

  const [threads, setThreads] = useState<MessageThread[]>([]);
  const [threadsLoading, setThreadsLoading] = useState(true);
  const [other, setOther] = useState<UserSummary | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [sending, setSending] = useState(false);
  const [recording, setRecording] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const loadThreads = useCallback(async () => {
    try {
      setThreads(await api.getThreads());
    } catch (err) {
      showError('Could not load messages', err instanceof Error ? err.message : 'Try again');
    } finally {
      setThreadsLoading(false);
    }
  }, [showError]);

  const loadConversation = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await api.getConversation(userId);
      setOther(data.user);
      // Append only new messages to avoid scroll jumping
      setMessages((current) => {
        const existingIds = new Set(current.map((m) => m.message_id));
        const newMessages = data.messages.filter((m) => !existingIds.has(m.message_id));
        return [...current, ...newMessages];
      });
      window.dispatchEvent(new CustomEvent('messages:read'));
    } catch (err) {
      showError('Could not open conversation', err instanceof Error ? err.message : 'Try again');
    } finally {
      setMessagesLoading(false);
    }
  }, [userId, showError]);

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  useEffect(() => {
    setMessagesLoading(Boolean(userId));
    setMessages([]);
    setOther(null);
    loadConversation();
    if (!userId) return;
    const timer = window.setInterval(loadConversation, 5000);
    return () => window.clearInterval(timer);
  }, [userId, loadConversation]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' });
  }, [messages]);

  const send = async (messageText = text, attachment: File | null = file) => {
    if (!userId) return;
    const trimmed = messageText.trim();
    if (!trimmed && !attachment) return;
    setSending(true);
    try {
      const sent = await api.sendMessage(userId, {
        text: trimmed,
        media: attachment ?? undefined,
      });
      setMessages((current) => [...current, sent]);
      setText('');
      setFile(null);
      loadThreads();
    } catch (err) {
      showError('Message not sent', err instanceof Error ? err.message : 'Try again');
    } finally {
      setSending(false);
    }
  };

  const toggleRecording = async () => {
    if (recording) {
      recorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
        setRecording(false);
        const mime = recorder.mimeType || 'audio/webm';
        const ext = mime.includes('ogg') ? 'ogg' : 'weba';
        const blob = new Blob(chunksRef.current, { type: mime });
        const voice = new File([blob], `voice-${Date.now()}.${ext}`, { type: mime });
        if (blob.size > 0) send('', voice);
      };
      recorder.start();
      recorderRef.current = recorder;
      setRecording(true);
    } catch {
      showError('Microphone unavailable', 'Allow microphone access to record a voice note');
    }
  };

  const activeThread = threads.find((thread) => thread.user.user_id === userId);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-10 lg:py-12">
      <PageHeader
        eyebrow="Direct messages"
        title="Messages"
        description="Chat with your connections. Send notes, photos, PDFs, voice messages or shared posts."
      />

      <div className="mt-8 grid gap-5 lg:grid-cols-[320px_minmax(0,1fr)]">
        <Card className={`overflow-hidden ${userId ? 'hidden lg:block' : ''}`} padding="none">
          <div className="border-b border-border px-4 py-3">
            <p className="eyebrow">Conversations</p>
          </div>
          {threadsLoading ? (
            <div className="space-y-3 p-4">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="skeleton h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <div className="skeleton h-3.5 w-28" />
                    <div className="skeleton h-3 w-40" />
                  </div>
                </div>
              ))}
            </div>
          ) : threads.length === 0 ? (
            <p className="p-6 text-body-sm text-text-muted">
              No conversations yet. Accept a connection request, then message them from their profile.
            </p>
          ) : (
            <ul className="max-h-[65vh] overflow-y-auto">
              {threads.map((thread) => (
                <li key={thread.user.user_id}>
                  <Link
                    to={`/messages/${thread.user.user_id}`}
                    className={`flex items-center gap-3 border-b border-border/60 px-4 py-3 transition-colors hover:bg-surface-sunken ${
                      thread.user.user_id === userId ? 'bg-brand-light/60' : ''
                    }`}
                  >
                    <Avatar name={thread.user.name} size="md" />
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center justify-between gap-2">
                        <span className="truncate text-body-sm font-semibold text-text">
                          {thread.user.name}
                        </span>
                        {thread.last_message && (
                          <span className="flex-shrink-0 text-[0.625rem] text-text-muted">
                            {timeAgo(thread.last_message.created_at)}
                          </span>
                        )}
                      </span>
                      <span className="mt-0.5 flex items-center gap-2">
                        <span className="min-w-0 flex-1 truncate text-caption text-text-muted">
                          {thread.last_message?.text ||
                            (thread.last_message?.media ? 'Attachment' : thread.user.programme)}
                        </span>
                        {thread.unread > 0 && (
                          <span className="grid h-5 min-w-5 place-items-center rounded-full bg-brand px-1 text-[0.625rem] font-bold text-surface">
                            {thread.unread}
                          </span>
                        )}
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className={`flex min-h-[65vh] flex-col overflow-hidden ${userId ? '' : 'hidden lg:flex'}`} padding="none">
          {!userId ? (
            <div className="flex flex-1 flex-col items-center justify-center p-10 text-center">
              <Send className="mb-4 h-10 w-10 text-text-muted" aria-hidden="true" />
              <p className="heading-md mb-1">Pick a conversation</p>
              <p className="body-sm text-text-muted">
                Choose a connection on the left, or open a profile and press Message.
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 border-b border-border px-4 py-3">
                <button
                  type="button"
                  onClick={() => navigate('/messages')}
                  className="rounded-full p-1.5 text-text-muted hover:bg-surface-sunken lg:hidden"
                  aria-label="Back to conversations"
                >
                  <ArrowLeft className="h-5 w-5" aria-hidden="true" />
                </button>
                <Avatar name={other?.name || activeThread?.user.name} size="md" />
                <div className="min-w-0">
                  <Link
                    to={`/profile/${other?.user_id || userId}`}
                    className="block truncate text-body-sm font-semibold text-text hover:text-brand"
                  >
                    {other?.name || activeThread?.user.name || 'Conversation'}
                  </Link>
                  <p className="text-caption text-text-muted">
                    {other?.programme || activeThread?.user.programme}
                  </p>
                </div>
              </div>

              <div className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-surface px-4 py-4">
                {messagesLoading ? (
                  <p className="flex items-center justify-center gap-2 py-8 text-caption text-text-muted">
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Loading…
                  </p>
                ) : messages.length === 0 ? (
                  <p className="py-10 text-center text-body-sm text-text-muted">
                    Say hello to {other?.name || 'your connection'}.
                  </p>
                ) : (
                  messages.map((message) => {
                    const mine = message.sender_id !== userId;
                    return (
                      <div
                        key={message.message_id}
                        className={`flex ${mine ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-body-sm shadow-sm sm:max-w-[70%] ${
                            mine
                              ? 'rounded-br-md bg-brand text-surface'
                              : 'rounded-bl-md border border-border bg-surface-elevated text-text'
                          }`}
                        >
                          <MessageBody message={message} />
                          <p className={`mt-1 text-right text-[0.625rem] ${mine ? 'text-surface/70' : 'text-text-muted'}`}>
                            {timeAgo(message.created_at)}
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
                <div ref={bottomRef} />
              </div>

              <div className="border-t border-border p-3">
                {file && (
                  <div className="mb-2 flex items-center gap-2 rounded-lg bg-surface-sunken px-3 py-2 text-caption text-text-muted">
                    <FileText className="h-3.5 w-3.5" aria-hidden="true" />
                    <span className="min-w-0 flex-1 truncate">{file.name}</span>
                    <button type="button" onClick={() => setFile(null)} className="font-semibold text-brand">
                      Remove
                    </button>
                  </div>
                )}
                <div className="flex items-end gap-2">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="rounded-full p-2.5 text-text-muted hover:bg-surface-sunken hover:text-brand"
                    aria-label="Attach a photo or PDF"
                  >
                    <ImagePlus className="h-5 w-5" aria-hidden="true" />
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.pdf"
                    className="hidden"
                    onChange={(event) => {
                      setFile(event.target.files?.[0] ?? null);
                      event.target.value = '';
                    }}
                  />
                  <textarea
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === ' ') {
                        event.stopPropagation();
                      }
                      if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        send();
                      }
                    }}
                    rows={1}
                    placeholder="Write a message…"
                    aria-label="Message"
                    className="input max-h-28 min-h-[2.75rem] flex-1 resize-none py-2.5"
                  />
                  <button
                    type="button"
                    onClick={toggleRecording}
                    className={`rounded-full p-2.5 ${
                      recording
                        ? 'bg-red-600 text-white'
                        : 'text-text-muted hover:bg-surface-sunken hover:text-brand'
                    }`}
                    aria-label={recording ? 'Stop recording' : 'Record a voice message'}
                  >
                    {recording ? (
                      <Square className="h-5 w-5" aria-hidden="true" />
                    ) : (
                      <Mic className="h-5 w-5" aria-hidden="true" />
                    )}
                  </button>
                  <Button
                    onClick={() => send()}
                    loading={sending}
                    disabled={!text.trim() && !file}
                    aria-label="Send message"
                  >
                    <Send className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </div>
                {recording && (
                  <p className="mt-2 text-caption font-medium text-red-600">
                    Recording… press the square to send.
                  </p>
                )}
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
