import React, { useMemo } from 'react';
import { useAmrGenes, useMechanismClassifications } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function DrugClassCoverageMatrix({ sampleId }: { sampleId: string }) {
  const { data: genes, loading: genesLoading } = useAmrGenes(sampleId);
  const { data: mechanisms, loading: mechLoading } = useMechanismClassifications();

  const { matrix, drugClasses, geneNames } = useMemo(() => {
    if (!genes || !mechanisms) return { matrix: [], drugClasses: [], geneNames: [] };

    // Get unique genes
    const uniqueGenes = Array.from(new Set(genes.map(g => g.gene_name))).sort();
    
    // Map genes to their affected drug classes from the mechanism table
    const geneToClasses: Record<string, Set<string>> = {};
    
    genes.forEach(g => {
      if (!geneToClasses[g.gene_name]) geneToClasses[g.gene_name] = new Set();
      // fallback to the base drug_class if mechanism classification isn't detailed
      geneToClasses[g.gene_name].add(g.drug_class);
      
      const mech = mechanisms.find(m => m.gene_or_mutation_id === g.gene_name);
      if (mech && mech.drug_classes_affected) {
        mech.drug_classes_affected.forEach(c => geneToClasses[g.gene_name].add(c));
      }
    });

    // Get all unique drug classes across these genes
    const allClasses = new Set<string>();
    Object.values(geneToClasses).forEach(set => set.forEach(c => allClasses.add(c)));
    const uniqueClasses = Array.from(allClasses).sort();

    // Build the boolean matrix
    const grid = uniqueGenes.map(gene => {
      return uniqueClasses.map(cls => geneToClasses[gene].has(cls));
    });

    return { matrix: grid, drugClasses: uniqueClasses, geneNames: uniqueGenes };
  }, [genes, mechanisms]);

  if (genesLoading || mechLoading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!genes || genes.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No coverage matrix available.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 overflow-x-auto h-full flex flex-col">
      <div className="mb-4 shrink-0">
        <h3 className="font-bold text-gray-900 text-sm">Class Coverage Matrix</h3>
        <p className="text-xs text-gray-500">Antibiotic classes compromised by detected determinants.</p>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full text-xs text-left border-collapse">
          <thead className="sticky top-0 bg-white z-10">
            <tr>
              <th className="pb-2 font-bold text-gray-500 border-b border-gray-200">Determinant</th>
              {drugClasses.map(cls => (
                <th key={cls} className="pb-2 px-1 text-center font-bold text-gray-700 border-b border-gray-200">
                  <div className="writing-vertical-rl transform rotate-180 h-24 truncate">{cls}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {geneNames.map((gene, rowIdx) => (
              <tr key={gene} className="hover:bg-gray-50">
                <td className="py-1.5 pr-2 font-mono font-bold text-gray-800 border-b border-gray-100 whitespace-nowrap">{gene}</td>
                {matrix[rowIdx].map((isActive, colIdx) => (
                  <td key={colIdx} className="p-1 border-b border-gray-100">
                    <div className="w-full flex justify-center">
                      <div 
                        className={`w-4 h-4 rounded-sm ${isActive ? 'bg-red-500 shadow-sm' : 'bg-gray-100'}`}
                        title={isActive ? `${gene} compromises ${drugClasses[colIdx]}` : ''}
                      ></div>
                    </div>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
