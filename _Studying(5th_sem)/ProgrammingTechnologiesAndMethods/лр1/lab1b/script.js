document.addEventListener('DOMContentLoaded', (() => {
    if (location.protocol === 'file:') {
        document.body.innerHTML = `<div style="text-align:center;margin-top:2em;font-family:sans-serif;">Контент не может быть просмотрен локально.</div>`;
        return () => {};
    }

    const P_HASH = 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3'; // '123'
    const TIMEOUT = 500;
    let timer;

    const styleEl = document.createElement('style');
    styleEl.textContent = `
        /* Блокировка выделения текста */
        .prot {
            -webkit-user-select: none;
            user-select: none;
        }
        
        #wm {
            position: fixed;
            inset: 0; 
            z-index: 9999;
            background: rgba(255, 255, 255, 0.98);
            color: red;
            font-size: 2em;
            text-align: center;
            padding-top: 20vh;
            
            pointer-events: none;
            
            opacity: 0;
            transition: opacity 0.2s ease-in-out;
        }
        
        #wm.vis {
            opacity: 1;
        }

        @media print {
            #wm {
                display: none !important;
        }}
    `;
    document.head.append(styleEl);

    const watermarkEl = document.createElement('div');
    watermarkEl.id = 'wm';
    watermarkEl.innerHTML = `КОПИРОВАНИЕ ЗАПРЕЩЕНО<br>
        <small style="font-size:0.5em;color:#333;">
        Все материалы являются объектом авторского права.<br>
        Незаконное копирование преследуется по ст. 146 УК РФ.<br>
        Ваша геолокация и отпечаток устройства зафиксированы.</small>`;

    const sha256 = async (str) => {
        const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
        return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
    };

    const handlers = {
        resetTimer: () => {
            watermarkEl.classList.remove('vis');
            clearTimeout(timer);
            timer = setTimeout(() => watermarkEl.classList.add('vis'), TIMEOUT);
        },
        keydown: async (e) => {
            handlers.resetTimer();
            if (e.ctrlKey && e.altKey && e.key === 'd') {
                const pass = prompt('Пароль для отключения защиты:');
                if (pass && await sha256(pass) === P_HASH) {
                    toggleProtection(false);
                } else if (pass) {
                    alert('Неверный пароль!');
                }
            }
            if ((e.ctrlKey && 'csu'.includes(e.key)) || e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
                e.preventDefault();
            }
        },
        prevent: (e) => e.preventDefault(),
    };

    const listeners = [
        ['mousemove', handlers.resetTimer],
        ['scroll', handlers.resetTimer],
        ['keydown', handlers.keydown],
        ['contextmenu', handlers.prevent]
    ];

    const toggleProtection = (enable) => {
        const method = enable ? 'addEventListener' : 'removeEventListener';
        listeners.forEach(([event, handler]) => document[method](event, handler));
        
        document.body.classList.toggle('prot', enable);
        clearTimeout(timer);

        if (enable) {
            document.body.append(watermarkEl);
            handlers.resetTimer();
        } else {
            watermarkEl.remove();
            alert('Защита отключена.');
        }
    };
    
    toggleProtection(true);
    console.log('Защита контента активна. Нажмите Ctrl + Alt + D для отключения.');
}));