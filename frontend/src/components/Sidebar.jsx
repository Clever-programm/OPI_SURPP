import { NavLink, useLocation } from 'react-router-dom'
import './Sidebar.css'

const navItems = [
  { path: '/', label: 'Главная' },
  { path: '/schedule', label: 'Расписание' },
  { path: '/orders', label: 'Заказы' },
  { path: '/recipes', label: 'Рецептуры' },
  { path: '/employees', label: 'Сотрудники' },
  { path: '/equipment', label: 'Оборудование' },
  { path: '/warehouse', label: 'Склад' },
]

function Sidebar() {
  const location = useLocation()

  return (
    <aside className="sidebar" id="sidebar">
      <div className="sidebar-logo">
        <span className="sidebar-logo-text">СУРПП</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item, index) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'sidebar-link--active' : ''}`
            }
            id={`nav-${item.path.replace('/', '') || 'home'}`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {/* Footer content removed per user request */}
      </div>
    </aside>
  )
}

export default Sidebar
