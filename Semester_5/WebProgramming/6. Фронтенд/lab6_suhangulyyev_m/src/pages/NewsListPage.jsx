import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { newsApi } from '../api';
import { useAuth } from '../context/AuthContext';
import styles from './NewsList.module.css';
import commonStyles from '../styles/Common.module.css';

export default function NewsListPage() {
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    
    const { loading: authLoading } = useAuth();

    useEffect(() => {
        if (authLoading) return;

        const fetchNews = async () => {
            try {
                setLoading(true);
                const response = await newsApi.getAll();
                setNews(response.data);
                setError(null);
            } catch (err) {
                console.error("News fetch error:", err);
                if (err.response && err.response.status === 401) {
                    setError('unauthorized');
                } else {
                    setError('failed');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchNews();
    }, [authLoading]);

    if (loading || authLoading) {
        return <div className={commonStyles.loading}>Загрузка ленты...</div>;
    }

    if (error === 'unauthorized') {
        return (
            <div className={commonStyles.container}>
                <div className={commonStyles.card} style={{textAlign: 'center', padding: '4rem 2rem'}}>
                    <h2 className={commonStyles.title}>Требуется авторизация</h2>
                    <p style={{color: 'var(--win-text-sec)', marginBottom: '2rem', fontSize: '1.1rem'}}>
                        Сервер ограничил доступ к новостям для гостей.
                        <br />Пожалуйста, войдите в свой аккаунт.
                    </p>
                    <div style={{display: 'flex', justifyContent: 'center', gap: '1rem'}}>
                        <button 
                            className={commonStyles.button} 
                            style={{maxWidth: '150px'}}
                            onClick={() => navigate('/login')}
                        >
                            Войти
                        </button>
                        <button 
                            className={commonStyles.buttonSecondary} 
                            style={{maxWidth: '150px'}}
                            onClick={() => navigate('/register')}
                        >
                            Регистрация
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    if (error === 'failed') {
        return (
            <div className={commonStyles.container}>
                <div className={commonStyles.error}>
                    Не удалось загрузить новости. Проверьте соединение с сервером.
                </div>
            </div>
        );
    }

    return (
        <div>
            <h1 style={{marginBottom: '1.5rem', fontSize: '2rem', fontWeight: '600', color: 'var(--win-text-main)'}}>
                Последние новости
            </h1>
            
            {news.length === 0 ? (
                <div className={commonStyles.card} style={{textAlign: 'center', color: 'var(--win-text-sec)'}}>
                    Список новостей пуст.
                </div>
            ) : (
                <div className={styles.grid}>
                    {news.map(item => (
                        <article key={item.id} className={styles.newsCard}>
                            <h3 className={styles.newsTitle}>
                                <Link to={`/news/${item.id}`}>{item.title}</Link>
                            </h3>
                            <div className={styles.newsMeta}>
                                <span style={{fontWeight: '600', color: 'var(--win-text-main)'}}>
                                    {item.author.name}
                                </span> 
                                <span style={{margin: '0 8px'}}>•</span>
                                <span>{new Date(item.published_at).toLocaleDateString()}</span>
                            </div>
                        </article>
                    ))}
                </div>
            )}
        </div>
    );
}
