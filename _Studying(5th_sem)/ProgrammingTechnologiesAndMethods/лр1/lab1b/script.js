// script.js

document.addEventListener('DOMContentLoaded', () => {
    // Хэш пароля '12345' (SHA-256)
    const PWD_HASH = '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5';
    const blinderOverlay = document.getElementById('blinder-overlay');

    async function sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    // --- Новая логика "ослепления" с оверлеем ---
    function blindPage() {
        if (blinderOverlay.style.display !== 'block') {
            blinderOverlay.style.display = 'block';
            // Используем requestAnimationFrame, чтобы скрыть оверлей после следующей отрисовки кадра
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    blinderOverlay.style.display = 'none';
                });
            });
        }
    }
    
    // --- Обработчики событий ---
    const protectionHandler = (e) => {
        if (e.ctrlKey && ['c', 'a', 's', 'u'].includes(e.key.toLowerCase())) {
            e.preventDefault();
            blindPage();
        }
        if (e.key === 'PrintScreen') {
            e.preventDefault();
            blindPage();
        }
    };
    
    const contextMenuHandler = (e) => e.preventDefault();
    const blurHandler = () => blindPage();

    function enableProtection() {
        document.body.classList.add('content-protection-enabled');
        document.addEventListener('contextmenu', contextMenuHandler);
        document.addEventListener('keydown', protectionHandler);
        window.addEventListener('blur', blurHandler);
        console.log('Защита контента включена.');
    }

    function disableProtection() {
        document.body.classList.remove('content-protection-enabled');
        document.removeEventListener('contextmenu', contextMenuHandler);
        document.removeEventListener('keydown', protectionHandler);
        window.removeEventListener('blur', blurHandler);
        sessionStorage.setItem('protectionDisabled', 'true');
        console.log('Защита контента отключена для этой сессии.');
        alert('Защита отключена!');
    }

    // --- Логика отключения по паролю ---
    document.body.addEventListener('dblclick', async (e) => {
        if (e.clientX < 50 && e.clientY < 50) {
            const password = prompt('Введите пароль для отключения защиты:');
            if (password) {
                const enteredHash = await sha256(password);
                if (enteredHash === PWD_HASH) {
                    disableProtection();
                } else {
                    alert('Неверный пароль!');
                }
            }
        }
    });

    // --- Инициализация ---
    if (sessionStorage.getItem('protectionDisabled') !== 'true') {
        enableProtection();
    }
});