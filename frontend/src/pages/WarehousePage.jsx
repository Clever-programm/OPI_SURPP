import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { stockApi, ingredientsApi } from '../api/client.js'
import './EntityPages.css'

function WarehousePage() {
  const [stockItems, setStockItems] = useState([])
  const [ingredients, setIngredients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [mode, setMode] = useState(null) // 'receive' | 'writeoff'
  const [formData, setFormData] = useState({ ingredient_id: '', quantity: '', expiration_date: '' })
  const [submitting, setSubmitting] = useState(false)
  const [expiring, setExpiring] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [stockData, ingredientsData, expiringData] = await Promise.all([
        stockApi.getAll({ limit: 100 }),
        ingredientsApi.getAll({ limit: 100 }),
        stockApi.getExpiringSoon(7).catch(() => ({ expiring_soon: [] })),
      ])
      setStockItems(stockData.items || [])
      setIngredients(ingredientsData.items || [])
      setExpiring(expiringData.expiring_soon || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const ingredientMap = Object.fromEntries(ingredients.map(i => [i.id, i]))

  const handleReceive = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await stockApi.receive({
        ingredient_id: Number(formData.ingredient_id),
        quantity: Number(formData.quantity),
        expiration_date: formData.expiration_date,
      })
      setMode(null)
      setFormData({ ingredient_id: '', quantity: '', expiration_date: '' })
      loadData()
    } catch (err) {
      alert('Ошибка поступления: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleWriteOff = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await stockApi.writeOff({
        ingredient_id: Number(formData.ingredient_id),
        quantity: Number(formData.quantity),
      })
      setMode(null)
      setFormData({ ingredient_id: '', quantity: '', expiration_date: '' })
      loadData()
    } catch (err) {
      alert('Ошибка списания: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '—'
    const d = new Date(dateStr)
    return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`
  }

  const formatDateTime = (dtStr) => {
    if (!dtStr) return '—'
    const d = new Date(dtStr)
    return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  return (
    <div className="warehouse-page" id="page-warehouse">
      <Header title="Склад" />

      <div className="page-toolbar">
        <div className="stock-toolbar-btns">
          <button className="btn-receive" onClick={() => setMode(mode === 'receive' ? null : 'receive')}>
            {mode === 'receive' ? '✕ Отмена' : '📦 Поступление'}
          </button>
          <button className="btn-writeoff" onClick={() => setMode(mode === 'writeoff' ? null : 'writeoff')}>
            {mode === 'writeoff' ? '✕ Отмена' : '📤 Списание'}
          </button>
        </div>
        <span className="page-count">
          Позиций: {stockItems.length}
          {expiring.length > 0 && (
            <span className="expiry-warning"> · ⚠ Истекает: {expiring.length}</span>
          )}
        </span>
      </div>

      {/* Receive form */}
      {mode === 'receive' && (
        <form className="entity-form" onSubmit={handleReceive}>
          <div className="form-row">
            <label>
              Ингредиент:
              <select value={formData.ingredient_id}
                onChange={e => setFormData({ ...formData, ingredient_id: e.target.value })} required>
                <option value="">— Выберите —</option>
                {ingredients.map(i => (
                  <option key={i.id} value={i.id}>{i.name} ({i.unit})</option>
                ))}
              </select>
            </label>
            <label>
              Количество:
              <input type="number" value={formData.quantity} min={0.01} step={0.01}
                onChange={e => setFormData({ ...formData, quantity: e.target.value })} required />
            </label>
            <label>
              Срок годности:
              <input type="date" value={formData.expiration_date}
                onChange={e => setFormData({ ...formData, expiration_date: e.target.value })} required
                min={new Date().toISOString().split('T')[0]} />
            </label>
          </div>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'Оформление...' : 'Оформить поступление'}
          </button>
        </form>
      )}

      {/* Write-off form */}
      {mode === 'writeoff' && (
        <form className="entity-form" onSubmit={handleWriteOff}>
          <div className="form-row">
            <label>
              Ингредиент:
              <select value={formData.ingredient_id}
                onChange={e => setFormData({ ...formData, ingredient_id: e.target.value })} required>
                <option value="">— Выберите —</option>
                {ingredients.map(i => (
                  <option key={i.id} value={i.id}>{i.name} ({i.unit})</option>
                ))}
              </select>
            </label>
            <label>
              Количество для списания:
              <input type="number" value={formData.quantity} min={0.01} step={0.01}
                onChange={e => setFormData({ ...formData, quantity: e.target.value })} required />
            </label>
          </div>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'Оформление...' : 'Списать'}
          </button>
        </form>
      )}

      {error && (
        <div className="error-banner">⚠️ {error}
          <button onClick={loadData} className="error-retry">Повторить</button>
        </div>
      )}

      {/* Expiring soon warning */}
      {expiring.length > 0 && (
        <div className="entity-card" style={{ borderLeft: '4px solid #CC5500', marginBottom: 16, animation: 'fadeIn 0.4s ease both' }}>
          <div style={{ padding: '14px 20px' }}>
            <h3 style={{ margin: '0 0 8px', fontSize: '0.9rem', color: '#CC5500' }}>
              ⚠️ Истекает срок годности ({expiring.length} позиций)
            </h3>
            <ul className="details-list">
              {expiring.map((item, i) => (
                <li key={i}>
                  <strong>{item.ingredient_name}</strong>: {item.quantity} ед. —
                  <span className="expiry-warning"> {item.days_until_expiry} дн. до истечения</span> (до {formatDate(item.expiration_date)})
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">Загрузка склада...</div>
      ) : (
        <div className="entity-card" style={{ animation: 'fadeIn 0.5s ease both' }}>
          <div className="stock-table-wrapper">
            <table className="stock-table">
              <thead>
                <tr>
                  <th>Ингредиент</th>
                  <th>Количество</th>
                  <th>Ед. изм.</th>
                  <th>Срок годности</th>
                  <th>Поступление</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {stockItems.map(item => {
                  const ing = ingredientMap[item.ingredient_id]
                  const isExpiringSoon = item.expiration_date &&
                    (new Date(item.expiration_date) - new Date()) / (1000 * 3600 * 24) <= 7
                  return (
                    <tr key={item.id}>
                      <td><strong>{ing?.name || `Ингредиент #${item.ingredient_id}`}</strong></td>
                      <td>
                        <span className="quantity-badge">{item.quantity}</span>
                      </td>
                      <td>{ing?.unit ? <span className="unit-badge">{ing.unit}</span> : '—'}</td>
                      <td>
                        {item.expiration_date ? (
                          <span className={isExpiringSoon ? 'expiry-warning' : 'expiry-ok'}>
                            {formatDate(item.expiration_date)}
                            {isExpiringSoon && ' ⚠'}
                          </span>
                        ) : '—'}
                      </td>
                      <td>{formatDateTime(item.received_at)}</td>
                      <td style={{ textAlign: 'center' }}>
                        <button 
                          className="btn-action-small"
                          title="Списать из этой партии"
                          onClick={() => {
                            const qty = prompt(`Сколько списать из этой партии? (Доступно: ${item.quantity})`, item.quantity);
                            if (qty && !isNaN(qty) && qty > 0) {
                              const doWriteOff = async () => {
                                setSubmitting(true);
                                try {
                                  await stockApi.writeOff({
                                    ingredient_id: item.ingredient_id,
                                    quantity: Number(qty),
                                    stock_id: item.id
                                  });
                                  loadData();
                                } catch (err) {
                                  alert('Ошибка: ' + err.message);
                                } finally {
                                  setSubmitting(false);
                                }
                              };
                              doWriteOff();
                            }
                          }}
                        >
                          Вычесть
                        </button>
                      </td>
                    </tr>
                  )
                })}
                {stockItems.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)', fontWeight: 600 }}>
                      Склад пуст
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default WarehousePage
