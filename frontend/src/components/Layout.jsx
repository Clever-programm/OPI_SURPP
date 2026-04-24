import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import './Layout.css'

function Layout() {
  return (
    <div className="layout" id="layout">
      <Sidebar />
      <main className="layout-main">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
