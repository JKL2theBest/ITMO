import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { newsApi, commentsApi } from '../api';
import { useAuth } from '../context/AuthContext';
import commonStyles from '../styles/Common.module.css'; 
import styles from './NewsDetail.module.css';

export default function NewsDetailPage() {
    const { id } = useParams();
    const { user } = useAuth();
    const navigate = useNavigate();
    
    const [newsItem, setNewsItem] = useState(null);
    const [comments, setComments] = useState([]);
    
    const [newComment, setNewComment] = useState('');
    const [loading, setLoading] = useState(true);
    
    const [isEditingNews, setIsEditingNews] = useState(false);
    const [editNewsTitle, setEditNewsTitle] = useState('');
    const [editNewsBody, setEditNewsBody] = useState('');

    const [editingCommentId, setEditingCommentId] = useState(null);
    const [editCommentText, setEditCommentText] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [newsRes, commentsRes] = await Promise.all([
                    newsApi.getOne(id),
                    commentsApi.getAll()
                ]);
                setNewsItem(newsRes.data);
                setEditNewsTitle(newsRes.data.title);
                const content = newsRes.data.content;
                setEditNewsBody(content.body || content.text || JSON.stringify(content));
                
                setComments(commentsRes.data.filter(c => c.news.id === id));
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    // --- НОВОСТИ ---
    const handleUpdateNews = async (e) => {
        e.preventDefault();
        try {
            const res = await newsApi.update(id, {
                title: editNewsTitle,
                content: { body: editNewsBody }
            });
            setNewsItem(res.data);
            setIsEditingNews(false);
        } catch (error) {
            alert("Ошибка при обновлении новости");
        }
    };

    const handleDeleteNews = async () => {
        if (window.confirm("Удалить новость безвозвратно?")) {
            try {
                await newsApi.delete(id);
                navigate('/');
            } catch (e) {
                alert("Ошибка при удалении");
            }
        }
    };

    // --- КОММЕНТАРИИ ---
    const handleCommentSubmit = async (e) => {
        e.preventDefault();
        try {
            const res = await commentsApi.create({ text: newComment, news_id: id });
            setComments([...comments, res.data]);
            setNewComment('');
        } catch (e) {
            alert("Ошибка");
        }
    };

    const startEditComment = (comment) => {
        setEditingCommentId(comment.id);
        setEditCommentText(comment.text);
    };

    const saveCommentEdit = async (commentId) => {
        try {
            const res = await commentsApi.update(commentId, { text: editCommentText });
            setComments(comments.map(c => c.id === commentId ? res.data : c));
            setEditingCommentId(null);
        } catch (e) {
            alert("Не удалось обновить комментарий");
        }
    };

    const handleDeleteComment = async (commentId) => {
        if (window.confirm("Удалить комментарий?")) {
            try {
                await commentsApi.delete(commentId);
                setComments(comments.filter(c => c.id !== commentId));
            } catch (e) {
                alert("Ошибка удаления");
            }
        }
    };

    const renderContent = (content) => {
        if (!content) return null;
        if (typeof content === 'string') return content;
        return content.body || content.text || JSON.stringify(content, null, 2);
    };

    if (loading) return <div className={commonStyles.loading}>Загрузка...</div>;
    if (!newsItem) return <div className={commonStyles.error}>Новость не найдена</div>;

    const canManageNews = user && (user.role === 'admin' || (user.role === 'verified_author' && user.id === newsItem.author.id));

    return (
        <div className={commonStyles.card} style={{marginTop: '2rem'}}>
            
            {/* РЕДАКТИРОВАНИЕ НОВОСТИ */}
            {isEditingNews ? (
                <form onSubmit={handleUpdateNews} className={commonStyles.formGroup}>
                    <h2 className={commonStyles.title}>Редактирование</h2>
                    <input 
                        className={commonStyles.input} 
                        value={editNewsTitle} 
                        onChange={e => setEditNewsTitle(e.target.value)} 
                        required 
                    />
                    <textarea 
                        className={`${commonStyles.input} ${styles.editNewsTextarea}`} 
                        value={editNewsBody} 
                        onChange={e => setEditNewsBody(e.target.value)} 
                        required 
                    />
                    <div className={styles.editActions}>
                        <button type="button" className={`${commonStyles.buttonSecondary} ${styles.btnAuto}`} onClick={() => setIsEditingNews(false)}>Отмена</button>
                        <button type="submit" className={`${commonStyles.button} ${styles.btnAuto}`}>Сохранить</button>
                    </div>
                </form>
            ) : (
                <article>
                    <h1 className={styles.articleTitle}>{newsItem.title}</h1>
                    <div className={styles.meta}>
                        <span className={styles.author}>{newsItem.author.name}</span>
                        <span>•</span>
                        <span>{new Date(newsItem.published_at).toLocaleString()}</span>
                    </div>
                    <div className={styles.content}>{renderContent(newsItem.content)}</div>
                    {canManageNews && (
                        <div className={styles.actions} style={{gap: '10px'}}>
                            <button className={`${commonStyles.buttonSecondary} ${styles.btnAuto}`} onClick={() => setIsEditingNews(true)}>Редактировать</button>
                            <button className={`${commonStyles.buttonDanger} ${styles.btnAuto}`} onClick={handleDeleteNews}>Удалить</button>
                        </div>
                    )}
                </article>
            )}

            {/* КОММЕНТАРИИ */}
            {!isEditingNews && (
                <section className={styles.commentsSection}>
                    <div className={styles.commentsHeader}>
                        <h3>Комментарии</h3>
                        <span className={styles.commentsCount}>{comments.length}</span>
                    </div>
                    
                    <div className={styles.commentsList}>
                        {comments.map(comment => (
                            <div key={comment.id} className={styles.commentItem}>
                                <div className={styles.commentHeader}>
                                    <span className={styles.commentAuthor}>{comment.author.name}</span>
                                    <span className={styles.commentDate}>{new Date(comment.created_at).toLocaleString()}</span>
                                </div>

                                {/* ЛОГИКА РЕДАКТИРОВАНИЯ КОММЕНТАРИЯ */}
                                {editingCommentId === comment.id ? (
                                    <div className={styles.editCommentWrapper}>
                                        <textarea 
                                            className={commonStyles.input} 
                                            value={editCommentText} 
                                            onChange={e => setEditCommentText(e.target.value)} 
                                            rows={2}
                                        />
                                        <div className={styles.editCommentActions}>
                                            <button className={`${commonStyles.button} ${styles.btnSmall}`} onClick={() => saveCommentEdit(comment.id)}>Сохранить</button>
                                            <button className={`${commonStyles.buttonSecondary} ${styles.btnSmall}`} onClick={() => setEditingCommentId(null)}>Отмена</button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <p className={styles.commentText}>{comment.text}</p>
                                        <div className={styles.commentActions}>
                                            {(user?.role === 'admin' || user?.id === comment.author.id) && (
                                                <button 
                                                    className={`${styles.btnTextAction} ${styles.textAccent}`}
                                                    onClick={() => startEditComment(comment)}
                                                >
                                                    Изменить
                                                </button>
                                            )}
                                            {(user?.role === 'admin' || user?.id === comment.author.id) && (
                                                <button 
                                                    className={`${styles.btnTextAction} ${styles.textDanger}`}
                                                    onClick={() => handleDeleteComment(comment.id)}
                                                >
                                                    Удалить
                                                </button>
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>

                    {user ? (
                        <form onSubmit={handleCommentSubmit} className={commonStyles.formGroup}>
                            <textarea 
                                className={commonStyles.input} 
                                value={newComment} 
                                onChange={e => setNewComment(e.target.value)} 
                                placeholder="Написать комментарий..." 
                                rows="3" 
                                required 
                            />
                            <button type="submit" className={`${commonStyles.button} ${styles.btnAuto}`} style={{alignSelf: 'flex-end'}}>Отправить</button>
                        </form>
                    ) : (
                        <div className={styles.loginPrompt}>
                            <Link to="/login" className={styles.loginLink}>Войдите</Link>, чтобы оставить комментарий.
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}
