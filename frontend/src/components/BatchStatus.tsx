import React, { useEffect, useState } from 'react';

export default function BatchStatus({ batchId, onComplete }: { batchId: string, onComplete: () => void }) {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    // Poll the status every 2 seconds
    const interval = setInterval(() => {
      fetch(`http://127.0.0.1:8000/api/v1/batches/${batchId}`)
        .then(res => res.json())
        .then(data => {
          setStatus(data);
          if (data.status === 'COMPLETED' || data.status === 'PARTIAL_FAILED' || data.status === 'COHORT_FAILED') {
            clearInterval(interval);
            setTimeout(onComplete, 2000); // Give user a moment to see 100% completion
          }
        })
        .catch(err => console.error(err));
    }, 2000);
    return () => clearInterval(interval);
  }, [batchId, onComplete]);

  if (!status) {
    return (
      <div className="flex flex-col items-center py-10">
        <div className="w-16 h-16 border-4 border-surface-card border-t-accent-teal rounded-full animate-spin mb-6"></div>
        <h3 className="text-xl font-bold text-text-primary mb-2">Initializing Batch...</h3>
      </div>
    );
  }

  const percent = status.total_isolates > 0 
    ? Math.round(((status.completed + status.failed) / status.total_isolates) * 100) 
    : 0;

  return (
    <div className="bg-surface-card/50 backdrop-blur-md rounded-2xl p-8 border border-surface-dark shadow-2xl w-full max-w-3xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-text-primary">{status.batch_name || 'Batch Processing'}</h2>
          <p className="text-text-muted text-sm font-mono mt-1">ID: {batchId}</p>
        </div>
        <div className="px-4 py-2 rounded-lg font-bold text-sm bg-accent-teal/20 text-accent-teal border border-accent-teal/30">
          {status.status}
        </div>
      </div>

      <div className="mb-8">
        <div className="flex justify-between text-sm font-bold text-text-primary mb-2">
          <span>Overall Progress</span>
          <span>{percent}%</span>
        </div>
        <div className="w-full h-4 bg-surface-dark rounded-full overflow-hidden flex">
          <div className="h-full bg-accent-teal transition-all duration-500" style={{ width: `${(status.completed / status.total_isolates) * 100}%` }}></div>
          <div className="h-full bg-red-500 transition-all duration-500" style={{ width: `${(status.failed / status.total_isolates) * 100}%` }}></div>
        </div>
        <div className="flex gap-6 mt-3 text-sm text-text-muted">
          <div><span className="font-bold text-accent-teal">{status.completed}</span> Completed</div>
          <div><span className="font-bold text-blue-500">{status.running}</span> Running</div>
          <div><span className="font-bold text-red-500">{status.failed}</span> Failed</div>
          <div><span className="font-bold">{status.total_isolates}</span> Total</div>
        </div>
      </div>

      <div className="border border-surface-dark rounded-xl overflow-hidden">
        <div className="bg-surface-dark px-4 py-3 border-b border-surface-dark/50 text-xs font-bold text-text-muted uppercase tracking-wider grid grid-cols-12 gap-4">
          <div className="col-span-6">Isolate Name</div>
          <div className="col-span-3">Status</div>
          <div className="col-span-3">Stage</div>
        </div>
        <div className="max-h-[400px] overflow-y-auto">
          {(status?.isolates || []).map((iso: any) => (
            <div key={iso.sample_id} className="px-4 py-3 border-b border-surface-dark/20 text-sm grid grid-cols-12 gap-4 items-center hover:bg-surface-dark/10">
              <div className="col-span-6 font-mono text-text-primary truncate" title={iso.filename}>{iso.filename}</div>
              <div className="col-span-3">
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  iso.status === 'COMPLETED' ? 'bg-[#198038]/20 text-[#198038]' :
                  iso.status === 'FAILED' ? 'bg-[#da1e28]/20 text-[#da1e28]' :
                  iso.status === 'RUNNING' ? 'bg-[#0f62fe]/20 text-[#0f62fe]' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {iso.status}
                </span>
              </div>
              <div className="col-span-3 text-text-muted text-xs truncate">
                {iso.current_stage || '-'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {status.cohort_analysis_status === 'RUNNING' && (
        <div className="mt-6 p-4 rounded-xl border border-[#0f62fe]/30 bg-[#0f62fe]/10 flex items-center gap-4">
          <div className="w-6 h-6 border-2 border-[#0f62fe]/30 border-t-[#0f62fe] rounded-full animate-spin"></div>
          <div>
            <div className="font-bold text-[#0f62fe] text-sm">Service 10 Running</div>
            <div className="text-xs text-[#0f62fe]/80">Computing Cohort Network, UMAP, and PCA aggregations...</div>
          </div>
        </div>
      )}
    </div>
  );
}
