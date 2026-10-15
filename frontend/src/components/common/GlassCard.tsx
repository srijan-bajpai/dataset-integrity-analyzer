import React, { useRef, useState } from 'react';
import { cn } from '../../lib/utils';

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  tilt?: boolean;
  elevation?: 'sm' | 'md' | 'lg';
  glow?: 'emerald' | 'sky' | 'amber' | 'rose' | 'indigo' | 'none';
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  tilt = true,
  elevation = 'md',
  glow = 'none',
  className,
  ...props
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const [glarePosition, setGlarePosition] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!tilt || !cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotX = ((y - centerY) / centerY) * -4; // max 4 deg gentle tilt
    const rotY = ((x - centerX) / centerX) * 4;

    setRotateX(rotX);
    setRotateY(rotY);

    setGlarePosition({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
      opacity: 0.12,
    });
  };

  const handleMouseLeave = () => {
    if (!tilt) return;
    setRotateX(0);
    setRotateY(0);
    setGlarePosition(prev => ({ ...prev, opacity: 0 }));
  };

  const glowClass = {
    emerald: 'hover:border-emerald-500/50 hover:shadow-[0_12px_32px_-4px_rgba(21,128,61,0.12)]',
    sky: 'hover:border-sky-500/50 hover:shadow-[0_12px_32px_-4px_rgba(3,105,161,0.12)]',
    amber: 'hover:border-amber-500/50 hover:shadow-[0_12px_32px_-4px_rgba(180,83,9,0.12)]',
    rose: 'hover:border-rose-500/50 hover:shadow-[0_12px_32px_-4px_rgba(190,18,60,0.12)]',
    indigo: 'hover:border-indigo-500/50 hover:shadow-[0_12px_32px_-4px_rgba(99,102,241,0.12)]',
    none: 'hover:border-stone-300 dark:hover:border-stone-700',
  }[glow];

  const elevationClass = {
    sm: 'shadow-warm-sm',
    md: 'shadow-warm-md',
    lg: 'shadow-warm-lg',
  }[elevation];

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: tilt ? `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)` : undefined,
        transition: 'transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease, border-color 0.2s ease',
      }}
      className={cn(
        'relative rounded-3xl bg-white dark:bg-[#221F1D] border border-stone-200/80 dark:border-stone-800/80 overflow-hidden p-6 tactile-card',
        elevationClass,
        glowClass,
        className
      )}
      {...props}
    >
      {/* Dynamic Specular Daylight Glare */}
      {tilt && (
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-300 z-10"
          style={{
            opacity: glarePosition.opacity,
            background: `radial-gradient(circle 320px at ${glarePosition.x}% ${glarePosition.y}%, rgba(255, 255, 255, 0.6), transparent 70%)`,
          }}
        />
      )}
      <div className="relative z-20">{children}</div>
    </div>
  );
};
