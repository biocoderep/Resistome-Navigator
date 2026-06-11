import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface FilterState {
  organism: string | null;
  project: string | null;
  region: string | null;
  dateRange: [string | null, string | null]; // YYYY-MM-DD
  confidenceTier: string | null;
}

interface FilterContextType {
  filters: FilterState;
  setFilters: React.Dispatch<React.SetStateAction<FilterState>>;
  clearFilters: () => void;
}

const defaultFilters: FilterState = {
  organism: null,
  project: null,
  region: null,
  dateRange: [null, null],
  confidenceTier: null,
};

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export function FilterProvider({ children }: { children: ReactNode }) {
  const [filters, setFilters] = useState<FilterState>(defaultFilters);

  const clearFilters = () => setFilters(defaultFilters);

  return (
    <FilterContext.Provider value={{ filters, setFilters, clearFilters }}>
      {children}
    </FilterContext.Provider>
  );
}

export function useDashboardFilters() {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useDashboardFilters must be used within a FilterProvider');
  }
  return context;
}
