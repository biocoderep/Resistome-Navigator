import React from 'react';

export default function CohortViews({ batchId }: { batchId?: string }) {

  if (!batchId) {
    return <div className="p-6 text-center text-gray-500">Cohort analytics require a valid Batch ID.</div>;
  }

  // The Shiny Server must be running on port 8080.
  // We pass embed=true to hide the dashboard's Chrome (sidebar, header).
  const shinyUrl = `http://127.0.0.1:8080/?batch_id=${batchId}&embed=true`;

  return (
    <div className="w-full h-[850px] bg-white rounded-xl overflow-hidden border border-gray-200">
      <iframe 
        src={shinyUrl} 
        className="w-full h-full border-none"
        title="Interactive Shiny Analytics"
      />
    </div>
  );
}
