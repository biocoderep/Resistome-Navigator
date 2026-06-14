import React, { useMemo } from 'react';
import { useAmrGenes, useVirulenceGenes } from '../hooks/useAmrData';

const AMR_COLOR = '#F4503B';      // status-r
const VIR_COLOR = '#00AD9F';      // accent-teal
const CHROM_COLOR = '#94A3B8';    // slate
const PLASMID_COLOR = '#AF4BCE';  // purple
const GRID = '#E2E8F0';
const TEXT = '#0F172A';
const MUTED = '#64748B';

interface Contig {
  id: string;
  length: number;
  isPlasmid: boolean;
  startDeg: number;
  spanDeg: number;
}

const polar = (cx: number, cy: number, r: number, deg: number) => {
  const a = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) };
};

const annularArc = (cx: number, cy: number, r: number, t: number, a0: number, a1: number) => {
  const ro = r + t / 2;
  const ri = r - t / 2;
  const p1 = polar(cx, cy, ro, a0);
  const p2 = polar(cx, cy, ro, a1);
  const p3 = polar(cx, cy, ri, a1);
  const p4 = polar(cx, cy, ri, a0);
  const large = a1 - a0 > 180 ? 1 : 0;
  return `M${p1.x},${p1.y} A${ro},${ro} 0 ${large} 1 ${p2.x},${p2.y} L${p3.x},${p3.y} A${ri},${ri} 0 ${large} 0 ${p4.x},${p4.y} Z`;
};

const isPlasmid = (id: string) => /plasmid|^p[0-9]|_p[_0-9]/i.test(id);

/**
 * Circular genome viewer for a single isolate. Contigs form the backbone ring
 * (chromosome vs plasmid coloured), AMR genes are ticks on the outer ring, and
 * virulence genes on the inner ring. Pure SVG so it exports as vector.
 */
export default function CircularGenomeViewer({ sampleId, size = 560 }: { sampleId: string; size?: number }) {
  const { data: amrGenes, loading: l1 } = useAmrGenes(sampleId);
  const { data: virGenes, loading: l2 } = useVirulenceGenes(sampleId);

  const model = useMemo(() => {
    const lengths: Record<string, number> = {};
    const mark = (g: any) => {
      const cid = g.contig_id || 'contig_1';
      const end = Number(g.end ?? g.end_position ?? 0) + 5000;
      lengths[cid] = Math.max(lengths[cid] || 50000, end);
    };
    (amrGenes || []).forEach(mark);
    (virGenes || []).forEach(mark);

    const ids = Object.keys(lengths);
    if (ids.length === 0) return null;

    const total = ids.reduce((s, id) => s + lengths[id], 0);
    const GAP = 3; // degrees between contigs
    const usable = 360 - GAP * ids.length;

    let cursor = 0;
    const contigs: Contig[] = ids.map((id) => {
      const span = (lengths[id] / total) * usable;
      const c: Contig = { id, length: lengths[id], isPlasmid: isPlasmid(id), startDeg: cursor, spanDeg: span };
      cursor += span + GAP;
      return c;
    });
    const byId: Record<string, Contig> = Object.fromEntries(contigs.map((c) => [c.id, c]));
    return { contigs, byId, total };
  }, [amrGenes, virGenes]);

  if (l1 || l2) return <div className="h-[360px] animate-pulse bg-surface rounded-lg" />;
  if (!model) return <div className="h-[360px] flex items-center justify-center text-text-muted text-sm">No genomic mapping data.</div>;

  const cx = size / 2;
  const cy = size / 2;
  const R = size * 0.34;
  const BACKBONE_T = size * 0.028;

  const geneAngle = (g: any) => {
    const c = model.byId[g.contig_id || 'contig_1'];
    if (!c) return null;
    const pos = Number(g.start ?? g.start_position ?? 0);
    return c.startDeg + Math.min(pos / c.length, 1) * c.spanDeg;
  };

  const tick = (g: any, rInner: number, rOuter: number, color: string, key: string) => {
    const deg = geneAngle(g);
    if (deg == null) return null;
    const a = polar(cx, cy, rInner, deg);
    const b = polar(cx, cy, rOuter, deg);
    return <line key={key} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={color} strokeWidth={2} strokeLinecap="round" />;
  };

  return (
    <div className="w-full flex justify-center">
      <svg viewBox={`0 0 ${size} ${size}`} width="100%" style={{ maxWidth: size }} role="img" aria-label="Circular genome viewer">
        {/* faint guide rings */}
        <circle cx={cx} cy={cy} r={R + size * 0.075} fill="none" stroke={GRID} strokeWidth={1} />
        <circle cx={cx} cy={cy} r={R - size * 0.075} fill="none" stroke={GRID} strokeWidth={1} />

        {/* contig backbone */}
        {model.contigs.map((c) => (
          <path
            key={c.id}
            d={annularArc(cx, cy, R, BACKBONE_T, c.startDeg, c.startDeg + c.spanDeg)}
            fill={c.isPlasmid ? PLASMID_COLOR : CHROM_COLOR}
            opacity={c.isPlasmid ? 0.85 : 0.5}
          />
        ))}

        {/* AMR gene ticks (outer) */}
        {(amrGenes || []).map((g: any, i: number) =>
          tick(g, R + BACKBONE_T / 2, R + size * 0.06, AMR_COLOR, `amr-${i}`),
        )}

        {/* Virulence gene ticks (inner) */}
        {(virGenes || []).map((g: any, i: number) =>
          tick(g, R - size * 0.06, R - BACKBONE_T / 2, VIR_COLOR, `vir-${i}`),
        )}

        {/* contig labels */}
        {model.contigs.map((c) => {
          const mid = c.startDeg + c.spanDeg / 2;
          const p = polar(cx, cy, R + size * 0.11, mid);
          const anchor = p.x < cx - 4 ? 'end' : p.x > cx + 4 ? 'start' : 'middle';
          return (
            <text key={`lbl-${c.id}`} x={p.x} y={p.y} fontSize={size * 0.018} fill={MUTED}
                  textAnchor={anchor} dominantBaseline="middle" fontFamily="monospace">
              {c.id}
            </text>
          );
        })}

        {/* centre summary */}
        <text x={cx} y={cy - 8} textAnchor="middle" fontSize={size * 0.05} fontWeight={700} fill={TEXT}>
          {(model.total / 1_000_000).toFixed(2)} Mb
        </text>
        <text x={cx} y={cy + 14} textAnchor="middle" fontSize={size * 0.022} fill={MUTED}>
          {model.contigs.length} contig{model.contigs.length > 1 ? 's' : ''}
        </text>

        {/* legend */}
        {[
          { c: AMR_COLOR, t: 'AMR gene' },
          { c: VIR_COLOR, t: 'Virulence' },
          { c: PLASMID_COLOR, t: 'Plasmid' },
          { c: CHROM_COLOR, t: 'Chromosome' },
        ].map((item, i) => (
          <g key={item.t} transform={`translate(${size * 0.04}, ${size - size * 0.10 + i * size * 0.026})`}>
            <rect width={size * 0.02} height={size * 0.02} rx={2} fill={item.c} />
            <text x={size * 0.028} y={size * 0.017} fontSize={size * 0.02} fill={MUTED}>{item.t}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}
