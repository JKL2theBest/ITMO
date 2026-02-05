import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import styles from '../styles/Common.module.css';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await login(email, password);
            navigate('/');
        } catch (err) {
            console.error(err);
            setError('Неверный email или пароль');
        }
    };

    return (
        <div className={styles.authCard}>
            <h2 className={styles.title}>Вход</h2>
            {error && <div className={styles.error}>{error}</div>}
            
            <form onSubmit={handleSubmit} className={styles.formGroup}>
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
                <button type="submit" className={styles.button}>Войти</button>
            </form>
            
            <p className={styles.linkText}>
                Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
            </p>
        </div>
    );
}
