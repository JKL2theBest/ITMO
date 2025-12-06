import { useState } from 'react';
import { newsApi } from '../api';
import { useNavigate } from 'react-router-dom';
import styles from './NewsCreate.module.css';
import commonStyles from '../styles/Common.module.css';

export default function NewsCreatePage() {
    const [title, setTitle] = useState('');
    const [body, setBody] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        
        try {
            await newsApi.create({
                title,
                content: { body: body },
                cover_image_url: null
            });
            navigate('/');
        } catch (e) {
            console.error(e);
            if (e.response && e.response.status === 403) {
                setError("У вас нет прав для создания новостей (нужна роль 'Верифицированный автор').");
            } else {
                setError("Ошибка при создании новости.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={commonStyles.container}>
            <div className={commonStyles.card} style={{maxWidth: '700px', margin: '0 auto'}}>
                <h2 className={commonStyles.title}>Новая публикация</h2>
                
                {error && <div className={commonStyles.error}>{error}</div>}
                
                <form onSubmit={handleSubmit} className={commonStyles.formGroup}>
                    <div>
                        <label className={styles.label}>Заголовок</label>
                        <input 
                            type="text" 
                            className={commonStyles.input}
                            placeholder="Введите заголовок новости" 
                            value={title} 
                            onChange={e => setTitle(e.target.value)} 
                            required
                            autoFocus
                        />
                    </div>
                    
                    <div>
                        <label className={styles.label}>Содержание</label>
                        <textarea 
                            className={`${commonStyles.input} ${styles.textarea}`}
                            placeholder="Напишите текст новости здесь..." 
                            value={body} 
                            onChange={e => setBody(e.target.value)} 
                            rows={12}
                            required
                        />
                    </div>

                    <div className={styles.actions}>
                        <button 
                            type="button" 
                            className={`${commonStyles.buttonSecondary} ${styles.btnAutoWidth}`}
                            onClick={() => navigate('/')}
                        >
                            Отмена
                        </button>
                        
                        <button 
                            type="submit" 
                            className={`${commonStyles.button} ${styles.btnAutoWidth}`}
                            disabled={isLoading}
                        >
                            {isLoading ? 'Публикация...' : 'Опубликовать'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
