/**
 * Базовый HTTP-клиент для взаимодействия с FastAPI бэкендом СУРПП.
 * Все запросы проксируются через /api/v1.
 */

const API_BASE = '/api/v1';

/**
 * Обёртка над fetch с обработкой ошибок и JSON-парсингом.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  // Удаляем Content-Type для DELETE запросов без тела
  if (config.method === 'DELETE' && !config.body) {
    delete config.headers['Content-Type'];
  }

  const response = await fetch(url, config);

  // 204 No Content — успешное удаление
  if (response.status === 204) {
    return null;
  }

  // Ошибки сервера
  if (!response.ok) {
    let errorData;
    let message = 'Произошла ошибка';
    try {
      errorData = await response.json();
      if (typeof errorData.detail === 'string') {
        message = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        // Форматируем ошибки валидации FastAPI
        message = errorData.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join('\n');
      }
    } catch {
      errorData = { detail: response.statusText };
      message = response.statusText || message;
    }
    const error = new Error(message);
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  return response.json();
}

// === Ингредиенты ===
export const ingredientsApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/ingredients/?${query}`);
  },
  getById: (id) => request(`/ingredients/${id}`),
  create: (data) => request('/ingredients/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/ingredients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`/ingredients/${id}`, { method: 'DELETE' }),
};

// === Оборудование ===
export const equipmentApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/equipment/?${query}`);
  },
  getById: (id) => request(`/equipment/${id}`),
  create: (data) => request('/equipment/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/equipment/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  updateQuantity: (id, quantity) =>
    request(`/equipment/${id}/quantity`, { method: 'PATCH', body: JSON.stringify({ quantity }) }),
  delete: (id) => request(`/equipment/${id}`, { method: 'DELETE' }),
};

// === Сотрудники ===
export const employeesApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/employees/?${query}`);
  },
  getAvailable: () => request('/employees/available'),
  getById: (id) => request(`/employees/${id}`),
  create: (data) => request('/employees/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/employees/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`/employees/${id}`, { method: 'DELETE' }),
  updateActive: (id, active) =>
    request(`/employees/${id}/active`, { method: 'PATCH', body: JSON.stringify({ active }) }),
  getCompetences: (id) => request(`/employees/${id}/competences`),
  addCompetence: (id, data) =>
    request(`/employees/${id}/competences`, { method: 'POST', body: JSON.stringify(data) }),
  removeCompetence: (employeeId, competenceId) =>
    request(`/employees/${employeeId}/competences/${competenceId}`, { method: 'DELETE' }),
};

// === Компетенции ===
export const competencesApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/competences/?${query}`);
  },
  create: (data) => request('/competences/', { method: 'POST', body: JSON.stringify(data) }),
  delete: (id) => request(`/competences/${id}`, { method: 'DELETE' }),
};

// === Рецептуры ===
export const recipesApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/recipes/?${query}`);
  },
  getById: (id) => request(`/recipes/${id}`),
  create: (data) => request('/recipes/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/recipes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`/recipes/${id}`, { method: 'DELETE' }),
  // Ингредиенты рецепта
  getIngredients: (id) => request(`/recipes/${id}/ingredients`),
  addIngredient: (id, data) =>
    request(`/recipes/${id}/ingredients`, { method: 'POST', body: JSON.stringify(data) }),
  removeIngredient: (recipeId, linkId) =>
    request(`/recipes/${recipeId}/ingredients/${linkId}`, { method: 'DELETE' }),
  // Операции рецепта
  getOperations: (id) => request(`/recipes/${id}/operations`),
  addOperation: (id, data) =>
    request(`/recipes/${id}/operations`, { method: 'POST', body: JSON.stringify(data) }),
  removeOperation: (recipeId, opId) =>
    request(`/recipes/${recipeId}/operations/${opId}`, { method: 'DELETE' }),
};

// === Заказы ===
export const ordersApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/orders/?${query}`);
  },
  getById: (id) => request(`/orders/${id}`),
  create: (data) => request('/orders/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/orders/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  updateStatus: (id, status) =>
    request(`/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  delete: (id) => request(`/orders/${id}`, { method: 'DELETE' }),
  // Позиции заказа
  getItems: (id) => request(`/orders/${id}/items`),
  addItem: (id, data) =>
    request(`/orders/${id}/items`, { method: 'POST', body: JSON.stringify(data) }),
  removeItem: (orderId, itemId) =>
    request(`/orders/${orderId}/items/${itemId}`, { method: 'DELETE' }),
};

// === Склад ===
export const stockApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/stock/?${query}`);
  },
  getByIngredient: (ingredientId) => request(`/stock/${ingredientId}`),
  getTotalQuantity: (ingredientId) => request(`/stock/${ingredientId}/total`),
  receive: (data) => request('/stock/receive', { method: 'POST', body: JSON.stringify(data) }),
  writeOff: (data) => request('/stock/write-off', { method: 'POST', body: JSON.stringify(data) }),
  checkAvailability: (data) =>
    request('/stock/check-availability', { method: 'POST', body: JSON.stringify(data) }),
  calculateRequirement: (recipeId, quantity) =>
    request(`/stock/calculate-requirement?recipe_id=${recipeId}&quantity=${quantity}`, { method: 'POST' }),
  getExpiringSoon: (days = 7) => request(`/stock/expiring-soon?days=${days}`),
};

// === Расписание ===
export const scheduleApi = {
  getAll: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/schedule/?${query}`);
  },
  getById: (id) => request(`/schedule/${id}`),
  getCalendar: (startDate, endDate, resourceType = 'equipment') =>
    request(`/schedule/calendar?start_date=${startDate}&end_date=${endDate}&resource_type=${resourceType}`),
  getByOrder: (orderId) => request(`/schedule/order/${orderId}`),
  getByEquipment: (equipmentId, startDate, endDate) =>
    request(`/schedule/equipment/${equipmentId}?start_date=${startDate}&end_date=${endDate}`),
  getByEmployee: (employeeId, startDate, endDate) =>
    request(`/schedule/employee/${employeeId}?start_date=${startDate}&end_date=${endDate}`),
  generate: (data) =>
    request('/schedule/generate', { method: 'POST', body: JSON.stringify(data) }),
  create: (data) => request('/schedule/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id, data) => request(`/schedule/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id) => request(`/schedule/${id}`, { method: 'DELETE' }),
  checkConflicts: (startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    return request(`/schedule/conflicts?${params.toString()}`);
  },
};
