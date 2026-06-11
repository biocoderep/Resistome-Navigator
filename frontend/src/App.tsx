import React, { useState } from 'react';
import TBioDashboard from './TBioDashboard';
import BatchStatus from './components/BatchStatus';
import { useNavigate } from 'react-router-dom';

function App() {
  const navigate = useNavigate();
  // New States for Automation Flow
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isBatch, setIsBatch] = useState(false);
  const [batchComplete, setBatchComplete] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);

    try {
      if (files.length === 1) {
        // Single File Upload Flow
        const formData = new FormData();
        formData.append('file', files[0]);
        formData.append('isolate_name', files[0].name);

        const upRes = await fetch('http://127.0.0.1:8000/api/v1/samples/upload', {
          method: 'POST',
          body: formData
        });
        const upData = await upRes.json();
        
        setUploading(false);
        setAnalyzing(true);
        
        await fetch('http://127.0.0.1:8000/api/v1/analysis/run-full', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sample_id: upData.id })
        });
        
        setTimeout(() => {
          setAnalyzing(false);
          // Redirect to the new admin dashboard layout
          navigate(`/admin/dashboard?batchId=${upData.batch_id || upData.id}`);
        }, 3000);
      } else {
        // Batch Upload Flow
        const formData = new FormData();
        files.forEach(f => formData.append('files', f));
        formData.append('project_id', '00000000-0000-0000-0000-000000000000');
        formData.append('batch_name', 'Batch Run ' + new Date().toLocaleTimeString());
        
        const upRes = await fetch('http://127.0.0.1:8000/api/v1/batches', {
          method: 'POST',
          body: formData
        });
        const upData = await upRes.json();
        
        setUploading(false);
        setIsBatch(true);
        setJobId(upData.batch_id);
      }
    } catch (err) {
      console.error(err);
      setUploading(false);
      setAnalyzing(false);
    }
  };

  // If batch is polling, show status (You can optionally redirect to a loading page here)
  if (jobId && isBatch && !batchComplete) {
    return (
      <div className="min-h-screen bg-surface flex flex-col p-8 items-center pt-20">
        <BatchStatus batchId={jobId} onComplete={() => {
          setBatchComplete(true);
          navigate(`/admin/dashboard?batchId=${jobId}`);
        }} />
      </div>
    );
  }

  // Upload / Loading Screen
  return (
    <div className="min-h-screen bg-surface flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-lg text-center mb-8">
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent-teal to-blue-400 mb-2">
          AMR Platform
        </h1>
      </div>
        
        {!uploading && !analyzing ? (
        <div className="bg-surface-card/50 backdrop-blur-md rounded-2xl p-8 border border-surface-dark shadow-2xl w-full max-w-lg">
          <div className="flex items-center justify-center w-full mb-6">
            <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-surface-dark border-dashed rounded-lg cursor-pointer bg-surface-card hover:bg-surface-dark/50 transition-colors group">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <svg className="w-10 h-10 mb-4 text-accent-teal group-hover:scale-110 transition-transform" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                  <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                </svg>
                <p className="text-sm text-text-muted mb-1"><span className="font-semibold text-text-primary">Click to upload</span> or drag and drop</p>
                <p className="text-xs text-text-muted">Upload a single .fasta or select multiple files for a Batch Cohort</p>
              </div>
              <input type="file" className="hidden" accept=".fasta,.fa,.fna" multiple onChange={handleFileChange} />
            </label>
          </div>

          {files.length > 0 && (
            <div className="mb-6 space-y-2">
              <div className="text-sm text-text-primary font-semibold border-b border-surface-dark pb-2 text-left">
                Selected {files.length} file{files.length > 1 ? 's' : ''}:
              </div>
              <div className="max-h-32 overflow-y-auto space-y-2">
                {files.map((file, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 bg-surface-dark rounded-lg">
                    <div className="w-8 h-8 rounded bg-surface-card flex items-center justify-center">
                      <svg className="w-4 h-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <p className="text-sm font-medium text-text-primary truncate">{file.name}</p>
                      <p className="text-xs text-text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={files.length === 0}
            className={`w-full py-3 rounded-lg font-bold text-white transition-all ${files.length > 0 ? 'bg-accent-teal hover:bg-accent-cyan shadow-lg shadow-accent-teal/20' : 'bg-surface-dark text-text-muted cursor-not-allowed'}`}
          >
            Start Analysis
          </button>
        </div>
        ) : (
          <div className="flex flex-col items-center py-10">
            <div className="w-16 h-16 border-4 border-surface-card border-t-accent-teal rounded-full animate-spin mb-6"></div>
            <h3 className="text-xl font-bold text-text-primary mb-2">
              {uploading ? "Uploading Sequence..." : "Running Pipeline..."}
            </h3>
            <p className="text-text-muted text-sm max-w-xs">
              {uploading ? "Transferring file to secure storage." : "Executing Genome Validation, Alignment, AMR Detection, and Phenotype Prediction."}
            </p>
          </div>
        )}
    </div>
  );
}

export default App;

