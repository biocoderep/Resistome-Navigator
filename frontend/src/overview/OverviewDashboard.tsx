import React from 'react';
import { Link } from 'react-router-dom';
import { Activity, ShieldAlert, GitMerge, FileCheck } from 'lucide-react';
import { 
  PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { useOverviewSummary } from '../hooks/useAmrData';

export default function OverviewDashboard() {
  const { data, loading, error } = useOverviewSummary();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4 m-4">
        <h3 className="text-red-800 font-medium">Error Loading Overview</h3>
        <p className="text-red-600">{error?.message || "Failed to load summary data."}</p>
      </div>
    );
  }

  // Transform data for charts
  const phenotypeData = [
    { name: 'Susceptible (S)', value: data.phenotype_distribution.S || 0 },
    { name: 'Intermediate (I)', value: data.phenotype_distribution.I || 0 },
    { name: 'Resistant (R)', value: data.phenotype_distribution.R || 0 },
  ];

  const virulenceData = Object.entries(data.virulence_categories || {}).map(([name, value]) => ({
    name, value
  })).sort((a, b) => b.value - a.value);

  const confidenceData = Object.entries(data.confidence_tiers || {}).map(([name, value]) => ({
    name, value
  }));

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">AMR Overview</h1>
          <p className="text-slate-500">Global summary of isolate and resistance metrics</p>
        </div>
        <div className="flex gap-4">
          <Link to="/dashboard" className="px-4 py-2 bg-white border border-slate-300 rounded-md shadow-sm text-slate-700 hover:bg-slate-50 transition-colors">
            View Cohort Dashboard
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-blue-100 rounded-full text-blue-600">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Total Isolates</p>
            <h3 className="text-2xl font-bold text-slate-800">{data.total_isolates}</h3>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-red-100 rounded-full text-red-600">
            <ShieldAlert size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Avg AMR Genes/Isolate</p>
            <h3 className="text-2xl font-bold text-slate-800">{data.amr_genes_per_isolate_avg.toFixed(1)}</h3>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-amber-100 rounded-full text-amber-600">
            <GitMerge size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Total Resistant Phenotypes</p>
            <h3 className="text-2xl font-bold text-slate-800">{data.phenotype_distribution.R || 0}</h3>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-slate-100 flex items-center gap-4">
          <div className="p-3 bg-green-100 rounded-full text-green-600">
            <FileCheck size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">High Confidence Findings</p>
            <h3 className="text-2xl font-bold text-slate-800">{data.confidence_tiers['HIGH'] || 0}</h3>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Phenotype Distribution */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-100 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">S/I/R Phenotype Distribution</h3>
          <div className="h-64">
            {phenotypeData.reduce((acc, curr) => acc + curr.value, 0) === 0 ? (
              <div className="flex h-full items-center justify-center text-slate-400">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={phenotypeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    <Cell fill="#10B981" /> {/* S: Green */}
                    <Cell fill="#F59E0B" /> {/* I: Amber */}
                    <Cell fill="#EF4444" /> {/* R: Red */}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Confidence Tier Breakdown */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-100 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Confidence Tier Breakdown</h3>
          <div className="h-64">
            {confidenceData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-slate-400">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={confidenceData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    <Cell fill="#10B981" /> {/* High */}
                    <Cell fill="#3B82F6" /> {/* Medium */}
                    <Cell fill="#9CA3AF" /> {/* Low */}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Virulence Category Mix */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-100 p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">Virulence Category Mix</h3>
          <div className="h-72">
            {virulenceData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-slate-400">No data available</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={virulenceData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <RechartsTooltip cursor={{ fill: '#f1f5f9' }} />
                  <Bar dataKey="value" fill="#6366F1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
