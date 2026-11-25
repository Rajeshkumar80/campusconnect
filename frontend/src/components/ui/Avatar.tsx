// Avatar Component

import { forwardRef, type HTMLAttributes, useMemo, type ReactElement, cloneElement } from 'react';
import { clsx } from 'clsx';

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  src?: string | null;
  alt?: string;
  name?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  shape?: 'circle' | 'square';
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(part => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

function getColorFromName(name: string): string {
  const colors = [
    'bg-brand-light text-brand',
    'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    'bg-yellow-50 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    'bg-pink-50 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
    'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
    'bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
  ];

  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

export const Avatar = forwardRef<HTMLDivElement, AvatarProps>(
  ({ src, alt, name, size = 'md', shape = 'circle', className, ...props }, ref) => {
    const sizeClasses = {
      sm: 'avatar-sm',
      md: 'avatar-md',
      lg: 'avatar-lg',
      xl: 'avatar-xl',
    };

    const shapeClasses = {
      circle: 'rounded-full',
      square: 'rounded-lg',
    };

    const initials = useMemo(() => name ? getInitials(name) : '?', [name]);
    const bgColor = useMemo(() => name ? getColorFromName(name) : 'bg-brand-light text-brand', [name]);

    const showImage = src && src.length > 0;

    return (
      <div
        ref={ref}
        className={clsx('avatar', sizeClasses[size], shapeClasses[shape], className)}
        {...props}
      >
        {showImage ? (
          <img
            src={src}
            alt={alt || name || 'Avatar'}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        ) : (
          <span className={clsx('flex items-center justify-center w-full h-full font-medium', bgColor)}>
            {initials}
          </span>
        )}
      </div>
    );
  }
);

Avatar.displayName = 'Avatar';

export interface AvatarGroupProps extends HTMLAttributes<HTMLDivElement> {
  max?: number;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const AvatarGroup = forwardRef<HTMLDivElement, AvatarGroupProps>(
  ({ children, max = 5, size = 'md', className, ...props }, ref) => {
    const kids = Array.isArray(children) ? children : [children];
    const visible = kids.slice(0, max);
    const remaining = kids.length - max;

    return (
      <div ref={ref} className={clsx('flex -space-x-2', className)} {...props}>
        {visible.map((child, index) => (
          <span key={index} className="relative z-[auto]">
            {typeof child === 'object' && child !== null && 'props' in child
              ? cloneElement(child as ReactElement<any>, { size })
              : child}
          </span>
        ))}
        {remaining > 0 && (
          <div
            className={clsx('avatar', sizeClasses[size], 'bg-surface-sunken text-text-muted border-2 border-surface')}
          >
            +{remaining}
          </div>
        )}
      </div>
    );
  }
);

AvatarGroup.displayName = 'AvatarGroup';

const sizeClasses = {
  sm: 'avatar-sm',
  md: 'avatar-md',
  lg: 'avatar-lg',
  xl: 'avatar-xl',
};