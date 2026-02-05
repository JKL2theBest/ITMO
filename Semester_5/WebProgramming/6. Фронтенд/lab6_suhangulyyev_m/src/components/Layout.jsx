import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import styles from './Navbar.module.css';
import commonStyles from '../styles/Common.module.css';

export default function Layout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const canCreate = user && (user.role === 'verified_author' || user.role === 'admin');
    const isAdmin = user && user.role === 'admin';

    return (
        <div>
            <nav className={styles.navbar}>
                <Link to="/" className={styles.logo}>ITMO News</Link>
                
                <div className={styles.links}>
                    <Link to="/" className={styles.link}>Новости</Link>
                    {canCreate && (
                        <Link to="/create" className={styles.link}>+ Создать</Link>
                    )}
                    {isAdmin && (
                        <Link to="/admin/users" className={styles.link} style={{color: '#e74c3c'}}>Админка</Link>
                    )}
                </div>

                <div className={styles.auth}>
                    {user ? (
                        <>
                            <Link to="/profile" className={styles.userInfo} style={{textDecoration: 'none', display: 'flex', alignItems: 'center'}}>
                                {user.name}
                                <span className={styles.badge}>
                                    {user.role === 'verified_author' ? 'Author' : user.role}
                                </span>
                            </Link>
                            <button className={styles.btnLogout} onClick={handleLogout}>Выйти</button>
                        </>
                    ) : (
                        <Link to="/login" className={styles.link}>Войти</Link>
                    )}
                </div>
            </nav>
            <main className={commonStyles.container}>
                <Outlet />
            </main>
        </div>
    );
}
