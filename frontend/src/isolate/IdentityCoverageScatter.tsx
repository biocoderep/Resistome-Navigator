import React, { useMemo } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine, Legend,
} from 'recharts';
import { useAmrGenes } from '../hooks/useAmrData';
import { CATEGORICAL } from '../utils/palette';

/**
 * Identity vs Coverage scatter for a single isolate — visualises AMR gene-call
 * confidence. Points are coloured by drug class and sized by confidence; the
 * dashed guides mark the 95% identity / 80% coverage quality thresholds.
 */
export default function IdentityCoverageScatter({ sampleId }: { sampleId: string }) {
  const { data: genes, loading, error } = useAmrGenes(sampleId);

  const { points, classes } = useMemo(() => {
    const pts = (genes || []).map((g: any) => ({
      gene: g.gene_name,
      drugClass: g.drug_class || 'Unknown',
      identity: Number(g.identity_pct ?? g.identity_percent ?? 0),
      coverage: Number(g.coverage_pct ?? g.coverage_percent ?? 0),
      // size weight from confidence (accepts 0-1 or 0-100 scales)
      z: 60 + 240 * normaliseConfidence(g.confidence_score),
    }));
    const cls = Array.from(new Set(pts.map((p) => p.drugClass)));
    return { points: pts, classes: cls };
  }, [genes]);

  if (loading) return <div className="h-80 animate-pulse bg-surface rounded-lg" />;
  if (error) return <div className="h-80 flex items-center justify-center text-status-r text-sm">Failed to load gene data.</div>;
  if (points.length === 0) return <div className="h-80 flex items-center justify-center text-text-muted text-sm">No AMR genes detected.</div>;

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 16, right: 24, bottom: 24, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis
            type="number" dataKey="coverage" name="Coverage" unit="%"
            domain={[Math.min(60, ...points.map((p) => p.coverage)), 100]}
            stroke="#64748B" fontSize={12}
            label={{ value: 'Coverage (%)', position: 'insideBottom', offset: -12, fill: '#64748B', fontSize: 12 }}
          />
          <YAxis
            type="number" dataKey="identity" name="Identity" unit="%"
            domain={[Math.min(60, ...points.map((p) => p.identity)), 100]}
            stroke="#64748B" fontSize={12}
            label={{ value: 'Identity (%)', angle: -90, position: 'insideLeft', fill: '#64748B', fontSize: 12 }}
          />
          <ZAxis type="number" dataKey="z" range={[60, 300]} />
          <ReferenceLine y={95} stroke="#F5A623" strokeDasharray="4 4" />
          <ReferenceLine x={80} stroke="#F5A623" strokeDasharray="4 4" />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', color: '#0F172A', fontSize: 12, borderRadius: 8 }}
            formatter={(value: any, name: any) => [`${value}`, name]}
            labelFormatter={() => ''}
          />
          <Scatter name="AMR genes" data={points}>
            {points.map((p, i) => (
              <Cell key={i} fill={CATEGORICAL[classes.indexOf(p.drugClass) % CATEGORICAL.length]} fillOpacity={0.8} />
            ))}
          </Scatter>
          <Legend
            payload={classes.slice(0, 10).map((c, i) => ({
              value: c, type: 'circle', id: c,
              color: CATEGORICAL[i % CATEGORICAL.length],
            }))}
            wrapperStyle={{ fontSize: 11 }}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

function normaliseConfidence(value: any): number {
  const n = Number(value ?? 0);
  if (!isFinite(n)) return 0.5;
  return n > 1 ? Math.min(n / 100, 1) : Math.min(Math.max(n, 0), 1);
}
