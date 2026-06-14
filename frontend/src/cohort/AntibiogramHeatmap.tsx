import React from 'react';
import { sirFill, STATUS_HEX } from '../utils/palette';

export interface AntibiogramIsolate {
  id: string;
  label: string;
  profile: Record<string, string>; // antibiotic -> S/I/R
}

/**
 * Clinical Antibiogram Heatmap — isolates on the Y axis, antibiotics on the X
 * axis, cells coloured by predicted S/I/R. Pure SVG (vector-exportable).
 */
export default function AntibiogramHeatmap({
  isolates,
  antibiotics,
  cell = 22,
}: {
  isolates: AntibiogramIsolate[];
  antibiotics: string[];
  cell?: number;
}) {
  if (!isolates.length || !antibiotics.length) {
    return <div className="h-64 flex items-center justify-center text-text-muted text-sm">No susceptibility data available.</div>;
  }

  const marginLeft = 150;
  const marginTop = 96;
  const legendH = 40;
  const gridW = antibiotics.length * cell;
  const gridH = isolates.length * cell;
  const width = marginLeft + gridW + 16;
  const height = marginTop + gridH + legendH;

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${height}`} width={Math.max(width, 320)} role="img" aria-label="Antibiogram heatmap">
        {/* antibiotic labels (rotated) */}
        {antibiotics.map((ab, c) => {
          const x = marginLeft + c * cell + cell / 2;
          return (
            <text key={ab} x={x} y={marginTop - 6} fontSize={11} fill="#0F172A"
                  transform={`rotate(-45 ${x} ${marginTop - 6})`} textAnchor="start" fontFamily="monospace">
              {ab}
            </text>
          );
        })}

        {/* rows */}
        {isolates.map((iso, r) => {
          const y = marginTop + r * cell;
          return (
            <g key={iso.id}>
              <text x={marginLeft - 8} y={y + cell / 2} fontSize={10} fill="#0F172A"
                    textAnchor="end" dominantBaseline="middle" fontFamily="monospace">
                {truncate(iso.label, 20)}
              </text>
              {antibiotics.map((ab, c) => {
                const sir = (iso.profile[ab] || '').toUpperCase();
                return (
                  <rect key={ab} x={marginLeft + c * cell} y={y} width={cell - 1.5} height={cell - 1.5}
                        rx={2} fill={sirFill(sir)}>
                    <title>{`${iso.label} · ${ab}: ${sir || 'N/A'}`}</title>
                  </rect>
                );
              })}
            </g>
          );
        })}

        {/* legend */}
        {[
          { k: 'S', t: 'Susceptible' },
          { k: 'I', t: 'Intermediate' },
          { k: 'R', t: 'Resistant' },
          { k: 'NONE', t: 'No data' },
        ].map((item, i) => (
          <g key={item.k} transform={`translate(${marginLeft + i * 130}, ${marginTop + gridH + 18})`}>
            <rect width={14} height={14} rx={3} fill={STATUS_HEX[item.k]} />
            <text x={20} y={11} fontSize={11} fill="#64748B">{item.t}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function truncate(s: string, n: number): string {
  return s.length <= n ? s : s.slice(0, n - 1) + '…';
}
