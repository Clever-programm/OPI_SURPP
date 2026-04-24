import { useState, useEffect } from 'react'
import Header from '../components/Header.jsx'
import { recipesApi, ingredientsApi } from '../api/client.js'
import './RecipesPage.css'

function RecipesPage() {
  const [recipes, setRecipes] = useState([])
  const [ingredients, setIngredients] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ name: '' })
  const [submitting, setSubmitting] = useState(false)
  const [expandedId, setExpandedId] = useState(null)
  const [details, setDetails] = useState({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [recipesData, ingredientsData] = await Promise.all([
        recipesApi.getAll({ limit: 100 }),
        ingredientsApi.getAll({ limit: 100 }),
      ])
      setRecipes(recipesData.items || [])
      setIngredients(ingredientsData.items || [])
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
                    {details[recipe.id].ingredients?.length > 0 ? (
                      <ul className="details-list">
                        {details[recipe.id].ingredients.map(ing => {
                          const ingInfo = ingredients.find(i => i.id === ing.ingredient_id)
                          return (
                            <li key={ing.id}>
                              {ingInfo?.name || `Ингредиент #${ing.ingredient_id}`}: <strong>{ing.quantity}</strong> {ingInfo?.unit || ''}
                            </li>
                          )
                        })}
                      </ul>
                    ) : <p className="details-empty">Нет ингредиентов</p>}
                  </div>
                  <div className="details-section">
                    <h4>Операции ({details[recipe.id].operations?.length || 0})</h4>
                    {details[recipe.id].operations?.length > 0 ? (
                      <ul className="details-list">
                        {details[recipe.id].operations
                          .sort((a, b) => a.sequence_order - b.sequence_order)
                          .map(op => (
                            <li key={op.id}>
                              <strong>{op.sequence_order}.</strong> {op.name} — {op.duration_minutes} мин.
                            </li>
                          ))}
                      </ul>
                    ) : <p className="details-empty">Нет операций</p>}
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
