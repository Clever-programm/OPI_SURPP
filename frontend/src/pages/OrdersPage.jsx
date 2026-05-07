import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { ordersApi, recipesApi } from '../api/client.js'
import './OrdersPage.css'

const STATUS_MAP = {
  new: 'Ожидает',
  planned: 'Запланирован',
  in_progress: 'Выпекание',
  done: 'Готов',
}

const statusColors = {
  new: { bg: '#FFF3C4', color: '#B8860B', border: '#F0C040' },
  planned: { bg: '#AED6F1', color: '#1B4F72', border: '#5DADE2' },
  in_progress: { bg: '#FFDAB9', color: '#CC5500', border: '#F0A050' },
  done: { bg: '#D4EDDA', color: '#1E7E34', border: '#80C090' },
}

function OrdersPage() {
  const [orders, setOrders] = useState([])
  const [recipes, setRecipes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ due_date: '', priority: 2, recipe_id: '', quantity: 1 })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [ordersData, recipesData] = await Promise.all([
        ordersApi.getAll({ limit: 100, sort_by: 'due_date', sort_order: 'asc' }),
        recipesApi.getAll({ limit: 100 }),
      ])
      setOrders(ordersData.items || [])
      setRecipes(recipesData.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Удалить этот заказ?')) return
    try {
      await ordersApi.delete(id)
      setOrders(prev => prev.filter(o => o.id !== id))
    } catch (err) {
      alert('Ошибка удаления: ' + err.message)
    }
  }

  const handleStatusChange = async (id, newStatus) => {
    try {
      await ordersApi.updateStatus(id, newStatus)
      setOrders(prev => prev.map(o => o.id === id ? { ...o, status: newStatus } : o))
    } catch (err) {
      alert('Ошибка обновления статуса: ' + err.message)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const newOrder = await ordersApi.create({
        due_date: formData.due_date,
        priority: Number(formData.priority),
        items: formData.recipe_id ? [{ recipe_id: Number(formData.recipe_id), quantity: Number(formData.quantity) }] : [],
      })
      setOrders(prev => [...prev, newOrder])
      setShowForm(false)
      setFormData({ due_date: '', priority: 2, recipe_id: '', quantity: 1 })
    } catch (err) {
      alert('Ошибка создания: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}`
  }

  const nextStatusMap = {
    new: 'planned',
    planned: 'in_progress',
    in_progress: 'done',
  }

  return (
    <div className="orders-page" id="page-orders">
      <Header title="Заказы" />

      <div className="orders-toolbar">
        <button className="btn-create" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Отмена' : '+ Новый заказ'}
        </button>
        <span className="orders-count">
          Всего: {orders.length}
        </span>
      </div>

      {showForm && (
        <form className="order-form" onSubmit={handleCreate}>
          <div className="form-row">
            <label>
              Дата выполнения:
              <input
                type="date"
                value={formData.due_date}
                onChange={e => setFormData({ ...formData, due_date: e.target.value })}
                required
                min={new Date().toISOString().split('T')[0]}
              />
            </label>
            <label>
              Приоритет:
              <select
                value={formData.priority}
                onChange={e => setFormData({ ...formData, priority: e.target.value })}
              >
                <option value={1}>Высокий</option>
                <option value={2}>Средний</option>
                <option value={3}>Низкий</option>
              </select>
            </label>
          </div>
          <div className="form-row">
            <label>
              Изделие (рецептура):
              <select
                value={formData.recipe_id}
                onChange={e => setFormData({ ...formData, recipe_id: e.target.value })}
              >
                <option value="">— Без позиции —</option>
                {recipes.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </label>
            {formData.recipe_id && (
              <label>
                Количество:
                <input
                  type="number"
                  min={1}
                  value={formData.quantity}
                  onChange={e => setFormData({ ...formData, quantity: e.target.value })}
                  required
                />
              </label>
            )}
          </div>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'Создание...' : 'Создать заказ'}
          </button>
        </form>
      )}

      {error && (
        <div className="error-banner">
          ⚠️ {error}
          <button onClick={loadData} className="error-retry">Повторить</button>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">Загрузка заказов...</div>
      ) : (
        <div className="orders-list">
          {orders.map((order, idx) => {
            const style = statusColors[order.status] || statusColors.new
            const nextStatus = nextStatusMap[order.status]
            return (
              <div
                className="order-card"
                key={order.id}
                id={`order-card-${order.id}`}
                style={{ animationDelay: `${idx * 80 + 200}ms` }}
              >
                <div className="order-card-left">
                  <div className="order-card-header">
                    <span className="order-card-num">Заказ №{order.id}</span>
                    <div className="order-card-dates">
                      <div>Создан: {formatDate(order.created_at)}</div>
                      <div>Выполнить до: {formatDate(order.due_date)}</div>
                    </div>
                  </div>
                  <div className="order-card-meta">
                    Приоритет: {order.priority === 1 ? '🔴 Высокий' : order.priority === 2 ? '🟡 Средний' : '🟢 Низкий'}
                  </div>
                </div>

                <div className="order-card-right">
                  <div className="order-card-status-row">
                    <span className="order-card-status-label">Статус:</span>
                    <span
                      className="order-card-status-badge"
                      style={{ background: style.bg, color: style.color, borderColor: style.border }}
                    >
                      {STATUS_MAP[order.status] || order.status}
                    </span>
                  </div>
                  {nextStatus && (
                    <button
                      className="btn-next-status"
                      onClick={() => handleStatusChange(order.id, nextStatus)}
                    >
                      → {STATUS_MAP[nextStatus]}
                    </button>
                  )}
                  <button
                    className="order-card-delete"
                    onClick={() => handleDelete(order.id)}
                  >
                    Удалить
                  </button>
                </div>
              </div>
            )
          })}

          {orders.length === 0 && !loading && (
            <div className="orders-empty">Нет заказов. Создайте первый!</div>
          )}
        </div>
      )}
    </div>
  )
}

export default OrdersPage
