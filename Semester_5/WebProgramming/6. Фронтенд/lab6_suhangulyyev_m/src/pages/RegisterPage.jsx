import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import styles from '../styles/Common.module.css';

export default function RegisterPage() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await register(name, email, password);
            navigate('/');
        } catch (err) {
            console.error(err);
            const msg = err.response?.data?.detail || 'Ошибка регистрации.';
            setError(msg);
        }
    };

    return (
        <div className={styles.authCard}>
            <h2 className={styles.title}>Регистрация</h2>
            {error && <div className={styles.error}>{error}</div>}
            
            <form onSubmit={handleSubmit} className={styles.formGroup}>
                <input 
                    type="text" 
                    className={styles.input}
                    placeholder="Имя пользователя" 
                    value={name} 
                    onChange={(e) => setName(e.target.value)} 
                    required
                />
                <input 
                    type="email" 
                    className={styles.input}
                    placeholder="Email" 
                    value={email} 
                    onChange={(e) => setEmail(e.target.value)} 
                    required
                />
                <input 
                    type="password" 
                    className={styles.input}
                    placeholder="Пароль" 
                    value={password} 
                    onChange={(e) => setPassword(e.target.value)} 
                    required
                />
                <button type="submit" className={styles.button}>Зарегистрироваться</button>
            </form>
            
            <p className={styles.linkText}>
                Уже есть аккаунт? <Link to="/login">Войти</Link>
            </p>
        </div>
    );
}
