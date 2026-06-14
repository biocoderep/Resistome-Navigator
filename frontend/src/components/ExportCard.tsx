import React, { useRef, useState, useEffect } from 'react';
import { Download, ChevronDown } from 'lucide-react';
import { exportChart, exportNodeRaster, type ExportFormat } from '../utils/exportChart';

interface ExportCardProps {
  title: string;
  filename: string;
  children: React.ReactNode;
  subtitle?: string;
  /**
   * 'card'    — full white card with title + export menu (default).
   * 'overlay' — transparent wrapper with a floating export menu in the
   *             top-right; use to add export to components that already
   *             render their own card chrome.
   */
  variant?: 'card' | 'overlay';
}

/**
 * Wraps a chart/table in a clean white card with a publication export menu.
 * Charts that render an <svg> get vector SVG + 300 dpi PNG + PDF export; canvas
 * based charts fall back to rasterised PNG/PDF.
 */
export const ExportCard: React.FC<ExportCardProps> = ({ title, filename, children, subtitle, variant = 'card' }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const findSvg = (): SVGSVGElement | null =>
    (ref.current?.querySelector('svg') as SVGSVGElement | null) ?? null;

  const handleExport = async (format: ExportFormat) => {
    setOpen(false);
    if (!ref.current) return;
    setBusy(true);
    try {
      const svg = findSvg();
      if (svg) {
        await exportChart(svg, format, filename);
      } else if (format !== 'svg') {
        await exportNodeRaster(ref.current, format, filename);
      } else {
        // No SVG present and SVG requested — raster PNG as the best available.
        await exportNodeRaster(ref.current, 'png', filename);
      }
    } catch (err) {
      console.error('Chart export failed', err);
    } finally {
      setBusy(false);
    }
  };

  const FORMATS: { key: ExportFormat; label: string; hint: string }[] = [
    { key: 'svg', label: 'SVG', hint: 'Vector' },
    { key: 'png', label: 'PNG', hint: '300 dpi' },
    { key: 'pdf', label: 'PDF', hint: 'Print' },
  ];

  const exportMenu = (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={busy}
        className="flex items-center gap-1 text-text-muted hover:text-accent-teal transition-colors px-2.5 py-1.5 rounded-lg hover:bg-surface border border-surface-dark text-sm disabled:opacity-50 bg-surface-card"
        title="Export figure"
      >
        <Download size={16} />
        <span className="font-medium">{busy ? 'Exporting…' : 'Export'}</span>
        <ChevronDown size={14} />
      </button>
      {open && (
        <div className="absolute right-0 mt-1 w-36 bg-surface-card border border-surface-dark rounded-lg shadow-lg z-20 overflow-hidden">
          {FORMATS.map((f) => (
            <button
              key={f.key}
              onClick={() => handleExport(f.key)}
              className="w-full flex items-center justify-between px-3 py-2 text-sm text-text-primary hover:bg-surface transition-colors"
            >
              <span className="font-medium">{f.label}</span>
              <span className="text-[10px] text-text-muted uppercase tracking-wide">{f.hint}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );

  if (variant === 'overlay') {
    return (
      <div className="relative">
        <div className="absolute right-3 top-3 z-10">{exportMenu}</div>
        <div ref={ref}>{children}</div>
      </div>
    );
  }

  return (
    <div className="relative bg-surface-card rounded-2xl p-6 shadow-sm border border-surface-dark mb-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold text-text-primary tracking-tight">{title}</h3>
          {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
        </div>
        {exportMenu}
      </div>
      <div ref={ref} className="bg-surface-card rounded-xl">
        {children}
      </div>
    </div>
  );
};

export default ExportCard;
