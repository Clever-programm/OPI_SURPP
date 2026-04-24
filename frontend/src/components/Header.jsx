import './Header.css'

function Header({ title }) {
  return (
    <header className="header" id="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-user" id="header-user">
        <span className="header-user-name">Имя Фамилия</span>
        <div className="header-user-avatar">
          <svg viewBox="0 0 40 40" width="40" height="40" fill="none">
            <circle cx="20" cy="20" r="20" fill="#AED6F1"/>
            <circle cx="20" cy="15" r="7" fill="#5DADE2"/>
            <ellipse cx="20" cy="32" rx="12" ry="8" fill="#5DADE2"/>
          </svg>
        </div>
      </div>
    </header>
  )
}

export default Header
