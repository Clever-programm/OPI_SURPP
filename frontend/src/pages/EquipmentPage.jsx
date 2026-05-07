import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { equipmentApi } from '../api/client.js'
import './EntityPages.css'

function EquipmentPage() {
  const [equipment, setEquipment] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ name: '', quantity: 1 })
  const [submitting, setSubmitting] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editQty, setEditQty] = useState(0)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await equipmentApi.getAll({ limit: 100 })
      setEquipment(data.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const newItem = await equipmentApi.create({
        name: formData.name,
        quantity: Number(formData.quantity),
      })
      setEquipment(prev => [...prev, newItem])
      setShowForm(false)
      setFormData({ name: '', quantity: 1 })
    } catch (err) {
      alert('Ошибка создания: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Удалить оборудование?')) return
    try {
      await equipmentApi.delete(id)
      setEquipment(prev => prev.filter(e => e.id !== id))
    } catch (err) {
      alert('Ошибка удаления: ' + err.message)
    }
  }

  const handleUpdateQuantity = async (id) => {
    try {
      const updated = await equipmentApi.updateQuantity(id, Number(editQty))
      setEquipment(prev => prev.map(e => e.id === id ? { ...e, quantity: updated.quantity } : e))
      setEditingId(null)
    } catch (err) {
      alert('Ошибка обновления: ' + err.message)
    }
  }

  return (
    <div className="equipment-page" id="page-equipment">
      <Header title="Оборудование" />

      <div className="page-toolbar">
        <button className="btn-create" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Отмена' : '+ Новое оборудование'}
        </button>
        <span className="page-count">
          Всего: {equipment.length} · Единиц: {equipment.reduce((s, e) => s + e.quantity, 0)}
        </span>
      </div>

      {showForm && (
        <form className="entity-form" onSubmit={handleCreate}>
          <div className="form-row">
            <label>
              Название оборудования:
              <input type="text" value={formData.name} placeholder="Печь конвекционная"
                onChange={e => setFormData({ ...formData, name: e.target.value })}
                required minLength={2} maxLength={100} />
            </label>
            <label>
              Количество единиц:
              <input type="number" value={formData.quantity} min={0}
                onChange={e => setFormData({ ...formData, quantity: e.target.value })} required />
            </label>
          </div>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'Создание...' : 'Добавить оборудование'}
          </button>
        </form>
      )}

      {error && (
        <div className="error-banner">⚠️ {error}
          <button onClick={loadData} className="error-retry">Повторить</button>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner">Загрузка оборудования...</div>
      ) : (
        <div className="entity-list">
          {equipment.map((eq, idx) => (
            <div className="entity-card" key={eq.id}
              style={{ animationDelay: `${idx * 80 + 200}ms` }}>
              <div className="entity-card-main">
                <div className="entity-card-info">
                  <span className="entity-card-name">{eq.name}</span>
                  <div className="entity-card-meta">
                    <span className="entity-card-id">ID: {eq.id}</span>
                  </div>
                </div>
                <div className="entity-card-actions">
                  {editingId === eq.id ? (
                    <>
                      <input
                        type="number"
                        value={editQty}
                        min={0}
                        onChange={e => setEditQty(e.target.value)}
                        style={{ width: 60, padding: '4px 8px', borderRadius: 6, border: '2px solid var(--color-primary)', fontFamily: 'var(--font-family)', fontWeight: 700 }}
                      />
                      <button className="btn-next-status" onClick={() => handleUpdateQuantity(eq.id)}>✓</button>
                      <button className="btn-delete-sm" onClick={() => setEditingId(null)}>✕</button>
                    </>
                  ) : (
                    <>
                      <span className="quantity-badge"
                        onClick={() => { setEditingId(eq.id); setEditQty(eq.quantity) }}
                        style={{ cursor: 'pointer' }}
                        title="Нажмите, чтобы изменить количество"
                      >
                        {eq.quantity} ед.
                      </span>
                      <button className="btn-delete-sm" onClick={() => handleDelete(eq.id)}>✕</button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
          {equipment.length === 0 && <div className="entity-empty">Нет оборудования</div>}
        </div>
      )}
    </div>
  )
}

export default EquipmentPage
