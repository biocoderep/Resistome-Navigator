/**
 * Publication-quality chart export utilities.
 *
 * Every chart in the platform renders as an SVG; these helpers let researchers
 * download any chart as:
 *   - SVG  (vector, native — best for figure editors)
 *   - PNG  (rasterised at 300 dpi for direct manuscript embedding)
 *   - PDF  (300 dpi PNG embedded in a page sized to the chart)
 *
 * For canvas-based charts (Plotly / force-graph) that have no <svg>, callers
 * fall back to html-to-image (see ExportCard).
 */

import { jsPDF } from 'jspdf';

const CSS_DPI = 96; // 1 CSS px === 1/96 inch
const EXPORT_BG = '#FFFFFF';

export type ExportFormat = 'svg' | 'png' | 'pdf';

function triggerDownload(url: string, filename: string): void {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function getSvgSize(svg: SVGSVGElement): { width: number; height: number } {
  // Prefer the viewBox, then explicit attrs, then layout box.
  const vb = svg.viewBox?.baseVal;
  if (vb && vb.width && vb.height) {
    return { width: vb.width, height: vb.height };
  }
  const rect = svg.getBoundingClientRect();
  const w = parseFloat(svg.getAttribute('width') || '') || rect.width || 800;
  const h = parseFloat(svg.getAttribute('height') || '') || rect.height || 600;
  return { width: w, height: h };
}

function serializeSvg(svg: SVGSVGElement): string {
  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');

  const { width, height } = getSvgSize(svg);
  if (!clone.getAttribute('width')) clone.setAttribute('width', String(width));
  if (!clone.getAttribute('height')) clone.setAttribute('height', String(height));

  // Opaque white background so exported figures are not transparent.
  const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  bg.setAttribute('x', '0');
  bg.setAttribute('y', '0');
  bg.setAttribute('width', '100%');
  bg.setAttribute('height', '100%');
  bg.setAttribute('fill', EXPORT_BG);
  clone.insertBefore(bg, clone.firstChild);

  return new XMLSerializer().serializeToString(clone);
}

export function exportSvg(svg: SVGSVGElement, filename: string): void {
  const blob = new Blob([serializeSvg(svg)], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  triggerDownload(url, ensureExt(filename, 'svg'));
  URL.revokeObjectURL(url);
}

async function svgToCanvas(svg: SVGSVGElement, scale: number): Promise<HTMLCanvasElement> {
  const data = serializeSvg(svg);
  const { width, height } = getSvgSize(svg);
  const blob = new Blob([data], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  try {
    const img = new Image();
    img.width = width;
    img.height = height;
    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve();
      img.onerror = () => reject(new Error('Failed to load SVG for rasterisation'));
      img.src = url;
    });

    const canvas = document.createElement('canvas');
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas 2D context unavailable');
    ctx.fillStyle = EXPORT_BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas;
  } finally {
    URL.revokeObjectURL(url);
  }
}

export async function exportPng(svg: SVGSVGElement, filename: string, dpi = 300): Promise<void> {
  const canvas = await svgToCanvas(svg, dpi / CSS_DPI);
  await new Promise<void>((resolve) => {
    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob);
        triggerDownload(url, ensureExt(filename, 'png'));
        URL.revokeObjectURL(url);
      }
      resolve();
    }, 'image/png');
  });
}

export async function exportPdf(svg: SVGSVGElement, filename: string, dpi = 300): Promise<void> {
  const { width, height } = getSvgSize(svg);
  const canvas = await svgToCanvas(svg, dpi / CSS_DPI);
  const imgData = canvas.toDataURL('image/png');
  const pdf = new jsPDF({
    orientation: width >= height ? 'landscape' : 'portrait',
    unit: 'pt',
    format: [width, height],
  });
  pdf.addImage(imgData, 'PNG', 0, 0, width, height);
  pdf.save(ensureExt(filename, 'pdf'));
}

/** Export a chart's <svg> in the requested format. */
export async function exportChart(
  svg: SVGSVGElement,
  format: ExportFormat,
  filename: string,
  dpi = 300,
): Promise<void> {
  if (format === 'svg') return exportSvg(svg, filename);
  if (format === 'png') return exportPng(svg, filename, dpi);
  return exportPdf(svg, filename, dpi);
}

/**
 * Fallback for non-SVG (canvas/WebGL) charts: rasterise a DOM node.
 * Uses html-to-image lazily so it is only loaded when needed.
 */
export async function exportNodeRaster(
  node: HTMLElement,
  format: Exclude<ExportFormat, 'svg'>,
  filename: string,
  dpi = 300,
): Promise<void> {
  const { toPng } = await import('html-to-image');
  const pixelRatio = dpi / CSS_DPI;
  const dataUrl = await toPng(node, { backgroundColor: EXPORT_BG, pixelRatio });

  if (format === 'png') {
    triggerDownload(dataUrl, ensureExt(filename, 'png'));
    return;
  }
  const rect = node.getBoundingClientRect();
  const pdf = new jsPDF({
    orientation: rect.width >= rect.height ? 'landscape' : 'portrait',
    unit: 'pt',
    format: [rect.width, rect.height],
  });
  pdf.addImage(dataUrl, 'PNG', 0, 0, rect.width, rect.height);
  pdf.save(ensureExt(filename, 'pdf'));
}

function ensureExt(filename: string, ext: string): string {
  const base = filename.replace(/\.(svg|png|pdf)$/i, '');
  return `${base}.${ext}`;
}
