/**
 * Shared colour palette — light / clinical theme.
 * Aligns with tailwind.config.js tokens (status-r/i/s, accent-teal).
 */

export const PALETTE = {
  blue1: '#19AADE',
  blue2: '#1AC9E6',
  teal1: '#1DE4BD',
  teal2: '#6DF0D2',
  purple1: '#AF4BCE',
  pink1: '#DB4CB2',
  pink2: '#EB548C',
  pink3: '#EA7369',
  pink4: '#F0A58F',
  orange1: '#DE542C',
  orange2: '#EF7E32',
  orange3: '#EE9A3A',
  yellow1: '#EABD3B',
  yellow2: '#E7E34E',
};

/** Colour-blind-safe categorical palette (IBM Carbon) for drug classes etc. */
export const CATEGORICAL = [
  '#6929c4', '#1192e8', '#005d5d', '#9f1853', '#fa4d56',
  '#198038', '#002d9c', '#ee5396', '#b28600', '#009d9a',
  '#8a3800', '#a56eff', '#012749', '#570408',
];

export const ACCENT_TEAL = '#00AD9F';

/** Fixed S/I/R fill colours (match tailwind status-r/i/s tokens). */
export const STATUS_HEX: Record<string, string> = {
  R: '#F4503B',
  I: '#F5A623',
  S: '#2BC48A',
  NONE: '#6B7C85',
};

export const sirFill = (sir?: string | null): string =>
  STATUS_HEX[String(sir || '').toUpperCase()] ?? STATUS_HEX.NONE;

export const getColorForClass = (drugClass: string): string => {
  const mapping: Record<string, string> = {
    Carbapenem: PALETTE.purple1,
    Polymyxin: PALETTE.pink3,
    Aminoglycoside: PALETTE.blue2,
    Fluoroquinolone: PALETTE.orange2,
    Tetracycline: PALETTE.yellow1,
    Sulfonamide: PALETTE.teal1,
    Rifamycin: PALETTE.pink2,
  };
  return mapping[drugClass] || PALETTE.blue1;
};

/** Deterministic categorical colour for an arbitrary label. */
export const colorForLabel = (label: string, index?: number): string => {
  if (typeof index === 'number') return CATEGORICAL[index % CATEGORICAL.length];
  let hash = 0;
  for (let i = 0; i < label.length; i++) hash = (hash * 31 + label.charCodeAt(i)) | 0;
  return CATEGORICAL[Math.abs(hash) % CATEGORICAL.length];
};

/** Light-theme S/I/R tailwind utility classes for badges/cells. */
export const getStatusColors = (sir: string) => {
  if (sir === 'R') return { bg: 'bg-status-r/10', text: 'text-status-r', border: 'border-status-r/30', fill: STATUS_HEX.R };
  if (sir === 'I') return { bg: 'bg-status-i/10', text: 'text-status-i', border: 'border-status-i/30', fill: STATUS_HEX.I };
  if (sir === 'S') return { bg: 'bg-status-s/10', text: 'text-status-s', border: 'border-status-s/30', fill: STATUS_HEX.S };
  return { bg: 'bg-surface', text: 'text-text-muted', border: 'border-surface-dark', fill: STATUS_HEX.NONE };
};
