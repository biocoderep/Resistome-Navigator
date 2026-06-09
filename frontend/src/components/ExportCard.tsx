import React, { useRef } from 'react';
import { toPng } from 'html-to-image';
import { Download } from 'lucide-react';

export const ExportCard = ({ title, filename, children }: { title: string, filename: string, children: React.ReactNode }) => {
  const ref = useRef<HTMLDivElement>(null);

  const handleDownload = async () => {
    if (!ref.current) return;
    try {
      const dataUrl = await toPng(ref.current, { backgroundColor: '#0E1E25', pixelRatio: 2 });
      const a = document.createElement('a');
      a.href = dataUrl;
      a.download = filename;
      a.click();
    } catch (err) {
      console.error('Failed to export image', err);
    }
  };

  return (
    <div className="bg-surface-card rounded-2xl p-6 shadow-lg border border-surface-dark transition-all hover:-translate-y-1 relative mb-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-text-primary tracking-tight">{title}</h3>
        <button 
          onClick={handleDownload}
          className="text-text-muted hover:text-accent-teal transition-colors p-2 rounded-full hover:bg-surface-dark"
          title="Download as PNG"
        >
          <Download size={20} />
        </button>
      </div>
      <div ref={ref} className="bg-surface-card rounded-xl">
        {children}
      </div>
    </div>
  );
};
