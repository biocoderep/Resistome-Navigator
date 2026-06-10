import React, { useState, useMemo } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, BarChart, Bar } from "recharts";
import * as d3 from "d3";
import _ from "lodash";

import DimReductionPlot from './components/charts/DimReductionPlot';
import CoOccurrenceNetwork from './components/charts/CoOccurrenceNetwork';
import MinimumSpanningTree from './components/charts/MinimumSpanningTree';

const FONT = "system-ui, -apple-system, sans-serif";
const MONO = "'SF Mono', 'Fira Code', monospace";

// ── Seeded RNG ──
const rng = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(42);
const rng2 = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(99);
const rng3 = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(77);

// ── Color Palettes ──
const PHENO_COLORS: any = { MDR: "#E63946", XDR: "#8338EC", Susceptible: "#2A9D8F", PDR: "#264653" };
const ST_COLORS: any = { ST258: "#E63946", ST11: "#457B9D", ST307: "#8338EC", ST15: "#F4845F", ST147: "#2A9D8F" };
const MECH_COLORS: any = {
  "Antibiotic inactivation": "#E63946", "Efflux pump": "#457B9D", "Target alteration": "#8338EC",
  "Target protection": "#F4845F", "Target replacement": "#2A9D8F", "Reduced permeability": "#E9C46A",
};
const SIG_COLORS: any = { up: "#E63946", down: "#457B9D", ns: "#CBD5E1" };

// ── AMR Gene List ──
const AMR_GENES = ["blaNDM-1","mcr-1","aac(6')-Ib","qnrS1","tet(A)","sul1","blaOXA-48","armA","blaCTX-M-15","dfrA12","catA1","aph(3')-Ia","ere(A)","blaKPC-3","arr-3","vanA","cfr","fosA","mph(A)","rmtB"];

// ══════════════════════════════════════
// DATA GENERATORS
// ══════════════════════════════════════

function genVolcanoData() {
  return AMR_GENES.map((g, i) => {
    const lfc = (rng() - 0.4) * 6;
    const pval = Math.pow(10, -(rng() * 8 + 0.5));
    const negLogP = -Math.log10(pval);
    const sig = Math.abs(lfc) >= 1 && negLogP >= 2 ? (lfc > 0 ? "up" : "down") : "ns";
    return { gene: g, lfc: +lfc.toFixed(2), negLogP: +negLogP.toFixed(2), pval, sig };
  });
}

function genPCAData() {
  const phenotypes = ["MDR", "MDR", "MDR", "XDR", "XDR", "Susceptible", "Susceptible", "Susceptible", "MDR", "XDR",
    "Susceptible", "MDR", "XDR", "Susceptible", "MDR", "MDR", "Susceptible", "XDR", "MDR", "Susceptible",
    "MDR", "XDR", "Susceptible", "MDR", "Susceptible", "XDR", "MDR", "Susceptible", "MDR", "XDR"];
  const centers: any = { MDR: [2, 1], XDR: [4, -2], Susceptible: [-3, 0.5] };
  return phenotypes.map((p, i) => ({
    id: `KP-${String(i + 1).padStart(3, "0")}`, phenotype: p,
    pc1: +(centers[p][0] + (rng() - 0.5) * 3).toFixed(2),
    pc2: +(centers[p][1] + (rng() - 0.5) * 2.5).toFixed(2),
  }));
}

function genHeatmapData() {
  const isolates = Array.from({ length: 30 }, (_, i) => `KP-${String(i + 1).padStart(3, "0")}`);
  const genes = AMR_GENES.slice(0, 15);
  const matrix = isolates.map(iso => {
    const row: any = {};
    genes.forEach(g => { row[g] = rng2() < 0.55 ? +(85 + rng2() * 15).toFixed(1) : 0; });
    return { isolate: iso, ...row };
  });
  return { isolates, genes, matrix };
}

function genUMAPData() {
  const sts = Object.keys(ST_COLORS);
  const centers: any = { ST258: [-3, 2], ST11: [2.5, 3], ST307: [4, -2], ST15: [-1, -3.5], ST147: [-4.5, -0.5] };
  const points: any[] = [];
  sts.forEach(st => {
    const n = 8 + Math.floor(rng3() * 8);
    for (let i = 0; i < n; i++) {
      points.push({
        id: `KP-${String(points.length + 1).padStart(3, "0")}`, st,
        u1: +(centers[st][0] + (rng3() - 0.5) * 2.5).toFixed(2),
        u2: +(centers[st][1] + (rng3() - 0.5) * 2.5).toFixed(2),
        ndm1: st === "ST11" ? +(80 + rng3() * 20).toFixed(1) : +(rng3() * 40).toFixed(1),
      });
    }
  });
  return points;
}

function genViolinData() {
  const genes = ["blaNDM-1", "mcr-1", "aac(6')-Ib", "qnrS1", "tet(A)", "blaOXA-48"];
  const groups = ["MDR", "XDR", "Susceptible"];
  const data: any[] = [];
  genes.forEach(gene => {
    groups.forEach(grp => {
      const n = 15 + Math.floor(rng() * 10);
      const base = grp === "Susceptible" ? 20 : grp === "MDR" ? 75 : 85;
      const spread = grp === "Susceptible" ? 30 : 15;
      for (let i = 0; i < n; i++) {
        data.push({ gene, group: grp, identity: +(Math.max(0, Math.min(100, base + (rng() - 0.5) * spread * 2))).toFixed(1) });
      }
    });
  });
  return { genes, groups, data };
}

function genMechCompData() {
  const mechs = Object.keys(MECH_COLORS);
  return Array.from({ length: 25 }, (_, i) => {
    const raw = mechs.map(() => rng() * 10);
    const total = raw.reduce((a, b) => a + b, 0);
    const row: any = { isolate: `KP-${String(i + 1).padStart(3, "0")}` };
    mechs.forEach((m, j) => { row[m] = +((raw[j] / total) * 100).toFixed(1); });
    return row;
  });
}

// ══════════════════════════════════════
// SHARED UI
// ══════════════════════════════════════
const Card = ({ title, subtitle, children }: any) => (
  <div style={{ background: "#FFF", borderRadius: 10, border: "1px solid #E5E7EB", padding: 20, marginBottom: 16, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
    <div style={{ marginBottom: 12 }}>
      <h3 style={{ fontSize: 14, fontWeight: 700, color: "#111827", margin: 0, fontFamily: FONT }}>{title}</h3>
      {subtitle && <p style={{ fontSize: 11, color: "#9CA3AF", margin: "3px 0 0", fontFamily: FONT }}>{subtitle}</p>}
    </div>
    {children}
  </div>
);

const ChipLegend = ({ items }: any) => (
  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
    {items.map(({ color, label }: any) => (
      <div key={label} style={{ display: "flex", alignItems: "center", gap: 5 }}>
        <div style={{ width: 10, height: 10, borderRadius: 3, background: color }} />
        <span style={{ fontSize: 10, color: "#6B7280", fontFamily: FONT }}>{label}</span>
      </div>
    ))}
  </div>
);

const CustomTooltip = ({ payload, labelFormatter }: any) => {
  if (!payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{ background: "#FFF", border: "1px solid #E5E7EB", borderRadius: 8, padding: "8px 12px", fontSize: 11, fontFamily: FONT, boxShadow: "0 4px 12px rgba(0,0,0,0.08)", maxWidth: 220 }}>
      {labelFormatter ? labelFormatter(d) : null}
    </div>
  );
};

// ══════════════════════════════════════
// 1. VOLCANO PLOT
// ══════════════════════════════════════
function VolcanoPlot() {
  const data = useMemo(genVolcanoData, []);
  return (
    <Card title="AMR Gene Differential Abundance" subtitle="Resistant vs. susceptible isolates · log₂FC ≥ 1, -log₁₀(p) ≥ 2 threshold">
      <ResponsiveContainer width="100%" height={380}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 40, left: 50 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
          <XAxis dataKey="lfc" type="number" name="log₂FC" domain={[-4, 4]} tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "log₂ Fold Change (Resistant / Susceptible)", position: "bottom", offset: 20, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <YAxis dataKey="negLogP" type="number" name="-log₁₀(p)" tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "-log₁₀(adjusted p-value)", angle: -90, position: "insideLeft", offset: -30, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <Tooltip content={<CustomTooltip labelFormatter={(d: any) => (
            <>
              <div style={{ fontWeight: 700, fontFamily: MONO }}>{d.gene}</div>
              <div style={{ color: "#6B7280" }}>log₂FC: {d.lfc} · p: {d.pval.toExponential(2)}</div>
              <div style={{ color: SIG_COLORS[d.sig], fontWeight: 600 }}>
                {d.sig === "up" ? "↑ Enriched in Resistant" : d.sig === "down" ? "↓ Enriched in Susceptible" : "Not significant"}
              </div>
            </>
          )} />} />
          {/* Threshold lines */}
          <Scatter data={data} shape="circle">
            {data.map((d, i) => <Cell key={i} fill={SIG_COLORS[d.sig]} fillOpacity={d.sig === "ns" ? 0.35 : 0.8} r={d.sig === "ns" ? 4 : 6} stroke={d.sig === "ns" ? "none" : SIG_COLORS[d.sig]} strokeWidth={1} />)}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      {/* Gene labels for significant hits */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
        {data.filter(d => d.sig !== "ns").map(d => (
          <span key={d.gene} style={{ fontSize: 9, fontFamily: MONO, padding: "2px 6px", borderRadius: 4, background: d.sig === "up" ? "#FEE2E2" : "#DBEAFE", color: d.sig === "up" ? "#991B1B" : "#1E40AF" }}>
            {d.sig === "up" ? "↑" : "↓"} {d.gene}
          </span>
        ))}
      </div>
      <ChipLegend items={[{ color: SIG_COLORS.up, label: "Upregulated in Resistant" }, { color: SIG_COLORS.down, label: "Upregulated in Susceptible" }, { color: SIG_COLORS.ns, label: "Not Significant" }]} />
    </Card>
  );
}

// ══════════════════════════════════════
// 2. PCA PLOT
// ══════════════════════════════════════
function PCAPlot() {
  const data = useMemo(genPCAData, []);
  const phenotypes = Object.keys(PHENO_COLORS);
  return (
    <Card title="Resistome PCA" subtitle="Principal component analysis on AMR gene presence/absence matrix · n=30 isolates">
      <ResponsiveContainer width="100%" height={380}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 40, left: 50 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
          <XAxis dataKey="pc1" type="number" domain={[-6, 7]} tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "PC1 (42.3% variance)", position: "bottom", offset: 20, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <YAxis dataKey="pc2" type="number" domain={[-4, 4]} tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "PC2 (18.7% variance)", angle: -90, position: "insideLeft", offset: -30, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <Tooltip content={<CustomTooltip labelFormatter={(d: any) => (
            <>
              <div style={{ fontWeight: 700 }}>{d.id}</div>
              <div style={{ color: PHENO_COLORS[d.phenotype], fontWeight: 600 }}>{d.phenotype}</div>
              <div style={{ color: "#6B7280" }}>PC1: {d.pc1} · PC2: {d.pc2}</div>
            </>
          )} />} />
          {phenotypes.map(p => (
            <Scatter key={p} name={p} data={data.filter(d => d.phenotype === p)} fill={PHENO_COLORS[p]}>
              {data.filter(d => d.phenotype === p).map((d, i) => (
                <Cell key={i} fill={PHENO_COLORS[p]} fillOpacity={0.7} stroke={PHENO_COLORS[p]} strokeWidth={1.5} r={6} />
              ))}
            </Scatter>
          ))}
          <Legend wrapperStyle={{ fontSize: 10, fontFamily: FONT }} />
        </ScatterChart>
      </ResponsiveContainer>
    </Card>
  );
}

// ══════════════════════════════════════
// 3. HEATMAP (Custom SVG)
// ══════════════════════════════════════
function Heatmap() {
  const { isolates, genes, matrix } = useMemo(genHeatmapData, []);
  const [hover, setHover] = useState<any>(null);
  const cellW = 38, cellH = 16, labelW = 56, topH = 80;
  const svgW = labelW + genes.length * cellW + 60;
  const svgH = topH + isolates.length * cellH + 20;

  const colorScale = (val: number) => {
    if (val === 0) return "#F9FAFB";
    const t = (val - 85) / 15;
    const r = Math.round(254 - t * 24), g = Math.round(226 - t * 186), b = Math.round(226 - t * 156);
    return `rgb(${r},${g},${b})`;
  };

  return (
    <Card title="AMR Gene Presence / Identity Heatmap" subtitle="Rows = isolates · Columns = AMR genes · Color intensity = % sequence identity · White = absent">
      <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: 600 }}>
        <svg viewBox={`0 0 ${svgW} ${svgH}`} style={{ width: svgW, height: svgH, display: "block" }}>
          {/* Column labels */}
          {genes.map((g, gi) => (
            <text key={g} x={labelW + gi * cellW + cellW / 2} y={topH - 6} fontSize={7} fill="#374151" fontFamily={MONO} fontWeight={600}
              textAnchor="end" transform={`rotate(-50, ${labelW + gi * cellW + cellW / 2}, ${topH - 6})`}>{g}</text>
          ))}
          {/* Row labels + cells */}
          {matrix.map((row, ri) => (
            <g key={row.isolate}>
              <text x={labelW - 4} y={topH + ri * cellH + cellH / 2 + 3} fontSize={7} fill="#6B7280" fontFamily={MONO} textAnchor="end">{row.isolate}</text>
              {genes.map((g, gi) => {
                const val = row[g];
                const isHov = hover && hover.r === ri && hover.c === gi;
                return (
                  <g key={g} onMouseEnter={() => setHover({ r: ri, c: gi, gene: g, iso: row.isolate, val })} onMouseLeave={() => setHover(null)}>
                    <rect x={labelW + gi * cellW} y={topH + ri * cellH} width={cellW - 1} height={cellH - 1}
                      fill={colorScale(val)} stroke={isHov ? "#111827" : "#F3F4F6"} strokeWidth={isHov ? 1.5 : 0.5} rx={1} />
                    {val > 0 && cellW > 30 && (
                      <text x={labelW + gi * cellW + cellW / 2 - 0.5} y={topH + ri * cellH + cellH / 2 + 3}
                        fontSize={6} fill={val > 95 ? "#FFF" : "#374151"} textAnchor="middle" fontFamily={MONO}>{val.toFixed(0)}</text>
                    )}
                  </g>
                );
              })}
            </g>
          ))}
          {/* Color scale legend */}
          <defs>
            <linearGradient id="heatGrad" x1="0" x2="1" y1="0" y2="0">
              <stop offset="0%" stopColor="#F9FAFB" /><stop offset="50%" stopColor="#FCA5A5" /><stop offset="100%" stopColor="#E63946" />
            </linearGradient>
          </defs>
          <rect x={labelW + genes.length * cellW + 10} y={topH} width={14} height={isolates.length * cellH} fill="url(#heatGrad)" rx={3} transform={`rotate(0)`} />
          <text x={labelW + genes.length * cellW + 32} y={topH + 8} fontSize={7} fill="#6B7280" fontFamily={FONT}>100%</text>
          <text x={labelW + genes.length * cellW + 32} y={topH + isolates.length * cellH / 2} fontSize={7} fill="#6B7280" fontFamily={FONT}>92%</text>
          <text x={labelW + genes.length * cellW + 32} y={topH + isolates.length * cellH - 2} fontSize={7} fill="#6B7280" fontFamily={FONT}>85%</text>
          {/* Tooltip */}
          {hover && (
            <g>
              <rect x={labelW + hover.c * cellW + cellW + 4} y={topH + hover.r * cellH - 10} width={120} height={36} rx={4} fill="#111827" opacity={0.92} />
              <text x={labelW + hover.c * cellW + cellW + 10} y={topH + hover.r * cellH + 4} fontSize={8} fill="#FFF" fontFamily={MONO} fontWeight={600}>{hover.gene}</text>
              <text x={labelW + hover.c * cellW + cellW + 10} y={topH + hover.r * cellH + 16} fontSize={7} fill="#9CA3AF" fontFamily={FONT}>
                {hover.iso} · {hover.val > 0 ? `${hover.val}% identity` : "Absent"}
              </text>
            </g>
          )}
        </svg>
      </div>
    </Card>
  );
}

// ══════════════════════════════════════
// 4. UMAP CLUSTERS
// ══════════════════════════════════════
function UMAPClusters() {
  const data = useMemo(genUMAPData, []);
  const sts = Object.keys(ST_COLORS);
  return (
    <Card title="Resistome UMAP — Sequence Type Clusters" subtitle={`UMAP on binary AMR gene matrix · Colored by MLST sequence type · n=${data.length} isolates`}>
      <ResponsiveContainer width="100%" height={380}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 40, left: 50 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
          <XAxis dataKey="u1" type="number" domain={[-6.5, 6.5]} tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "UMAP-1", position: "bottom", offset: 20, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <YAxis dataKey="u2" type="number" domain={[-6, 6]} tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "UMAP-2", angle: -90, position: "insideLeft", offset: -30, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <Tooltip content={<CustomTooltip labelFormatter={(d: any) => (
            <>
              <div style={{ fontWeight: 700 }}>{d.id}</div>
              <div style={{ color: ST_COLORS[d.st], fontWeight: 600 }}>{d.st}</div>
              <div style={{ color: "#6B7280" }}>blaNDM-1 identity: {d.ndm1}%</div>
            </>
          )} />} />
          {sts.map(st => (
            <Scatter key={st} name={st} data={data.filter(d => d.st === st)} fill={ST_COLORS[st]}>
              {data.filter(d => d.st === st).map((d, i) => (
                <Cell key={i} fill={ST_COLORS[st]} fillOpacity={0.75} stroke={ST_COLORS[st]} strokeWidth={1.5} r={6} />
              ))}
            </Scatter>
          ))}
          <Legend wrapperStyle={{ fontSize: 10, fontFamily: FONT }} />
        </ScatterChart>
      </ResponsiveContainer>
    </Card>
  );
}

// ══════════════════════════════════════
// 5. FEATURE PLOT (gene intensity on UMAP)
// ══════════════════════════════════════
function FeaturePlot() {
  const data = useMemo(genUMAPData, []);
  const [selGene, setSelGene] = useState("blaNDM-1");
  const genes = ["blaNDM-1", "mcr-1", "blaOXA-48"];

  const featureColor = (val: number) => {
    if (val < 20) return "#F3F4F6";
    const t = (val - 20) / 80;
    return d3.interpolateYlOrRd(t * 0.85 + 0.15);
  };

  return (
    <Card title="AMR Feature Plot" subtitle={`Expression intensity of ${selGene} projected onto UMAP coordinates`}>
      <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
        {genes.map(g => (
          <button key={g} onClick={() => setSelGene(g)} style={{
            padding: "4px 12px", borderRadius: 6, border: "1px solid #E5E7EB", fontSize: 11, fontFamily: MONO,
            cursor: "pointer", fontWeight: selGene === g ? 700 : 400,
            background: selGene === g ? "#111827" : "#FFF", color: selGene === g ? "#FFF" : "#374151",
          }}>{g}</button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={380}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 40, left: 50 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" />
          <XAxis dataKey="u1" type="number" domain={[-6.5, 6.5]} tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "UMAP-1", position: "bottom", offset: 20, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <YAxis dataKey="u2" type="number" domain={[-6, 6]} tick={{ fontSize: 10, fill: "#9CA3AF" }}
            label={{ value: "UMAP-2", angle: -90, position: "insideLeft", offset: -30, style: { fontSize: 11, fill: "#6B7280", fontFamily: FONT } }} />
          <Tooltip content={<CustomTooltip labelFormatter={(d: any) => (
            <>
              <div style={{ fontWeight: 700 }}>{d.id} ({d.st})</div>
              <div style={{ color: "#6B7280" }}>{selGene}: {d.ndm1}% identity</div>
            </>
          )} />} />
          <Scatter data={data}>
            {data.map((d, i) => (
              <Cell key={i} fill={featureColor(d.ndm1)} stroke="#D1D5DB" strokeWidth={0.5} r={6} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      {/* Gradient legend */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6 }}>
        <span style={{ fontSize: 9, color: "#9CA3AF" }}>0%</span>
        <div style={{ width: 180, height: 10, borderRadius: 5, background: "linear-gradient(90deg, #F3F4F6 0%, #FEF3C7 25%, #FDBA74 50%, #F87171 75%, #991B1B 100%)" }} />
        <span style={{ fontSize: 9, color: "#9CA3AF" }}>100% identity</span>
      </div>
    </Card>
  );
}

// ══════════════════════════════════════
// 6. VIOLIN / DOT PLOT (Custom SVG)
// ══════════════════════════════════════
function ViolinDotPlot() {
  const { genes, groups, data } = useMemo(genViolinData, []);
  const geneW = 120, groupW = 34, padL = 80, padT = 30, plotH = 200, padB = 40;
  const svgW = padL + genes.length * geneW + 20;
  const svgH = padT + plotH + padB;
  const yScale = (val: number) => padT + plotH - (val / 100) * plotH;

  const buildViolin = (points: any[], cx: number, halfW: number) => {
    if (points.length < 3) return "";
    const bins = d3.bin().domain([0, 100] as any).thresholds(15)(points.map(p => p.identity));
    const maxCount = d3.max(bins, b => b.length) || 1;
    const pts = bins.map(b => ({ y: yScale((b.x0! + b.x1!) / 2), w: (b.length / maxCount) * halfW }));
    const left = pts.map(p => `${cx - p.w},${p.y}`).join(" ");
    const right = [...pts].reverse().map(p => `${cx + p.w},${p.y}`).join(" ");
    return `${left} ${right}`;
  };

  return (
    <Card title="AMR Gene Identity Distribution" subtitle="% sequence identity per gene across resistance phenotype groups · Violin + strip plot">
      <div style={{ overflowX: "auto" }}>
        <svg viewBox={`0 0 ${svgW} ${svgH}`} style={{ width: "100%", minWidth: svgW, height: svgH }}>
          {/* Y axis */}
          {[0, 25, 50, 75, 100].map(v => (
            <g key={v}>
              <line x1={padL - 4} y1={yScale(v)} x2={svgW - 20} y2={yScale(v)} stroke="#F3F4F6" strokeWidth={0.5} />
              <text x={padL - 8} y={yScale(v) + 3} fontSize={8} fill="#9CA3AF" textAnchor="end" fontFamily={MONO}>{v}%</text>
            </g>
          ))}
          <text x={12} y={padT + plotH / 2} fontSize={9} fill="#6B7280" fontFamily={FONT} textAnchor="middle" transform={`rotate(-90, 12, ${padT + plotH / 2})`}>% Sequence Identity</text>

          {genes.map((gene, gi) => {
            const gx = padL + gi * geneW;
            return (
              <g key={gene}>
                {/* Gene label */}
                <text x={gx + geneW / 2} y={svgH - 8} fontSize={8} fill="#374151" fontFamily={MONO} fontWeight={600} textAnchor="middle">{gene}</text>
                {/* Separator */}
                {gi > 0 && <line x1={gx - 2} y1={padT} x2={gx - 2} y2={padT + plotH} stroke="#F3F4F6" strokeWidth={0.5} />}
                {/* Violins per group */}
                {groups.map((grp, gri) => {
                  const cx = gx + 20 + gri * groupW;
                  const pts = data.filter(d => d.gene === gene && d.group === grp);
                  const polyPts = buildViolin(pts, cx, 12);
                  const color = PHENO_COLORS[grp];
                  const median = d3.median(pts, d => d.identity) || 0;
                  return (
                    <g key={grp}>
                      {polyPts && <polygon points={polyPts} fill={color} fillOpacity={0.15} stroke={color} strokeWidth={1} strokeOpacity={0.4} />}
                      {pts.map((p, pi) => (
                        <circle key={pi} cx={cx + (rng() - 0.5) * 8} cy={yScale(p.identity)} r={1.8} fill={color} fillOpacity={0.5} />
                      ))}
                      <line x1={cx - 6} y1={yScale(median)} x2={cx + 6} y2={yScale(median)} stroke={color} strokeWidth={2} />
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>
      <ChipLegend items={groups.map(g => ({ color: PHENO_COLORS[g], label: g }))} />
    </Card>
  );
}

// ══════════════════════════════════════
// 7. RESISTANCE MECHANISM COMPOSITION
// ══════════════════════════════════════
function MechComposition() {
  const data = useMemo(genMechCompData, []);
  const mechs = Object.keys(MECH_COLORS);

  return (
    <Card title="Resistance Mechanism Composition" subtitle="Proportional breakdown of resistance mechanisms per isolate · Stacked 100% bar chart">
      <ResponsiveContainer width="100%" height={420}>
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, bottom: 20, left: 50 }} barCategoryGap={2}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 9, fill: "#9CA3AF" }}
            label={{ value: "% of Resistance Determinants", position: "bottom", offset: 5, style: { fontSize: 10, fill: "#6B7280", fontFamily: FONT } }} />
          <YAxis dataKey="isolate" type="category" tick={{ fontSize: 8, fill: "#6B7280", fontFamily: MONO }} width={46} />
          <Tooltip contentStyle={{ fontSize: 11, fontFamily: FONT, borderRadius: 8 }} />
          {mechs.map(m => (
            <Bar key={m} dataKey={m} stackId="a" fill={MECH_COLORS[m]} fillOpacity={0.85} />
          ))}
          <Legend wrapperStyle={{ fontSize: 9, fontFamily: FONT }} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

// ══════════════════════════════════════
// MAIN DASHBOARD
// ══════════════════════════════════════
const TABS = [
  { id: "volcano", label: "Volcano", icon: "◆" },
  { id: "pca", label: "PCA", icon: "◎" },
  { id: "heatmap", label: "Heatmap", icon: "▦" },
  { id: "umap", label: "UMAP", icon: "◉" },
  { id: "feature", label: "Feature", icon: "◐" },
  { id: "violin", label: "Violin", icon: "♪" },
  { id: "mechanism", label: "Mechanism", icon: "▤" },
  { id: "3d-umap", label: "3D UMAP", icon: "⚗" },
  { id: "3d-network", label: "3D Network", icon: "✇" },
  { id: "3d-mst", label: "3D MST", icon: "⎈" },
];

export default function TBioDashboard() {
  const [tab, setTab] = useState("volcano");

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: FONT, background: "#F9FAFB" }}>
      {/* Sidebar */}
      <div style={{ width: 200, background: "#111827", padding: "20px 0", flexShrink: 0, display: "flex", flexDirection: "column", height: "100vh", position: "sticky", top: 0 }}>
        <div style={{ padding: "0 16px 20px", borderBottom: "1px solid #1F2937" }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: "#FFF", letterSpacing: "-0.02em" }}>AMR Analytics</div>
          <div style={{ fontSize: 9, color: "#6B7280", marginTop: 2, textTransform: "uppercase", letterSpacing: "0.08em" }}>T-BioInfo Style</div>
        </div>
        <div style={{ padding: "12px 8px", flex: 1 }}>
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              width: "100%", padding: "10px 12px", border: "none", borderRadius: 6, fontSize: 12,
              cursor: "pointer", display: "flex", alignItems: "center", gap: 8, marginBottom: 2,
              background: tab === t.id ? "#1F2937" : "transparent",
              color: tab === t.id ? "#FFF" : "#9CA3AF", fontWeight: tab === t.id ? 600 : 400,
              fontFamily: FONT, transition: "all 0.15s",
            }}>
              <span style={{ fontSize: 14, width: 20, textAlign: "center" }}>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>
        <div style={{ padding: "12px 16px", borderTop: "1px solid #1F2937" }}>
          <div style={{ fontSize: 8, color: "#4B5563", textTransform: "uppercase", letterSpacing: "0.1em" }}>Pipeline v2.1</div>
          <div style={{ fontSize: 8, color: "#4B5563" }}>CARD · ResFinder · AMRFinder+</div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: 24, overflowY: "auto" }}>
        <div style={{ marginBottom: 16 }}>
          <h1 style={{ fontSize: 20, fontWeight: 800, color: "#111827", margin: 0 }}>
            {TABS.find(t => t.id === tab)?.label} Plot
          </h1>
          <p style={{ fontSize: 11, color: "#9CA3AF", margin: "4px 0 0" }}>
            Klebsiella pneumoniae cohort · {tab === "volcano" || tab === "pca" || tab === "violin" ? "30" : tab === "heatmap" ? "30 × 15" : tab === "mechanism" ? "25" : "~50"} isolates
          </p>
        </div>

        {tab === "volcano" && <VolcanoPlot />}
        {tab === "pca" && <PCAPlot />}
        {tab === "heatmap" && <Heatmap />}
        {tab === "umap" && <UMAPClusters />}
        {tab === "feature" && <FeaturePlot />}
        {tab === "violin" && <ViolinDotPlot />}
        {tab === "mechanism" && <MechComposition />}
        
        {/* Our custom 3D integrations */}
        {tab === "3d-umap" && (
          <Card title="Live 3D UMAP" subtitle="Plotly interactive 3D Scatter">
             <DimReductionPlot />
          </Card>
        )}
        {tab === "3d-network" && (
          <Card title="Live 3D Co-occurrence Network" subtitle="ForceGraph3D Interactive Graph">
             <CoOccurrenceNetwork />
          </Card>
        )}
        {tab === "3d-mst" && (
          <Card title="Live 3D Minimum Spanning Tree" subtitle="ForceGraph3D Interactive Graph">
             <MinimumSpanningTree />
          </Card>
        )}
      </div>
    </div>
  );
}
