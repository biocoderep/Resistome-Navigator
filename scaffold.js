const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, 'frontend', 'src', 'components', 'dashboard');

const components = [
  'PipelineTracker',
  'Service1Validation',
  'Service3Detection',
  'Service4Mutation',
  'Service5Mechanism',
  'Service6Phenotype',
  'Service7Virulence',
  'Service8Confidence',
  'GenomicSummary',
  'CohortViews'
];

components.forEach(name => {
  const code = `import React from 'react';

export default function ${name}() {
  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">${name}</h2>
      <div className="p-10 border border-dashed border-surface-dark rounded-xl text-center text-text-muted">
        Component scaffolding for ${name}
      </div>
    </div>
  );
}
`;
  fs.writeFileSync(path.join(dir, `${name}.tsx`), code);
});

console.log('Successfully scaffolded 10 dashboard components.');
