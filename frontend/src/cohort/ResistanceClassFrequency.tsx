import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
} from 'recharts';
import { STATUS_HEX } from '../utils/palette';

export interface ClassFrequencyRow {
  category: string; // drug class or antibiotic
  R: number;
  I: number;
  S: number;
}

/**
 * Resistance Class Frequency — stacked S/I/R counts per drug class/antibiotic
 * across the cohort. Recharts (SVG, vector-exportable).
 */
export default function ResistanceClassFrequency({
  data,
  height = 340,
  asPercent = false,
}: {
  data: ClassFrequencyRow[];
  height?: number;
  asPercent?: boolean;
}) {
  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-text-muted text-sm">No phenotype data available.</div>;
  }

  const rows = asPercent
    ? data.map((d) => {
        const total = d.R + d.I + d.S || 1;
        return { category: d.category, R: (d.R / total) * 100, I: (d.I / total) * 100, S: (d.S / total) * 100 };
      })
    : data;

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 16, right: 16, bottom: 48, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis dataKey="category" stroke="#64748B" fontSize={11} angle={-40} textAnchor="end" interval={0} height={60} />
          <YAxis stroke="#64748B" fontSize={12}
                 label={{ value: asPercent ? 'Isolates (%)' : 'Isolates (n)', angle: -90, position: 'insideLeft', fill: '#64748B', fontSize: 12 }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', color: '#0F172A', fontSize: 12, borderRadius: 8 }}
            formatter={(v: any) => (asPercent ? `${Number(v).toFixed(1)}%` : v)}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="S" stackId="a" name="Susceptible" fill={STATUS_HEX.S} />
          <Bar dataKey="I" stackId="a" name="Intermediate" fill={STATUS_HEX.I} />
          <Bar dataKey="R" stackId="a" name="Resistant" fill={STATUS_HEX.R}>
            {rows.map((_, i) => <Cell key={i} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
