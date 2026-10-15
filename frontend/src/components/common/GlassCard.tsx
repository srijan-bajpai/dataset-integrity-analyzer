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

    const rotX = ((y - centerY) / centerY) * -6; // max 6 deg tilt
    const rotY = ((x - centerX) / centerX) * 6;

    setRotateX(rotX);
    setRotateY(rotY);

    setGlarePosition({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
      opacity: 0.15,
    });
  };

  const handleMouseLeave = () => {
    if (!tilt) return;
    setRotateX(0);
    setRotateY(0);
    setGlarePosition(prev => ({ ...prev, opacity: 0 }));
  };

  const glowClass = {
    emerald: 'hover:shadow-glow-emerald hover:border-emerald-500/40',
    sky: 'hover:shadow-glow-sky hover:border-sky-500/40',
    amber: 'hover:shadow-glow-amber hover:border-amber-500/40',
    rose: 'hover:shadow-glow-rose hover:border-rose-500/40',
    indigo: 'hover:shadow-glow-indigo hover:border-indigo-500/40',
    none: 'hover:border-zinc-700/80 dark:hover:border-zinc-700/80',
  }[glow];

  const elevationClass = {
    sm: 'shadow-glass-sm',
    md: 'shadow-glass',
    lg: 'shadow-2xl',
  }[elevation];

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: tilt ? `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)` : undefined,
        transition: 'transform 0.15s ease-out, box-shadow 0.25s ease, border-color 0.2s ease',
      }}
      className={cn(
        'relative rounded-2xl glass-card specular-border overflow-hidden p-5',
        elevationClass,
        glowClass,
        className
      )}
      {...props}
    >
      {/* Dynamic Specular Glare */}
      {tilt && (
        <div
          className="pointer-events-none absolute inset-0 transition-opacity duration-300 z-10"
          style={{
            opacity: glarePosition.opacity,
            background: `radial-gradient(circle 280px at ${glarePosition.x}% ${glarePosition.y}%, rgba(255, 255, 255, 0.4), transparent 70%)`,
          }}
        />
      )}
      <div className="relative z-20">{children}</div>
    </div>
  );
};
