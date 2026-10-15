import React from 'react';
import { getReadinessColor, getReadinessTier } from '../../lib/utils';
import { ShieldCheck, AlertOctagon, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface ReadinessGauge3DProps {
  score: number;
  verdict?: string;
  coveragePct?: number;
  size?: number;
}

export const ReadinessGauge3D: React.FC<ReadinessGauge3DProps> = ({
  score,
  verdict,
  coveragePct = 100,
  size = 240,
}) => {
  const colors = getReadinessColor(score);
  const tier = getReadinessTier(score);

  // SVG circular arc geometry
  const strokeWidth = 14;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  // Use a 270-degree arc gauge
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (arcLength * Math.min(Math.max(score, 0), 100)) / 100;

  const getIcon = () => {
    switch (tier) {
      case 'ready':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'acceptable':
        return <ShieldCheck className="w-5 h-5 text-sky-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      case 'critical':
        return <AlertOctagon className="w-5 h-5 text-rose-400" />;
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center select-none py-2">
      {/* Background ambient radial glow */}
      <div
        className="absolute w-44 h-44 rounded-full blur-3xl opacity-30 pointer-events-none transition-all duration-700"
        style={{ backgroundColor: colors.hex }}
      />

      {/* SVG Arc Gauge */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="rotate-[135deg] transform origin-center"
        >
          {/* Track background */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
            className="text-zinc-800/80 dark:text-zinc-800/60"
          />

          {/* Value Progress Stroke */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={colors.hex}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1), stroke 0.5s ease',
              filter: `drop-shadow(0 0 10px ${colors.hex}80)`,
            }}
          />
        </svg>

        {/* Center Readout & Diagnosis */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-4">
          <div className="flex items-center gap-1.5 mb-0.5">
            {getIcon()}
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-zinc-400">
              Readiness
            </span>
          </div>

          <div className="flex items-baseline justify-center gap-1">
            <span className="text-5xl font-black font-sans tracking-tight text-white drop-shadow-md">
              {Math.round(score)}
            </span>
            <span className="text-zinc-500 font-mono text-sm">/ 100</span>
          </div>

          <div
            className={`mt-1 text-xs font-semibold px-2.5 py-0.5 rounded-full border tracking-wide uppercase font-mono ${colors.bg} ${colors.border} ${colors.text}`}
          >
            {verdict || (
              tier === 'ready' ? 'Production Ready' :
              tier === 'acceptable' ? 'Acceptable' :
              tier === 'warning' ? 'Needs Fixes' : 'Critical Blocker'
            )}
          </div>

          <span className="text-[10px] text-zinc-500 font-mono mt-1">
            {coveragePct}% dimensions assessed
          </span>
        </div>
      </div>
    </div>
  );
};
