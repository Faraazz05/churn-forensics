import { Routes, Route } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import LandingPage from './index'

import { DemoEntry } from './pages/Demo'
import { ModelXAI } from './pages/ModelXAI'
import { Dashboard } from './pages/Dashboard'
import { UploadData } from './pages/Upload'
import { Processing } from './pages/Processing'
import { CustomerProfile } from './pages/CustomerProfile'
import { SegmentsPage } from './pages/Segments'
import { DriftAnalysis } from './pages/DriftAnalysis'
import { InsightsPage } from './pages/Insights'
import { ReportsPage } from './pages/Reports'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/demo" element={<DemoEntry />} />
      
      <Route element={<AppShell />}>
        <Route path="/demo/model" element={<ModelXAI />} />
        <Route path="/demo/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<UploadData />} />
        <Route path="/processing/:runId" element={<Processing />} />
        <Route path="/analysis/model" element={<ModelXAI />} />
        <Route path="/analysis/dashboard" element={<Dashboard />} />
        <Route path="/customers/:id" element={<CustomerProfile />} />
        <Route path="/segments" element={<SegmentsPage />} />
        <Route path="/drift" element={<DriftAnalysis />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
      </Route>
    </Routes>
  )
}
