import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import commonStyles from '../styles/Common.module.css';

export default function ProtectedRoute({ roles = [] }) {
    const { user, loading } = useAuth();

    if (loading) {
        return <div className={commonStyles.loading}>Проверка прав...</div>;
    }

    // 1. Если не авторизован — на логин
    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // 2. Если нужны конкретные роли, а у юзера их нет — на главную (или 403)
    if (roles.length > 0 && !roles.includes(user.role)) {
        alert("У вас недостаточно прав для доступа к этой странице.");
        return <Navigate to="/" replace />;
    }

    // 3. Все ок — рендерим контент
    return <Outlet />;
}
