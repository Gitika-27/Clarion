import { Routes, Route } from 'react-router-dom'
import { StatusProvider } from './context/StatusContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Catalog from './pages/Catalog'
import Review from './pages/Review'
import Outliers from './pages/Outliers'
import Export from './pages/Export'

export default function App() {
  return (
    <StatusProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="catalog" element={<Catalog />} />
          <Route path="review/*" element={<Review />} />
          <Route path="outliers" element={<Outliers />} />
          <Route path="export" element={<Export />} />
        </Route>
      </Routes>
    </StatusProvider>
  )
}
