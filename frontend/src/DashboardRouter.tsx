import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import TBioDashboard from './TBioDashboard';
import { CohortDashboard } from './CohortDashboard';

const API = 'http://127.0.0.1:8000/api/v1';

type Mode = 'loading' | 'single' | 'cohort';

/**
 * Decides which dashboard to render for a given ``?batchId=`` query param:
 *   - a batch with >1 isolate  -> CohortDashboard (population view)
 *   - a single isolate         -> TBioDashboard (deep-dive)
 * The param is overloaded by the upload flow (it can be a batch id or, for
 * single uploads, a sample id), so we resolve it against the cohort metadata.
 */
export default function DashboardRouter() {
  const [params] = useSearchParams();
  const batchId = params.get('batchId');
  const [mode, setMode] = useState<Mode>('loading');
  const [sampleId, setSampleId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!batchId) {
      setMode('single');
      return;
    }
    fetch(`${API}/isolates/cohort-metadata?batch_id=${batchId}`)
      .then((r) => (r.ok ? r.json() : []))
      .then((samples: any[]) => {
        if (cancelled) return;
        if (Array.isArray(samples) && samples.length > 1) {
          setMode('cohort');
        } else if (Array.isArray(samples) && samples.length === 1) {
          setSampleId(samples[0].sample_id);
          setMode('single');
        } else {
          // No batch matched — treat the param itself as a sample id.
          setSampleId(batchId);
          setMode('single');
        }
      })
      .catch(() => {
        if (cancelled) return;
        setSampleId(batchId);
        setMode('single');
      });
    return () => {
      cancelled = true;
    };
  }, [batchId]);

  if (mode === 'loading') {
    return <div className="p-10 text-center text-text-muted animate-pulse">Resolving dashboard…</div>;
  }
  if (mode === 'cohort') {
    return <CohortDashboard />;
  }
  return <TBioDashboard sampleId={sampleId || batchId || ''} />;
}
