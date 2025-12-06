import { useState, useEffect } from 'react';
import { usersApi } from '../api';
import { useAuth } from '../context/AuthContext';
import styles from './Profile.module.css';
import commonStyles from '../styles/Common.module.css';

export default function ProfilePage() {
    const { user } = useAuth();
    const [name, setName] = useState('');
    const [avatarUrl, setAvatarUrl] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        if (user) {
            setName(user.name);
            setAvatarUrl(user.avatar_url || '');
        }
    }, [user]);

    const handleUpdate = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');
        try {
            await usersApi.update(user.id, {
                name,
                avatar_url: avatarUrl.trim() || null
            });
            setMessage('Профиль успешно обновлен!');
        } catch (err) {
            console.error("Update failed:", err.message);
            setError('Не удалось обновить профиль');
        }
    };

    if (!user) return <div className={commonStyles.loading}>Загрузка...</div>;

    return (
        <div className={commonStyles.container}>
            <div className={commonStyles.card} style={{maxWidth: '500px', margin: '2rem auto'}}>
                <h2 className={commonStyles.title}>Мой профиль</h2>
                
                {message && <div className={styles.successMessage}>{message}</div>}
                {error && <div className={commonStyles.error}>{error}</div>}

                <div className={styles.header}>
                    {/* БЕЗОПАСНОЕ ОТОБРАЖЕНИЕ АВАТАРА */}
                    <div className={styles.avatarContainer}>
                        {avatarUrl ? (
                            <img 
                                src={avatarUrl} 
                                alt={name} 
                                className={styles.avatarImg}
                                onError={(e) => { e.target.style.display = 'none'; }}
                            />
                        ) : (
                            <div className={styles.avatarPlaceholder}>{name[0]?.toUpperCase()}</div>
                        )}
                    </div>
                    
                    <div className={styles.email}>{user.email}</div>
                    <div className={styles.roleBadge}>{user.role}</div>
                </div>

                <form onSubmit={handleUpdate} className={commonStyles.formGroup}>
                    <div>
                        <label className={styles.label}>Имя</label>
                        <input 
                            className={commonStyles.input} 
                            value={name} 
                            onChange={e => setName(e.target.value)} 
                            maxLength={50}
                            required
                        />
                    </div>
                    <div>
                        <label className={styles.label}>URL Аватара</label>
                        <input 
                            className={commonStyles.input} 
                            value={avatarUrl} 
                            onChange={e => setAvatarUrl(e.target.value)} 
                            placeholder="https://example.com/avatar.jpg"
                            type="url"
                        />
                    </div>
                    <button type="submit" className={commonStyles.button}>Сохранить изменения</button>
                </form>
            </div>
        </div>
    );
}
