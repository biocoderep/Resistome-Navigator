import React from 'react';

type SIR = 'R' | 'I' | 'S' | 'NOT_TESTABLE';

export const SirBadge = ({ sir }: { sir: SIR }) => {
  let bgColor = 'bg-status-none';
  let textColor = 'text-white';
  let label = sir;

  if (sir === 'R') bgColor = 'bg-status-r';
  if (sir === 'I') bgColor = 'bg-status-i';
  if (sir === 'S') bgColor = 'bg-status-s';
  if (sir === 'NOT_TESTABLE') label = 'N/A';

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-bold ${bgColor} ${textColor}`}>
      {label}
    </span>
  );
};
