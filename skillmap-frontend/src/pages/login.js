import yandexIcon from '../assets/photo-yandex.png';
import API_CONFIG from '../config.js';
import { setTokens } from '../auth.js';

// 1. Карта редиректов по ролям
const ROLE_REDIRECTS = {
    employee: '/profile',
    manager: '/matrix',
    hr: '/hr',
};

// 2. HTML-Шаблон страницы
function getLoginTemplate() {
    return `
        <div class="main-container">
            <div class="auth-container">
                <h1 class="title">SkillMap</h1>
                <label class="subtitle">Введите данные для авторизации</label>

                <form id="login-form" class="login-form" novalidate>
                    <!-- Блок для общих ошибок (например, ошибки от Яндекса) -->
                    <div id="general-error" class="error-message general-error hidden"></div>

                    <div class="form-group">
                        <label for="email">Корпоративная почта</label>
                        <input type="email" id="email" name="email" placeholder="examplemail@gmail.com">
                        <div class="error-message" id="email-error"></div>
                    </div>

                    <div class="form-group">
                        <label for="password">Пароль</label>
                        <input type="password" id="password" name="password" placeholder="********">
                        <div class="error-message" id="password-error"></div>
                    </div>

                    <button type="submit" class="btn-primary">Войти</button>

                    <div class="divider">
                        <span>или</span>
                    </div>

                    <button type="button" class="btn-google" id="yandex-login-btn">
                        <img src="${yandexIcon}" alt="Yandex" class="google-icon">
                        Войти через Яндекс
                    </button>
                </form>

                <a href="#" class="forgot">Забыли пароль?</a>

                <div class="info-auth">
                    <span>Нет аккаунта?</span>
                    <a href="#">Обратитесь к HR</a>
                </div>
            </div>
        </div>
    `;
}

// 3. Управление отображением ошибок
function clearErrors(form) {
    form.querySelectorAll('.error-message').forEach(
        (el) => (el.textContent = ''),
    );
    form.querySelectorAll('.error').forEach((el) =>
        el.classList.remove('error'),
    );
}

function showInputError(inputId, message) {
    const input = document.getElementById(inputId);
    const errorEl = document.getElementById(`${inputId}-error`);

    if (input) input.classList.add('error');
    if (errorEl) errorEl.textContent = message;
}

function showGeneralError(message) {
    const generalErrEl = document.getElementById('general-error');
    if (generalErrEl) {
        generalErrEl.textContent = message;
        generalErrEl.classList.remove('hidden');
    }
}

// 4. Логика запроса к API
async function loginUser(email, password) {
    const response = await fetch(
        `${API_CONFIG.BASE_URL}${API_CONFIG.AUTH.LOGIN}`,
        {
            method: 'POST',
            headers: API_CONFIG.HEADERS,
            credentials: 'include',
            body: JSON.stringify({ email, password, rememberMe: false }),
        },
    );

    let data = null;
    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
        throw new Error(data?.message || 'Неверная почта или пароль');
    }

    return data;
}

// 5. Проверка параметров URL на ошибки OAuth
function checkYandexOAuthErrors() {
    const url = new URL(window.location.href);
    const err = url.searchParams.get('yandex_error');
    if (!err) return;

    showGeneralError(`Ошибка входа через Яндекс: ${err}`);

    url.searchParams.delete('yandex_error');
    window.history.replaceState({}, '', url.pathname + url.search);
}

// 6. Подключение событий
function bindEvents() {
    const form = document.getElementById('login-form');
    const yandexBtn = document.getElementById('yandex-login-btn');

    yandexBtn?.addEventListener('click', () => {
        window.location.href = '/api/auth/yandex/start';
    });

    form?.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearErrors(form);

        const email = form.email.value.trim();
        const password = form.password.value.trim();

        // Валидация полей
        if (!email || !email.includes('@')) {
            showInputError('email', 'Введите корректную почту');
            return;
        }

        if (!password || password.length < 3) {
            showInputError(
                'password',
                'Пароль должен содержать не менее 3 символов',
            );
            return;
        }

        try {
            const data = await loginUser(email, password);

            if (data?.tokens) {
                setTokens(data.tokens);
            }

            const role = String(data?.user?.role || '')
                .trim()
                .toLowerCase();
            window.location.href = ROLE_REDIRECTS[role] || '/profile';
        } catch (error) {
            showInputError('password', error.message);
        }
    });
}

// 7. Основная функция рендера
export function renderLoginPage() {
    const app = document.getElementById('app');
    if (!app) return;

    app.innerHTML = getLoginTemplate();
    bindEvents();
    checkYandexOAuthErrors();
}
