import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export type ReadinessTier = 'ready' | 'acceptable' | 'warning' | 'critical';

export function getReadinessTier(score: number): ReadinessTier {
  if (score >= 80) return 'ready';
  if (score >= 65) return 'acceptable';
  if (score >= 45) return 'warning';
  return 'critical';
}

export function getReadinessColor(score: number): {
  text: string;
  bg: string;
  border: string;
  glow: string;
  gradient: string;
  hex: string;
} {
  const tier = getReadinessTier(score);
  switch (tier) {
    case 'ready':
      return {
        text: 'text-emerald-400',
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30',
        glow: 'shadow-glow-emerald',
        gradient: 'from-emerald-500 to-teal-400',
        hex: '#10b981',
      };
    case 'acceptable':
      return {
        text: 'text-sky-400',
        bg: 'bg-sky-500/10',
        border: 'border-sky-500/30',
        glow: 'shadow-glow-sky',
        gradient: 'from-sky-500 to-blue-400',
        hex: '#0ea5e9',
      };
    case 'warning':
      return {
        text: 'text-amber-400',
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
        glow: 'shadow-glow-amber',
        gradient: 'from-amber-500 to-orange-400',
        hex: '#f59e0b',
      };
    case 'critical':
      return {
        text: 'text-rose-400',
        bg: 'bg-rose-500/10',
        border: 'border-rose-500/30',
        glow: 'shadow-glow-rose',
        gradient: 'from-rose-500 to-red-400',
        hex: '#f43f5e',
      };
  }
}

export function formatPercent(value: number | undefined | null, decimals = 1): string {
  if (value === undefined || value === null) return 'N/A';
  return `${(value * (value <= 1 && value > 0 ? 100 : 1)).toFixed(decimals)}%`;
}

// Plain-English translations (ELI5 Mode)
export const ELI5_TRANSLATIONS: Record<string, { title: string; simple: string; technical: string }> = {
  distribution: {
    title: 'Class Balance',
    simple: 'Are you giving the AI an equal chance to learn every category, or is one category drowning out the others?',
    technical: 'Class distribution entropy, Gini coefficient, and min/max imbalance ratio across labels.',
  },
  fairness: {
    title: 'Fairness & Representation',
    simple: 'Does your dataset fairly represent all protected demographic groups, or does it leave certain groups under-represented?',
    technical: 'Max absolute gap against specified demographic targets and conditional class parity.',
  },
  quality: {
    title: 'Image Clarity & Quality',
    simple: 'Are there photos that are too blurry, too dark, washed out, or low resolution for the AI to recognize?',
    technical: 'Defect rate computed over Laplacian variance, luminance clipping, michelson contrast, and dimension bounds.',
  },
  duplicates: {
    title: 'Duplicates & Leakage',
    simple: 'Are identical or nearly identical photos repeated? Critically, did photos from your test set sneak into your training set?',
    technical: 'Perceptual hashing (pHash) Hamming distance <= 6, near-duplicate clusters, and cross-split leakage groups.',
  },
  diversity: {
    title: 'Visual Variety & Outliers',
    simple: 'Do your photos show diverse angles, lighting, and variations, or are they repetitive copies with weird outliers?',
    technical: 'Feature embedding cosine distance, Silhouette score-optimized k-means clustering entropy, and DBSCAN noise rate.',
  },
  labels: {
    title: 'Label Accuracy',
    simple: 'Did a human tag an image with the wrong name? (e.g. tagging a dog as a cat).',
    technical: 'Confident Learning out-of-fold predicted probability matrix and suspected mislabel flags.',
  },
  c1_confounds: {
    title: 'Hidden Traps (Cross-Dimensions)',
    simple: 'When two dataset problems sneak together—for example, when almost all photos of Category A happen to be dark and blurry, teaching the AI to cheat.',
    technical: 'Bivariate interaction tests (Kruskal-Wallis effect size epsilon^2, Pearson r, chi-squared) with Benjamini-Hochberg FDR correction.',
  },
  c2_impact: {
    title: 'Projected Model Accuracy Impact',
    simple: 'If you train your AI model on this messy dataset, how much accuracy will you lose on real-world test data?',
    technical: 'Empirical synthetic degradation curve modeling downstream test accuracy loss and uncertainty bounds.',
  },
};
