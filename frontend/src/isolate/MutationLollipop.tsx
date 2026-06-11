import React, { useMemo } from 'react';
import { scaleLinear, scaleBand } from '@visx/scale';
import { Group } from '@visx/group';
import { Line, Circle } from '@visx/shape';
import { AxisBottom } from '@visx/axis';
import { useResistanceMutations } from '../../hooks/useAmrData';
import { theme } from '../../theme/tokens';

export default function MutationLollipop({ sampleId, width = 600, height = 300 }: { sampleId: string, width?: number, height?: number }) {
  const { data: mutations, loading } = useResistanceMutations(sampleId);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!mutations || mutations.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No resistance mutations.</div>;

  const margin = { top: 40, right: 20, bottom: 40, left: 80 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // Group by gene
  const genes = Array.from(new Set(mutations.map(m => m.gene)));
  
  // Scales
  const yScale = scaleBand<string>({
    range: [0, innerHeight],
    domain: genes,
    padding: 0.5,
  });

  // For x-axis, we need max position across all genes
  const maxPos = Math.max(...mutations.map(m => m.position), 1000); // fallback 1000 aa
  const xScale = scaleLinear<number>({
    range: [0, innerWidth],
    domain: [0, maxPos + 50],
  });

  const getSigColor = (sig: string) => {
    if (sig === 'HIGH') return theme.colors.confidence.HIGH;
    if (sig === 'MEDIUM') return theme.colors.confidence.MEDIUM;
    return theme.colors.confidence.LOW;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 overflow-x-auto">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Point Mutations</h3>
        <p className="text-xs text-gray-500">Amino acid substitutions on reference gene bodies.</p>
      </div>

      <div style={{ position: 'relative', width, height }}>
        <svg width={width} height={height}>
          <Group top={margin.top} left={margin.left}>
            {/* Draw gene bodies (horizontal lines) */}
            {genes.map(gene => {
              const y = (yScale(gene) || 0) + yScale.bandwidth() / 2;
              return (
                <g key={gene}>
                  <text 
                    x={-10} y={y} dy=".32em" textAnchor="end" 
                    className="text-xs font-mono font-bold fill-gray-700"
                  >
                    {gene}
                  </text>
                  <Line
                    from={{ x: 0, y }}
                    to={{ x: innerWidth, y }}
                    stroke={theme.colors.surface.border}
                    strokeWidth={4}
                    strokeLinecap="round"
                  />
                </g>
              );
            })}

            {/* Draw lollipops */}
            {mutations.map((m, i) => {
              const x = xScale(m.position);
              const yBase = (yScale(m.gene) || 0) + yScale.bandwidth() / 2;
              // Alternate direction to avoid overlaps if needed, here we just go up
              const yHead = yBase - 25; 
              
              return (
                <g key={i} className="group cursor-default">
                  {/* Stick */}
                  <Line
                    from={{ x, y: yBase }}
                    to={{ x, y: yHead }}
                    stroke="#9CA3AF"
                    strokeWidth={1.5}
                  />
                  {/* Head */}
                  <Circle
                    cx={x}
                    cy={yHead}
                    r={6}
                    fill={getSigColor(m.clinical_significance)}
                    stroke="white"
                    strokeWidth={2}
                  />
                  {/* Label */}
                  <text
                    x={x}
                    y={yHead - 10}
                    textAnchor="middle"
                    className="text-[9px] font-mono fill-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    {m.ref_aa}{m.position}{m.alt_aa}
                  </text>
                </g>
              );
            })}

            <AxisBottom
              top={innerHeight}
              scale={xScale}
              numTicks={10}
              stroke={theme.colors.surface.border}
              tickStroke={theme.colors.surface.border}
              tickLabelProps={() => ({
                fill: theme.colors.text.secondary,
                fontSize: 10,
                textAnchor: 'middle',
              })}
              label="Amino Acid Position"
              labelProps={{
                fill: theme.colors.text.secondary,
                fontSize: 12,
                textAnchor: 'middle',
                dy: 20
              }}
            />
          </Group>
        </svg>
      </div>
    </div>
  );
}
