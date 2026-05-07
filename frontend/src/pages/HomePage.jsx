import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { ordersApi, scheduleApi } from '../api/client.js'
import './HomePage.css'

/* Маппинг статусов бэкенда на русский */
const STATUS_MAP = {
  new: 'Новый',
  planned: 'Запланирован',
  in_progress: 'Выпекание',
  done: 'Готов',
}

function HomePage() {
  const [orders, setOrders] = useState([])
  const [stats, setStats] = useState({ total: 0, active: 0, problems: 0, violations: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Загружаем заказы
      const ordersData = await ordersApi.getAll({ limit: 100 })
      const items = ordersData.items || []
      setOrders(items)

      // Считаем статистику по статусам
      const total = items.length
      const active = items.filter(o => o.status === 'in_progress' || o.status === 'planned').length
      const problems = items.filter(o => {
        // Проблема — заказ просрочен (due_date < today и не done)
        if (o.status === 'done') return false
        const due = new Date(o.due_date)
        return due < new Date()
      }).length
      const violations = 0 // Пока нет бэкенд-метрики

      setStats({ total, active, problems, violations })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Ближайшие заказы (очередь) — берём первые 4 по дате
  const queueOrders = [...orders]
    .filter(o => o.status !== 'done')
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
    .slice(0, 4)

  // Данные для графика — подсчёт заказов по месяцам
  const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
  const monthCounts = new Array(12).fill(0)
  orders.forEach(o => {
    const m = new Date(o.created_at).getMonth()
    monthCounts[m]++
  })
  const maxCount = Math.max(...monthCounts, 1)

  // Рейтинг (рассчитываем как % выполненных заказов)
  const doneCount = orders.filter(o => o.status === 'done').length
  const rating = orders.length > 0 ? (doneCount / orders.length * 10).toFixed(1) : '0.0'

  const statCards = [
    { value: stats.total, label: 'Заказы', btnText: 'Все' },
    { value: stats.active, label: 'Активные', btnText: 'Подробнее' },
    { value: stats.problems, label: 'Проблемы', btnText: 'Просмотр' },
    { value: stats.violations, label: 'Нарушения', btnText: 'Просмотр' },
  ]

  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}`
  }

  return (
    <div className="home-page" id="page-home">
      <Header title="Главная" />

      {error && (
        <div className="error-banner">
          ⚠️ {error}
          <button onClick={loadData} className="error-retry">Повторить</button>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">Загрузка данных...</div>
      ) : (
        <>
          {/* Stats cards */}
          <div className="home-stats">
            {statCards.map((stat, i) => (
              <div
                className="stat-card"
                key={i}
                id={`stat-card-${i}`}
                style={{ animationDelay: `${i * 80 + 200}ms` }}
              >
                <div className="stat-value">{stat.value}</div>
                <div className="stat-label">{stat.label}</div>
                <button className="stat-btn">{stat.btnText}</button>
              </div>
            ))}
          </div>

          {/* Bottom section */}
          <div className="home-bottom">
            {/* Orders queue */}
            <div className="home-card home-orders" id="orders-queue" style={{ animationDelay: '500ms' }}>
              <h2 className="home-card-title">Очередь заказов</h2>
              <div className="orders-list">
                {queueOrders.length === 0 && (
                  <div className="orders-empty-hint">Нет активных заказов</div>
                )}
                {queueOrders.map((order, i) => (
                  <div className="order-row" key={order.id}>
                    <span className="order-pill">Заказ от {formatDate(order.created_at)}</span>
                    <span className="order-pill">До {formatDate(order.due_date)}</span>
                    <span className="order-status-pill" data-status={order.status}>
                      {STATUS_MAP[order.status] || order.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right column */}
            <div className="home-right">
              {/* Year chart */}
              <div className="home-card home-chart" id="year-chart" style={{ animationDelay: '600ms' }}>
                <h2 className="home-card-title">График года</h2>
                <div className="chart-container">
                  <div className="chart-bars">
                    {monthCounts.map((val, i) => (
                      <div className="chart-bar-wrapper" key={i}>
                        <div
                          className="chart-bar"
                          style={{
                            height: `${(val / maxCount) * 100}%`,
                            animationDelay: `${700 + i * 60}ms`
                          }}
                        />
                        <span className="chart-label">{months[i]}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Rating */}
              <div className="home-card home-rating" id="user-rating" style={{ animationDelay: '700ms' }}>
                <h2 className="home-card-title">Ваш рейтинг</h2>
                <div className="rating-content">
                  <div className="rating-score">{rating}</div>
                  <div className="rating-details">
                    <div className="rating-details-title">Итоги месяца</div>
                    <div className="rating-detail">Выполнено заказов: {doneCount}</div>
                    <div className="rating-detail">Просроченных: {stats.problems}</div>
                    <div className="rating-detail">Активных: {stats.active}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default HomePage
