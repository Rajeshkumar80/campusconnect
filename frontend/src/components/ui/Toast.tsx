// Toast Component

import { createContext, useContext, useState, useCallback, type ReactNode, createElement, type ComponentType } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import type { Toast } from '../../types';

interface ToastContextType {
  toasts: Toast[];
  showToast: (toast: Omit<Toast, 'id'>) => string;
  hideToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).slice(2, 9);
    const newToast: Toast = { ...toast, id };
    setToasts(prev => [...prev, newToast]);

    // Auto-dismiss
    const duration = toast.duration ?? 5000;
    if (duration > 0) {
      setTimeout(() => hideToast(id), duration);
    }

    return id;
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, showToast, hideToast }}>
      {children}
      <ToastContainer toasts={toasts} onHide={hideToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

function ToastContainer({ toasts, onHide }: { toasts: Toast[]; onHide: (id: string) => void }) {
  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
    warning: AlertTriangle,
  };

  const colors = {
    success: 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400 border-green-200 dark:border-green-800',
    error: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400 border-red-200 dark:border-red-800',
    info: 'bg-brand-light text-brand dark:bg-brand/20 dark:text-brand border-brand/20 dark:border-brand/30',
    warning: 'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800',
  };

  return (
    <AnimatePresence>
      {toasts.map(toast => (
        <motion.div
          key={toast.id}
          className={clsx(
            'toast flex items-start gap-3 p-4 rounded-xl border shadow-lg min-w-[300px] max-w-md',
            colors[toast.type]
          )}
          initial={{ opacity: 0, x: 100, y: 20 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          exit={{ opacity: 0, x: 100, y: 20 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          role="alert"
          aria-live="polite"
        >
          <div className="flex-shrink-0 mt-0.5">
            {createElement(icons[toast.type] as ComponentType<any>, { className: "h-5 w-5", "aria-hidden": "true" })}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium body-sm">{toast.title}</p>
            {toast.message && (
              <p className="body-sm opacity-80 mt-0.5">{toast.message}</p>
            )}
          </div>
          <button
            onClick={() => onHide(toast.id)}
            className="flex-shrink-0 p-1 rounded hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            aria-label="Dismiss toast"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </motion.div>
      ))}
    </AnimatePresence>
  );
}

// Hook for easy toast access
export function useToastHelpers() {
  const { showToast, hideToast } = useToast();

  const success = useCallback((title: string, message?: string, duration?: number) =>
    showToast({ type: 'success', title, message, duration }), [showToast]);

  const error = useCallback((title: string, message?: string, duration?: number) =>
    showToast({ type: 'error', title, message, duration }), [showToast]);

  const info = useCallback((title: string, message?: string, duration?: number) =>
    showToast({ type: 'info', title, message, duration }), [showToast]);

  const warning = useCallback((title: string, message?: string, duration?: number) =>
    showToast({ type: 'warning', title, message, duration }), [showToast]);

  return { success, error, info, warning, hideToast };
}