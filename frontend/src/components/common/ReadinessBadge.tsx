import React from 'react';
import { cn, getReadinessColor, getReadinessTier } from '../../lib/utils';

interface ReadinessBadgeProps {
  score?: number;
  verdict?: string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
  className?: string;
}

export const ReadinessBadge: React.FC<ReadinessBadgeProps> = ({
  score = 0,
  verdict,
  size = 'md',
  showDot = true,
  className,
}) => {
  const colors = getReadinessColor(score);
  const tier = getReadinessTier(score);

  const displayVerdict = verdict || (
    tier === 'ready' ? 'Production Ready' :
    tier === 'acceptable' ? 'Acceptable' :
    tier === 'warning' ? 'Needs Remediation' : 'Critical Blocker'
  );

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1.5',
    md: 'text-xs font-medium px-2.5 py-1 gap-2',
    lg: 'text-sm font-semibold px-3 py-1.5 gap-2.5',
  }[size];

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border tracking-wide uppercase font-mono shadow-sm',
        colors.bg,
        colors.border,
        colors.text,
        sizeClasses,
        className
      )}
    >
      {showDot && (
        <span className="relative flex h-2 w-2">
          <span
            className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
            style={{ backgroundColor: colors.hex }}
          />
          <span
            className="relative inline-flex rounded-full h-2 w-2"
            style={{ backgroundColor: colors.hex }}
          />
        </span>
      )}
      <span>{displayVerdict}</span>
      {score !== undefined && (
        <span className="opacity-75 font-sans font-bold">[{Math.round(score)}]</span>
      )}
    </span>
  );
};
