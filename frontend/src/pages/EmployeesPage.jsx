import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { employeesApi, competencesApi } from '../api/client.js'
import './EntityPages.css'

function EmployeesPage() {
  const [employees, setEmployees] = useState([])
  const [competences, setCompetences] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ name: '', active: true })
  const [submitting, setSubmitting] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [empCompetences, setEmpCompetences] = useState({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [empData, compData] = await Promise.all([
        employeesApi.getAll({ limit: 100 }),
        competencesApi.getAll({ limit: 100 }).catch(() => ({ items: [] })),
      ])
      setEmployees(empData.items || [])
      setCompetences(compData.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadCompetences = async (id) => {
    if (empCompetences[id]) return
    try {
      const data = await employeesApi.getCompetences(id)
      setEmpCompetences(prev => ({ ...prev, [id]: data }))
    } catch (err) {
      console.error('Ошибка загрузки компетенций:', err)
    }
  }

  const toggleExpand = (id) => {
    if (expandedId === id) {
      setExpandedId(null)
    } else {
      setExpandedId(id)
      loadCompetences(id)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const newEmp = await employeesApi.create({
        name: formData.name,
        active: formData.active,
      })
      setEmployees(prev => [...prev, newEmp])
      setShowForm(false)
      setFormData({ name: '', active: true })
    } catch (err) {
      alert('Ошибка создания: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Удалить сотрудника?')) return
    try {
      await employeesApi.delete(id)
      setEmployees(prev => prev.filter(e => e.id !== id))
      if (expandedId === id) setExpandedId(null)
    } catch (err) {
      alert('Ошибка удаления: ' + err.message)
    }
  }

  const handleToggleActive = async (emp) => {
    try {
      const updated = await employeesApi.updateActive(emp.id, !emp.active)
      setEmployees(prev => prev.map(e => e.id === emp.id ? { ...e, active: updated.active } : e))
    } catch (err) {
      alert('Ошибка обновления: ' + err.message)
    }
  }

  return (
    <div className="employees-page" id="page-employees">
      <Header title="Сотрудники" />

      <div className="page-toolbar">
        <button className="btn-create" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Отмена' : '+ Новый сотрудник'}
        </button>
        <span className="page-count">
          Всего: {employees.length} · Активных: {employees.filter(e => e.active).length}
        </span>
      </div>

      {showForm && (
        <form className="entity-form" onSubmit={handleCreate}>
          <div className="form-row">
            <label>
              ФИО сотрудника:
              <input type="text" value={formData.name} placeholder="Иванова Мария Петровна"
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                required minLength={3} maxLength={150} />
            </label>
            <label>
              Статус:
              <select value={formData.active ? 'true' : 'false'}
                onChange={e => setFormData({ ...formData, active: e.target.value === 'true' })}>
                <option value="true">Активен</option>
                <option value="false">Неактивен</option>
              </select>
            </label>
          </div>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'Создание...' : 'Добавить сотрудника'}
          </button>
        </form>
      )}

      {error && (
        <div className="error-banner">⚠️ {error}
          <button onClick={loadData} className="error-retry">Повторить</button>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">Загрузка сотрудников...</div>
      ) : (
        <div className="entity-list">
          {employees.map((emp, idx) => (
            <div className="entity-card" key={emp.id}
              style={{ animationDelay: `${idx * 80 + 200}ms` }}>
              <div className="entity-card-main" onClick={() => toggleExpand(emp.id)}>
                <div className="entity-card-info">
                  <span className="entity-card-name">{emp.name}</span>
                  <div className="entity-card-meta">
                    <span className="entity-card-id">ID: {emp.id}</span>
                    <span className={`status-badge ${emp.active ? 'active' : 'inactive'}`}>
                      {emp.active ? 'Активен' : 'Неактивен'}
                    </span>
                  </div>
                </div>
                <div className="entity-card-actions">
                  <button className="btn-expand">{expandedId === emp.id ? '▲' : '▼'}</button>
                  <button className="btn-next-status"
                    onClick={(e) => { e.stopPropagation(); handleToggleActive(emp) }}>
                    {emp.active ? 'Деактивировать' : 'Активировать'}
                  </button>
                  <button className="btn-delete-sm"
                    onClick={(e) => { e.stopPropagation(); handleDelete(emp.id) }}>✕</button>
                </div>
              </div>

              {expandedId === emp.id && (
                <div className="entity-details">
                  <div className="details-section">
                    <h4>Компетенции (квалификации)</h4>
                    {empCompetences[emp.id]?.length > 0 ? (
                      <ul className="details-list">
                        {empCompetences[emp.id].map(c => (
                          <li key={c.id}>
                            {c.competence_name || `Компетенция #${c.competence_id}`}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="details-empty">Нет назначенных компетенций</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
          {employees.length === 0 && <div className="entity-empty">Нет сотрудников</div>}
        </div>
      )}
    </div>
  )
}

export default EmployeesPage
