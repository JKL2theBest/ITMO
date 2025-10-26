import axios from 'axios';

// Создаем экземпляр axios с базовыми настройками
const apiClient = axios.create({
  baseURL: '/api/v1',
});

// Функция для установки токена в заголовки
export const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};

// Функции для каждого эндпоинта
export const registerUser = (login, password) => {
  return apiClient.post('/auth/register', { login, password });
};

export const loginUser = (login, password) => {
  return apiClient.post('/auth/login', { login, password });
};

// Проверяем и устанавливаем токен при первой загрузке
const token = localStorage.getItem('accessToken');
setAuthToken(token);

export default apiClient;