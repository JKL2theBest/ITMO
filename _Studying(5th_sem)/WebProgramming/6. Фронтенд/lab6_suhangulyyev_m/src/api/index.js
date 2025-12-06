import axios from 'axios';

export const axiosInstance = axios.create({
    baseURL: 'http://127.0.0.1:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// --- Перехватчики (Interceptors) ---

axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Не перехватываем 401 при попытке входа
        if (originalRequest.url.includes('/auth/login')) {
            return Promise.reject(error);
        }

        // Если ошибка 401 и это не повторная попытка
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            const refreshToken = localStorage.getItem('refresh_token');

            // Если рефреш токена нет, значит мы просто Гость
            if (!refreshToken) {
                return Promise.reject(error);
            }
            
            try {
                const response = await axios.post('http://127.0.0.1:8000/api/v1/auth/refresh', {
                    refresh_token: refreshToken
                });

                const { access_token, refresh_token: newRefreshToken } = response.data;

                localStorage.setItem('access_token', access_token);
                if (newRefreshToken) {
                    localStorage.setItem('refresh_token', newRefreshToken);
                }

                axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                originalRequest.headers['Authorization'] = `Bearer ${access_token}`;

                return axiosInstance(originalRequest);
            } catch (refreshError) {
                console.error("Refresh token failed:", refreshError.message);
            }

            // Если не удалось обновить - логаут
            console.warn("Session expired. Logging out...");
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
        }
        
        return Promise.reject(error);
    }
);

// --- API Методы ---

export const authApi = {
    login: (username, password) => {
        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);
        return axiosInstance.post('/auth/login', params, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
    },
    refreshToken: (token) => axios.post('http://127.0.0.1:8000/api/v1/auth/refresh', { refresh_token: token }),
    register: (userData) => axiosInstance.post('/auth/register', userData),
    getMe: (userId) => axiosInstance.get(`/users/${userId}`),
};

export const newsApi = {
    getAll: () => axiosInstance.get('/news/'),
    getOne: (id) => axiosInstance.get(`/news/${id}`),
    create: (data) => axiosInstance.post('/news/', data),
    update: (id, data) => axiosInstance.patch(`/news/${id}`, data),
    delete: (id) => axiosInstance.delete(`/news/${id}`),
};

export const commentsApi = {
    getAll: (limit = 1000) => axiosInstance.get(`/comments/?limit=${limit}`),
    create: (data) => axiosInstance.post('/comments/', data),
    update: (id, data) => axiosInstance.patch(`/comments/${id}`, data),
    delete: (id) => axiosInstance.delete(`/comments/${id}`),
};

export const usersApi = {
    getAll: () => axiosInstance.get('/users/'),
    getOne: (id) => axiosInstance.get(`/users/${id}`),
    update: (id, data) => axiosInstance.patch(`/users/${id}`, data),
    delete: (id) => axiosInstance.delete(`/users/${id}`),
};
