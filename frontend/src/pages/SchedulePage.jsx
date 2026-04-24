import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { scheduleApi, employeesApi, equipmentApi } from '../api/client.js'
import './SchedulePage.css'

function SchedulePage() {
  const [scheduleItems, setScheduleItems] = useState([])
  const [employees, setEmployees] = useState([])
  const [equipment, setEquipment] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showGenerate, setShowGenerate] = useState(false)
  const [generateForm, setGenerateForm] = useState({
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 30 * 24 * 3600000).toISOString().split('T')[0],
    prioritize_by: 'due_date',
  })
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [schedData, empData, eqData] = await Promise.all([
        scheduleApi.getAll({ limit: 100 }),
        employeesApi.getAll({ limit: 100 }),
        equipmentApi.getAll({ limit: 100 }),
      ])
      setScheduleItems(schedData.items || [])
      setEmployees(empData.items || [])
      setEquipment(eqData.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async (e) => {
    e.preventDefault()
    setGenerating(true)
    try {
      const result = await scheduleApi.generate(generateForm)
      alert(`Расписание сформировано!\nЗапланировано заказов: ${result.orders_planned}\nОпераций: ${result.scheduled_count}`)
      setShowGenerate(false)
      loadData()
    } catch (err) {
      alert('Ошибка формирования: ' + err.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleDeleteSchedule = async (id) => {
    if (!confirm('Удалить запись расписания?')) return
    try {
      await scheduleApi.delete(id)
      setScheduleItems(prev => prev.filter(s => s.id !== id))
    } catch (err) {
      alert('Ошибка удаления: ' + err.message)
    }
  }

  const formatDateTime = (dt) => {
    if (!dt) return '—'
    const d = new Date(dt)
    return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  const empMap = Object.fromEntries(employees.map(e => [e.id, e.name]))
  const eqMap = Object.fromEntries(equipment.map(e => [e.id, e.name]))

  // Группировка по employee
  const grouped = {}
  scheduleItems.forEach(item => {
    const empId = item.employee_id || 0
    const empName = item.employee_name || empMap[empId] || 'Не назначен'
    if (!grouped[empId]) grouped[empId] = { name: empName, items: [] }
    grouped[empId].items.push(item)
  })

  return (
    <div className="schedule-page" id="page-schedule">
      <Header title="Расписание" />

      <div className="schedule-toolbar">
        <button className="btn-create" onClick={() => setShowGenerate(!showGenerate)}>
          {showGenerate ? '✕ Отмена' : '⚡ Сформировать расписание'}
        </button>
        <span className="schedule-count">Записей: {scheduleItems.length}</span>
      </div>

      {showGenerate && (
        <form className="generate-form" onSubmit={handleGenerate}>
          <div className="form-row">
            <label>
              Дата начала:
              <input type="date" value={generateForm.start_date}
                onChange={e => setGenerateForm({ ...generateForm, start_date: e.target.value })} required />
            </label>
            <label>
              Дата окончания:
              <input type="date" value={generateForm.end_date}
                onChange={e => setGenerateForm({ ...generateForm, end_date: e.target.value })} required />
            </label>
            <label>
              Приоритет:
              <select value={generateForm.prioritize_by}
                onChange={e => setGenerateForm({ ...generateForm, prioritize_by: e.target.value })}>
                <option value="due_date">По сроку</option>
                <option value="priority">По приоритету</option>
                <option value="created_at">По дате создания</option>
              </select>
            </label>
          </div>
          <button type="submit" className="btn-submit" disabled={generating}>
            {generating ? 'Формирование...' : 'Сформировать'}
          </button>
        </form>
      )}

      {error && (
        <div className="error-banner">⚠️ {error}
          <button onClick={loadData} className="error-retry">Повторить</button>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">Загрузка расписания...</div>
      ) : (
        <div className="schedule-list">
          {Object.keys(grouped).length === 0 && (
            <div className="schedule-empty">Расписание пусто. Сформируйте его!</div>
          )}
          {Object.entries(grouped).map(([empId, group], gIdx) => (
            <div className="schedule-card" key={empId}
              style={{ animationDelay: `${gIdx * 120 + 200}ms` }}>
              <div className="schedule-card-header">
                <strong>Сотрудник: {group.name}</strong>
                <span className="schedule-card-count">{group.items.length} операций</span>
              </div>
              <div className="schedule-table-wrapper">
                <table className="schedule-table">
                  <thead>
                    <tr>
                      <th>Операция</th>
                      <th>Изделие</th>
                      <th>Начало</th>
                      <th>Окончание</th>
                      <th>Длит. (мин)</th>
                      <th>Оборудование</th>
                      <th>Заказ</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {group.items.map(item => (
                      <tr key={item.id}>
                        <td>{item.operation_name || item.name || `Операция #${item.operation_id}`}</td>
                        <td>{item.recipe_name || '—'}</td>
                        <td>{formatDateTime(item.start_time)}</td>
                        <td>{formatDateTime(item.end_time)}</td>
                        <td>{item.duration_minutes}</td>
                        <td>{item.equipment_name || eqMap[item.equipment_id] || '—'}</td>
                        <td>#{item.order_id}</td>
                        <td>
                          <button className="btn-delete-sm" onClick={() => handleDeleteSchedule(item.id)}>✕</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SchedulePage
