import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { recipesApi, ingredientsApi, equipmentApi, competencesApi } from '../api/client.js'
import './RecipesPage.css'

function RecipesPage() {
  const [recipes, setRecipes] = useState([])
  const [ingredients, setIngredients] = useState([])
  const [equipment, setEquipment] = useState([])
  const [competences, setCompetences] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ name: '' })
  const [submitting, setSubmitting] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [details, setDetails] = useState({})
  
  // Состояние для форм внутри рецепта
  const [newIng, setNewIng] = useState({ ingredient_id: '', quantity: '' })
  const [newOp, setNewOp] = useState({ name: '', duration_minutes: '', equipment_id: '', competence_id: '', sequence_number: '' })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [recipesData, ingredientsData, equipmentData, competencesData] = await Promise.all([
        recipesApi.getAll({ limit: 100 }),
        ingredientsApi.getAll({ limit: 100 }),
        equipmentApi.getAll({ limit: 100 }),
        competencesApi.getAll({ limit: 100 }),
      ])
      setRecipes(recipesData.items || [])
      setIngredients(ingredientsData.items || [])
      setEquipment(equipmentData.items || [])
      setCompetences(competencesData.items || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadDetails = async (id) => {
    if (details[id]) return
    try {
      const data = await recipesApi.getById(id)
      setDetails(prev => ({ ...prev, [id]: data }))
    } catch (err) {
      alert('Ошибка загрузки деталей: ' + err.message)
    }
  }

  const toggleExpand = (id) => {
    if (expandedId === id) {
      setExpandedId(null)
    } else {
      setExpandedId(id)
      loadDetails(id)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const newRecipe = await recipesApi.create({ name: formData.name })
      setRecipes(prev => [...prev, newRecipe])
      setShowForm(false)
      setFormData({ name: '' })
    } catch (err) {
      alert('Ошибка создания: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Удалить рецептуру?')) return
    try {
      await recipesApi.delete(id)
      setRecipes(prev => prev.filter(r => r.id !== id))
      if (expandedId === id) setExpandedId(null)
    } catch (err) {
      alert('Ошибка удаления: ' + err.message)
    }
  }

  const handleAddIngredient = async (recipeId) => {
    if (!newIng.ingredient_id || !newIng.quantity) return
    try {
      await recipesApi.addIngredient(recipeId, {
        ingredient_id: Number(newIng.ingredient_id),
        quantity: Number(newIng.quantity)
      })
      setNewIng({ ingredient_id: '', quantity: '' })
      // Перезагружаем детали
      const data = await recipesApi.getById(recipeId)
      setDetails(prev => ({ ...prev, [recipeId]: data }))
    } catch (err) {
      alert('Ошибка добавления ингредиента: ' + err.message)
    }
  }

  const handleRemoveIngredient = async (recipeId, linkId) => {
    try {
      await recipesApi.removeIngredient(recipeId, linkId)
      const data = await recipesApi.getById(recipeId)
      setDetails(prev => ({ ...prev, [recipeId]: data }))
    } catch (err) {
      alert('Ошибка удаления: ' + err.message)
    }
  }

  const handleAddOperation = async (recipeId) => {
    if (!newOp.name || !newOp.duration_minutes || !newOp.sequence_number) return
    try {
      await recipesApi.addOperation(recipeId, {
        name: newOp.name,
        duration_minutes: Number(newOp.duration_minutes),
        sequence_number: Number(newOp.sequence_number),
        equipment_id: newOp.equipment_id ? Number(newOp.equipment_id) : null,
        competence_id: newOp.competence_id ? Number(newOp.competence_id) : null,
      })
      setNewOp({ name: '', duration_minutes: '', equipment_id: '', competence_id: '', sequence_number: '' })
      const data = await recipesApi.getById(recipeId)
      setDetails(prev => ({ ...prev, [recipeId]: data }))
    } catch (err) {
      alert('Ошибка добавления операции: ' + err.message)
    }
  }

  const handleRemoveOperation = async (recipeId, opId) => {
    try {
      await recipesApi.removeOperation(recipeId, opId)
      const data = await recipesApi.getById(recipeId)
      setDetails(prev => ({ ...prev, [recipeId]: data }))
    } catch (err) {
      alert('Ошибка удаления операции: ' + err.message)
    }
  }

  return (
    <div className="recipes-page" id="page-recipes">
      <Header title="Рецептуры" />

      <div className="page-toolbar">
        <button className="btn-create" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Отмена' : '+ Новая рецептура'}
        </button>
        <span className="page-count">Всего: {recipes.length}</span>
      </div>

      {showForm && (
        <form className="entity-form" onSubmit={handleCreate}>
          <div className="form-row">
            <label>
              Название изделия:
              <input type="text" value={formData.name} placeholder="Например: Торт Наполеон"
                onChange={e => setFormData({ name: e.target.value })} required minLength={2} maxLength={100} />
            </label>
          </div>
          <button type="submit" className="btn-submit" disabled={submitting}>
            {submitting ? 'Создание...' : 'Создать рецептуру'}
          </button>
        </form>
      )}

      {error && <div className="error-banner">⚠️ {error}<button onClick={loadData} className="error-retry">Повторить</button></div>}

      {loading ? (
        <div className="loading-spinner">Загрузка рецептур...</div>
      ) : (
        <div className="entity-list">
          {recipes.map((recipe, idx) => (
            <div className="entity-card" key={recipe.id}
              style={{ animationDelay: `${idx * 80 + 200}ms` }}>
              <div className="entity-card-main" onClick={() => toggleExpand(recipe.id)}>
                <div className="entity-card-info">
                  <span className="entity-card-name">{recipe.name}</span>
                  <span className="entity-card-id">ID: {recipe.id}</span>
                </div>
                <div className="entity-card-actions">
                  <button className="btn-expand">{expandedId === recipe.id ? '▲' : '▼'}</button>
                  <button className="btn-delete-sm" onClick={(e) => { e.stopPropagation(); handleDelete(recipe.id) }}>✕</button>
                </div>
              </div>

              {expandedId === recipe.id && details[recipe.id] && (
                <div className="entity-details">
                  <div className="details-section">
                    <h4>Ингредиенты ({details[recipe.id].ingredients?.length || 0})</h4>
                    <ul className="details-list">
                      {details[recipe.id].ingredients?.map(ing => {
                        const ingInfo = ingredients.find(i => i.id === ing.ingredient_id)
                        return (
                          <li key={ing.id} className="detail-item-row">
                            <span>{ingInfo?.name || `Ингредиент #${ing.ingredient_id}`}: <strong>{ing.quantity}</strong> {ingInfo?.unit || ''}</span>
                            <button className="btn-delete-tiny" onClick={() => handleRemoveIngredient(recipe.id, ing.id)}>✕</button>
                          </li>
                        )
                      })}
                      <li className="detail-add-form">
                        <select value={newIng.ingredient_id} onChange={e => setNewIng({ ...newIng, ingredient_id: e.target.value })}>
                          <option value="">— Выберите ингредиент —</option>
                          {ingredients.map(i => <option key={i.id} value={i.id}>{i.name} ({i.unit})</option>)}
                        </select>
                        <input type="number" placeholder="Кол-во" value={newIng.quantity} onChange={e => setNewIng({ ...newIng, quantity: e.target.value })} style={{ width: 80 }} />
                        <button className="btn-add-tiny" onClick={() => handleAddIngredient(recipe.id)}>+</button>
                      </li>
                    </ul>
                  </div>

                  <div className="details-section">
                    <h4>Операции ({details[recipe.id].operations?.length || 0})</h4>
                    <ul className="details-list">
                      {details[recipe.id].operations
                        ?.sort((a, b) => a.sequence_number - b.sequence_number)
                        .map(op => (
                          <li key={op.id} className="detail-item-row">
                            <span><strong>{op.sequence_number}.</strong> {op.name} — {op.duration_minutes} мин.</span>
                            <button className="btn-delete-tiny" onClick={() => handleRemoveOperation(recipe.id, op.id)}>✕</button>
                          </li>
                        ))}
                      <li className="detail-add-form-vertical">
                        <div className="form-mini-row">
                          <input type="number" placeholder="№" value={newOp.sequence_number} onChange={e => setNewOp({ ...newOp, sequence_number: e.target.value })} style={{ width: 40 }} title="Порядковый номер" />
                          <input type="text" placeholder="Название операции" value={newOp.name} onChange={e => setNewOp({ ...newOp, name: e.target.value })} style={{ flex: 1 }} />
                          <input type="number" placeholder="Мин" value={newOp.duration_minutes} onChange={e => setNewOp({ ...newOp, duration_minutes: e.target.value })} style={{ width: 60 }} title="Длительность в минутах" />
                        </div>
                        <div className="form-mini-row">
                          <select value={newOp.equipment_id} onChange={e => setNewOp({ ...newOp, equipment_id: e.target.value })} style={{ flex: 1 }}>
                            <option value="">— Оборудование (опц.) —</option>
                            {equipment.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                          </select>
                          <select value={newOp.competence_id} onChange={e => setNewOp({ ...newOp, competence_id: e.target.value })} style={{ flex: 1 }}>
                            <option value="">— Компетенция (опц.) —</option>
                            {competences.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                          </select>
                          <button className="btn-add-tiny" onClick={() => handleAddOperation(recipe.id)} style={{ padding: '0 15px' }}>Добавить</button>
                        </div>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ))}
          {recipes.length === 0 && <div className="entity-empty">Нет рецептур</div>}
        </div>
      )}
    </div>
  )
}

export default RecipesPage
