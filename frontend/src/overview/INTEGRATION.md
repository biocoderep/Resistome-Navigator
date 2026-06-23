# Overview Dashboard Integration Contract

This document provides exact specifications for integrating the new `OverviewDashboard` component.

## 1. Route Mounting
The dashboard has been registered in `frontend/src/routes.jsx` under the path `/overview`.
- **Component:** `frontend/src/overview/OverviewDashboard.tsx`
- **URL Path:** `/admin/overview` (due to the layout prefix)

## 2. API Endpoints
The component expects exactly **one new endpoint** to be implemented by the backend. It does not hit existing endpoints to avoid over-fetching heavy isolate lists.

### [NEW] Aggregate Overview Endpoint
- **Method:** `GET`
- **Path:** `/api/v1/isolates/overview-summary`
- **Optional Query Params:** `?batch_id=<uuid>` (if filtering by project/batch)
- **Expected Response Type:** `OverviewSummaryPayload` (defined in `frontend/src/types/amr.ts`).

#### TypeScript Contract
```typescript
export interface OverviewSummaryPayload {
  total_isolates: number;
  amr_genes_per_isolate_avg: number;
  phenotype_distribution: { S: number; I: number; R: number };
  virulence_categories: Record<string, number>;
  confidence_tiers: Record<string, number>;
}
```

## 3. Environment Variables & Mock Data
- **Variable:** `VITE_USE_MOCK`
- **Effect:** When `VITE_USE_MOCK=true`, the dashboard will bypass the `/api/v1/isolates/overview-summary` endpoint entirely and resolve immediately with `mockOverviewSummary` defined in `frontend/src/mockData.ts`.
- **Loading & Error States:** Handled internally by `useAmrFetch`. If the API fails when mock is off, the component renders a crisp error box.

## 4. "Go Live" Instructions for Integrator
1. Implement the `GET /api/v1/isolates/overview-summary` endpoint in FastAPI (e.g., in `backend/api/routes/analysis_routes.py` or similar).
2. Ensure the returned JSON strictly matches the `OverviewSummaryPayload` shape above.
3. In your environment, set `VITE_USE_MOCK=false`.
4. Run the frontend. The dashboard will now execute real fetch calls to your new endpoint.

## 5. Assumptions & TODOs
- **Assumption:** The `recharts` package handles responsive resizing smoothly within the Tailwind grid layout.
- **Assumption:** S/I/R string literal keys map directly to Susceptible, Intermediate, Resistant.
- **TODO for Integrator:** If authorization headers are required for the new endpoint, ensure they are attached in `frontend/src/hooks/useAmrData.ts` (currently it uses standard browser `fetch` without interceptors).
