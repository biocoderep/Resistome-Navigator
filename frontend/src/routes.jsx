/*!

=========================================================
* Light Bootstrap Dashboard React - v2.0.1
=========================================================

* Product Page: https://www.creative-tim.com/product/light-bootstrap-dashboard-react
* Copyright 2022 Creative Tim (https://www.creative-tim.com)
* Licensed under MIT (https://github.com/creativetimofficial/light-bootstrap-dashboard-react/blob/master/LICENSE.md)

* Coded by Creative Tim

=========================================================

* The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

*/
import DashboardRouter from "./DashboardRouter";
import App from "./App";
import OverviewDashboard from "./overview/OverviewDashboard";

const dashboardRoutes = [
  {
    path: "/overview",
    name: "Overview",
    icon: "nc-icon nc-layout-11",
    component: OverviewDashboard,
    layout: "/admin"
  },
  {
    path: "/dashboard",
    name: "Results Dashboard",
    icon: "nc-icon nc-chart-pie-35",
    component: DashboardRouter,
    layout: "/admin"
  },
  {
    path: "/new-analysis",
    name: "New Analysis",
    icon: "nc-icon nc-cloud-upload-94",
    component: App, // we might need to be careful if App is the router root, but we can just link to /
    layout: ""
  }
];

export default dashboardRoutes;
