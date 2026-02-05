import { useState, useEffect } from 'react';
import { registerUser, loginUser, setAuthToken } from './api';
import SnakeGame from './components/SnakeGame';
import './index.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('accessToken'));
  const [currentPage, setCurrentPage] = useState('main');
  const [formData, setFormData] = useState({ login: '', password: '' });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState(null); // { type: 'success' | 'error', message: string }

  // Эффект для обработки успешных действий (замена setTimeout)
  useEffect(() => {
    if (status?.type !== 'success') return;

    let timeoutId;
    if (currentPage === 'register') {
      timeoutId = setTimeout(() => {
        setCurrentPage('login');
        setStatus(null);
        setFormData({ login: '', password: '' }); // Сбрасываем форму
      }, 2000);
    } else if (currentPage === 'login') {
      timeoutId = setTimeout(() => {
        setCurrentPage('main');
        setStatus(null);
        setFormData({ login: '', password: '' });
      }, 1500);
    }

    // Функция очистки для предотвращения ошибок
    return () => clearTimeout(timeoutId);
  }, [status, currentPage]);


  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    setAuthToken(null);
    setIsAuthenticated(false);
    setCurrentPage('main');
  };

  const validate = (name, value) => {
    switch (name) {
      case 'login':
        if (value.length < 3) return 'Логин должен содержать минимум 3 символа';
        if (value.length > 32) return 'Логин должен содержать максимум 32 символа';
        if (!/^[a-zA-Z0-9_.-]+$/.test(value)) {
          return 'Логин может содержать только латиницу, цифры и символы: . _ -';
        }
        return '';
      case 'password':
        if (value.length < 8) return 'Пароль должен содержать минимум 8 символов';
        if (!/[A-Z]/.test(value)) return 'Пароль должен содержать минимум одну заглавную букву';
        if (!/[a-z]/.test(value)) return 'Пароль должен содержать минимум одну строчную букву';
        if (!/\d/.test(value)) return 'Пароль должен содержать минимум одну цифру';
        if (!/[!@#$%^&*(),.?:{}|<>]/.test(value)) {
          return 'Пароль должен содержать минимум один специальный символ';
        }
        return '';
      default:
        return '';
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: validate(name, value) }));
  };

  const isFormValid = !errors.login && !errors.password && formData.login && formData.password;

  const handleApiCall = async (apiFunction, successMessage) => {
    if (!isFormValid || isLoading) return;
    
    setIsLoading(true);
    setStatus(null);

    try {
      const response = await apiFunction(formData.login, formData.password);
      setStatus({ type: 'success', message: successMessage });
      return response.data;
    } catch (error) {
      let errorMessage = 'Произошла неизвестная ошибка';
      if (error.response) {
        if (error.response.status === 409) errorMessage = 'Пользователь с таким логином уже существует';
        else if (error.response.status === 401) errorMessage = 'Неверный логин или пароль';
        else errorMessage = error.response.data.detail || errorMessage;
      }
      setStatus({ type: 'error', message: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRegisterSubmit = (e) => {
    e.preventDefault();
    handleApiCall(registerUser, 'Пользователь успешно создан!');
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    const data = await handleApiCall(loginUser, 'Успешный вход в систему!');
    if (data?.access_token) {
      localStorage.setItem('accessToken', data.access_token);
      setAuthToken(data.access_token);
      setIsAuthenticated(true);
      setIsLoading(false); // Разблокируем форму после успешного входа
    }
  };

  const renderForm = (isLogin = false) => (
    <div className="windows7-dialog">
      <div className="windows7-header">
        <div className="windows7-icon">{isLogin ? '🔐' : '👤'}</div>
        {isLogin ? 'Вход в систему' : 'Регистрация пользователя'}
      </div>
      <form className="windows7-form" onSubmit={isLogin ? handleLoginSubmit : handleRegisterSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="login">Логин:</label>
          <input
            type="text" id="login" name="login" className="windows7-input"
            value={formData.login} onChange={handleInputChange}
            placeholder={isLogin ? "Введите ваш логин" : "Введите логин (3-32 символа)"} 
            disabled={isLoading}
          />
          {errors.login && <div className="field-error">{errors.login}</div>}
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="password">Пароль:</label>
          <input
            type="password" id="password" name="password" className="windows7-input"
            value={formData.password} onChange={handleInputChange}
            placeholder={isLogin ? "Введите ваш пароль" : "Введите пароль (мин. 8 символов)"}
            disabled={isLoading}
          />
          {errors.password && <div className="field-error">{errors.password}</div>}
        </div>
        <div className="form-actions">
          <button type="button" className="windows7-button" onClick={() => setCurrentPage('main')}>
            ← Назад
          </button>
          <button type="submit" className={`windows7-button register-button`} disabled={!isFormValid || isLoading}>
            {isLoading && <span className="loading-spinner"></span>}
            {isLogin ? 'Войти' : 'Зарегистрироваться'}
          </button>
        </div>
        {status && (
          <div className={`status-message status-${status.type}`}>
            {status.message}
          </div>
        )}
      </form>
    </div>
  );

  const renderPageContent = () => {
    switch (currentPage) {
      case 'register':
        return <div className="app"><div className="windows-bg"></div>{renderForm(false)}</div>;
      case 'login':
        return <div className="app"><div className="windows-bg"></div>{renderForm(true)}</div>;
      case 'snake':
        return isAuthenticated ? <SnakeGame onExit={() => setCurrentPage('main')} /> : renderMainPage();
      default:
        return renderMainPage();
    }
  };

  const renderMainPage = () => (
    <div className="app">
      <div className="windows-bg"></div>
      {isAuthenticated ? (
        <div className="windows7-dialog dialog-main">
          <div className="windows7-header"><div className="windows7-icon">🎉</div>Авторизация успешна!</div>
          <div className="dialog-content">
            <h1 className="dialog-title">Вы успешно вошли в систему!</h1>
            <p className="dialog-text">Теперь вам доступен эксклюзивный контент.</p>
            <div className="video-container">
              <video className="prize-video" autoPlay loop muted playsInline>
                <source src="/Прикольчик.MP4" type="video/mp4" />
                Ваш браузер не поддерживает видео.
              </video>
            </div>
            <div>
              <button className="windows7-button button-prize" onClick={() => setCurrentPage('snake')}>
                🎮 Получить приз!
              </button>
              <button className="windows7-button button-margin-left" onClick={handleLogout}>
                Выйти
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="windows7-dialog dialog-main">
          <div className="windows7-header"><div className="windows7-icon">🚀</div>Система Регистрации</div>
          <div className="dialog-content">
            <h1 className="dialog-title">Добро пожаловать!</h1>
            <p className="dialog-text">Пожалуйста, войдите в систему или зарегистрируйтесь.</p>
            <div className="button-group">
              <button className="windows7-button register-button" onClick={() => setCurrentPage('register')}>
                Регистрация
              </button>
              <button className="windows7-button button-margin-left" onClick={() => setCurrentPage('login')}>
                Войти
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return <>{renderPageContent()}</>;
}

export default App;
