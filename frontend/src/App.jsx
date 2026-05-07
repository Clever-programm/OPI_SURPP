import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import HomePage from './pages/HomePage.jsx'
import SchedulePage from './pages/SchedulePage.jsx'
import OrdersPage from './pages/OrdersPage.jsx'
import RecipesPage from './pages/RecipesPage.jsx'
import EmployeesPage from './pages/EmployeesPage.jsx'
import EquipmentPage from './pages/EquipmentPage.jsx'
import WarehousePage from './pages/WarehousePage.jsx'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/schedule" element={<SchedulePage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/recipes" element={<RecipesPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/equipment" element={<EquipmentPage />} />
        <Route path="/warehouse" element={<WarehousePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
