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
  yellow2: '#E7E34E'
};

export const getColorForClass = (drugClass: string) => {
  const mapping: Record<string, string> = {
    'Carbapenem': PALETTE.purple1,
    'Polymyxin': PALETTE.pink3,
    'Aminoglycoside': PALETTE.blue2,
    'Fluoroquinolone': PALETTE.orange2,
    'Tetracycline': PALETTE.yellow1,
    'Sulfonamide': PALETTE.teal1,
    'Rifamycin': PALETTE.pink2,
  };
  return mapping[drugClass] || PALETTE.blue1;
};

export const getStatusColors = (sir: string) => {
  if (sir === "R") return { bg: "bg-red-900/20", text: "text-red-400", border: "border-red-900/50", fill: "#F87171" };
  if (sir === "I") return { bg: "bg-yellow-900/20", text: "text-yellow-400", border: "border-yellow-900/50", fill: "#FACC15" };
  if (sir === "S") return { bg: "bg-green-900/20", text: "text-green-400", border: "border-green-900/50", fill: "#4ADE80" };
  return { bg: "bg-surface-card", text: "text-text-muted", border: "border-surface-dark", fill: "#94A3B8" };
};
