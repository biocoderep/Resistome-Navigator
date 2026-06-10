import React, { useState, useEffect } from 'react';

const STAGES = [
  { id: 'S1', name: 'Genome Validation', time: '14s' },
  { id: 'S2', name: 'Alignment & Mapping', time: '1m 24s' },
  { id: 'S3', name: 'AMR Detection', time: '42s' },
  { id: 'S4', name: 'Mutation Profiling', time: '35s' },
  { id: 'S5', name: 'Mechanism Classifier', time: '12s' },
  { id: 'S6', name: 'Phenotype Prediction', time: '8s' },
  { id: 'S7', name: 'Virulence Factors', time: '18s' },
  { id: 'S8', name: 'Confidence Aggregation', time: '5s' },
  { id: 'S9', name: 'Report Generation', time: '11s' },
];

export default function PipelineTracker() {
  const [currentStep, setCurrentStep] = useState(0);

  // Simulate pipeline progress
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep(prev => (prev < STAGES.length ? prev + 1 : prev));
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="p-6 h-full flex flex-col gap-6 items-center">
      
      <div className="text-center max-w-2xl mb-8">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Operational Telemetry</h3>
        <p className="text-sm text-gray-500">
          Live tracking of asynchronous tasks processed by Celery/RabbitMQ across the 9 microservices.
        </p>
      </div>

      <div className="w-full max-w-2xl bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
        
        <div className="flex justify-between items-center mb-8 pb-4 border-b border-gray-100">
          <div>
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider">Job ID</div>
            <div className="text-sm font-mono text-gray-900">req_8f72a9b1c4</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider">Status</div>
            <div className="text-sm font-bold text-blue-600">
              {currentStep < STAGES.length ? 'Processing...' : 'Complete'}
            </div>
          </div>
        </div>

        <div className="relative">
          {/* Vertical line connecting nodes */}
          <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-gray-100"></div>
          
          <div className="flex flex-col gap-6">
            {STAGES.map((stage, i) => {
              const isCompleted = i < currentStep;
              const isActive = i === currentStep;
              const isPending = i > currentStep;
              
              return (
                <div key={stage.id} className="relative flex items-center gap-6">
                  {/* Node */}
                  <div 
                    className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-sm z-10 transition-colors duration-500 ${
                      isCompleted ? 'bg-[#198038] text-white' : 
                      isActive ? 'bg-[#0f62fe] text-white shadow-[0_0_0_4px_rgba(15,98,254,0.2)]' : 
                      'bg-gray-100 text-gray-400 border-2 border-gray-200'
                    }`}
                  >
                    {isCompleted ? '✓' : stage.id}
                  </div>
                  
                  {/* Content */}
                  <div className={`flex-1 flex justify-between items-center ${isPending ? 'opacity-40' : 'opacity-100'} transition-opacity duration-500`}>
                    <div>
                      <div className={`font-bold ${isActive ? 'text-blue-600' : 'text-gray-900'}`}>{stage.name}</div>
                      <div className="text-xs text-gray-500 font-mono mt-1">
                        {isCompleted ? `Took ${stage.time}` : isActive ? 'Running...' : 'Pending'}
                      </div>
                    </div>
                    {isActive && (
                      <div className="w-5 h-5 border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin"></div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>

    </div>
  );
}
