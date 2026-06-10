import React from 'react';

type SIR = 'R' | 'I' | 'S' | 'NOT_TESTABLE';

export const getBadgeStyle = (sir: SIR | 'NOT_TESTABLE' | 'N/A' | string) => {
  switch (sir) {
    case 'S': return 'bg-[#198038]/10 text-[#198038] border-[#198038]/20';
    case 'I': return 'bg-[#b28600]/10 text-[#b28600] border-[#b28600]/20';
    case 'R': return 'bg-[#da1e28]/10 text-[#da1e28] border-[#da1e28]/20';
    default: return 'bg-surface-dark text-text-muted border-surface-dark';
  }
};

export const SirBadge = ({ sir }: { sir: SIR }) => {
  const style = getBadgeStyle(sir);
  const label = sir === 'NOT_TESTABLE' ? 'N/A' : sir;

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-bold border ${style}`}>
      {label}
    </span>
  );
};
