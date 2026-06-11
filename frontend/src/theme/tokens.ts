/**
 * Design Tokens
 * Centralised theming configuration for the AMR Characterisation Engine
 */

export const colors = {
  // Fixed phenotype colours as mandated
  phenotype: {
    S: '#2E7D32', // Green
    I: '#F9A825', // Yellow/Orange
    R: '#C62828', // Red
  },
  
  // Interpretation tier colours
  confidence: {
    HIGH: '#005d5d', // Deep Teal
    MEDIUM: '#0f62fe', // Bright Blue
    LOW: '#8a3800', // Brown/Orange
    INSUFFICIENT: '#878d96', // Grey
  },
  
  // IBM Carbon-inspired colour-blind safe palette for categorical data (e.g., drug classes, organisms)
  categorical: [
    '#6929c4', // Purple
    '#1192e8', // Cyan
    '#005d5d', // Teal
    '#9f1853', // Magenta
    '#fa4d56', // Red
    '#570408', // Dark Red
    '#198038', // Green
    '#002d9c', // Dark Blue
    '#ee5396', // Pink
    '#b28600', // Gold
    '#009d9a', // Mint
    '#012749', // Navy
    '#8a3800', // Rust
    '#a56eff', // Lavender
  ],

  // Background and surface colours
  surface: {
    base: '#F3F4F6', // gray-100
    card: '#FFFFFF',
    border: '#E5E7EB', // gray-200
  },

  // Typography colours
  text: {
    primary: '#111827', // gray-900
    secondary: '#4B5563', // gray-600
    muted: '#9CA3AF', // gray-400
  }
};

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px'
};

export const typography = {
  fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontSize: {
    sm: '12px',
    base: '14px',
    lg: '16px',
    xl: '20px',
    title: '24px'
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    bold: 700
  }
};

export const theme = {
  colors,
  spacing,
  typography
};
