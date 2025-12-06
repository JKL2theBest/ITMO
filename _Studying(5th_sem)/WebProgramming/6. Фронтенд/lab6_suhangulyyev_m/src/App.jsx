import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

import NewsListPage from './pages/NewsListPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import NewsDetailPage from './pages/NewsDetailPage';
import NewsCreatePage from './pages/NewsCreatePage';
import ProfilePage from './pages/ProfilePage';
import AdminUsersPage from './pages/AdminUsersPage';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          {/* Публичные маршруты */}
          <Route index element={<NewsListPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
          <Route path="news/:id" element={<NewsDetailPage />} />

          {/* Защищенные маршруты (Нужна любая авторизация) */}
          <Route element={<ProtectedRoute />}>
             <Route path="profile" element={<ProfilePage />} />
          </Route>

          {/* Защищенные маршруты (Только для Авторов и Админов) */}
          <Route element={<ProtectedRoute roles={['verified_author', 'admin']} />}>
             <Route path="create" element={<NewsCreatePage />} />
          </Route>

          {/* Защищенные маршруты (Только для Админов) */}
          <Route element={<ProtectedRoute roles={['admin']} />}>
             <Route path="admin/users" element={<AdminUsersPage />} />
          </Route>

        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
