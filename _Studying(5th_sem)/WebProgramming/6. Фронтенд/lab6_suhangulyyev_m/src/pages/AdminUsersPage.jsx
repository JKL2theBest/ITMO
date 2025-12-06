import { useEffect, useState } from 'react';
import { usersApi } from '../api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import styles from './AdminUsers.module.css';
import commonStyles from '../styles/Common.module.css';

export default function AdminUsersPage() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user && user.role !== 'admin') {
            navigate('/');
            return;
        }
        fetchUsers();
    }, [user]);

    const fetchUsers = async () => {
        try {
            const res = await usersApi.getAll();
            setUsers(res.data);
        } catch (error) {
            console.error("Fetch users error:", error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm('Вы уверены? Это удалит пользователя и все его данные.')) {
            try {
                await usersApi.delete(id);
                setUsers(users.filter(u => u.id !== id));
            } catch (error) {
                alert('Ошибка при удалении');
            }
        }
    };

    const getRoleClass = (role) => {
        if (role === 'admin') return styles.roleAdmin;
        if (role === 'verified_author') return styles.roleAuthor;
        return styles.roleUser;
    };

    if (loading) return <div className={commonStyles.loading}>Загрузка...</div>;

    return (
        <div className={commonStyles.container}>
            <h1 className={styles.header}>Управление пользователями</h1>
            <div className={commonStyles.card} style={{ padding: '0', overflow: 'hidden' }}>
                <table className={styles.table}>
                    <thead>
                        <tr>
                            <th className={styles.th}>Имя</th>
                            <th className={styles.th}>Email</th>
                            <th className={styles.th}>Роль</th>
                            <th className={styles.th}>Дата регистрации</th>
                            <th className={styles.th}>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(u => (
                            <tr key={u.id} className={styles.tr}>
                                <td className={styles.td}>
                                    <div className={styles.userCell}>
                                        {/* БЕЗОПАСНЫЙ АВАТАР */}
                                        {u.avatar_url ? (
                                            <img 
                                                src={u.avatar_url} 
                                                alt={u.name} 
                                                className={styles.avatarSmall} 
                                                onError={(e) => { e.target.style.display = 'none' }}
                                            />
                                        ) : (
                                            <div className={styles.avatarPlaceholder}>
                                                {u.name[0]?.toUpperCase()}
                                            </div>
                                        )}
                                        {u.name}
                                    </div>
                                </td>
                                <td className={styles.td}>{u.email}</td>
                                <td className={styles.td}>
                                    <span className={`${styles.roleBadge} ${getRoleClass(u.role)}`}>
                                        {u.role}
                                    </span>
                                </td>
                                <td className={`${styles.td} ${styles.dateCell}`}>
                                    {new Date(u.registered_at).toLocaleDateString()}
                                </td>
                                <td className={styles.td}>
                                    {u.id !== user.id && (
                                        <button 
                                            onClick={() => handleDelete(u.id)}
                                            className={`${commonStyles.buttonDanger} ${styles.actionBtn}`}
                                        >
                                            Удалить
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
