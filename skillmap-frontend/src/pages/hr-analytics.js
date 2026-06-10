// src/pages/hr-analytics.js
import arrowIcon from "../assets/Icon.svg";
import avatarIcon from "../assets/icon-avatar.jpg";
import menuIcon1 from "../assets/image-menu1.svg";
import menuIcon2 from "../assets/image-menu2.svg";
import arrowUp from "../assets/up.svg";
import arrowDown from "../assets/down.svg";
import API_CONFIG from "../config.js";

import courseIcon1 from "../assets/Component-1.svg";
import courseIcon2 from "../assets/Component-2.svg";
import courseIcon3 from "../assets/Component-3.svg";
import courseIcon4 from "../assets/Component-4.svg";
import courseIcon5 from "../assets/Component-5.svg";

const courseIcons = [courseIcon1, courseIcon2, courseIcon3, courseIcon4, courseIcon5];

function getRandomIcon() {
    return courseIcons[Math.floor(Math.random() * courseIcons.length)];
}

export function renderHrAnalyticsPage() {
    const app = document.getElementById("app");
    if (!app) return;

    // Данные для курсов с иконками
    const coursesData = [
        { name: "Основы Data Engineering" },
        { name: "Информационная безопасность" },
        { name: "Machine Learning с нуля" },
        { name: "Figma с нуля" }
    ];

    // Генерируем HTML для курсов
    const coursesHtml = coursesData.map(course => `
        <div class="analytics-learning-item">
            <div class="analytics-learning-left">
                <div class="course-icon-wrapper">
                    <img src="${getRandomIcon()}" alt="иконка" class="course-icon">
                </div>
                <span>${course.name}</span>
            </div>
            <button class="analytics-plan-btn">Запланировать</button>
        </div>
    `).join('');

    app.innerHTML = `
        <div class="analytics-page">
            <!-- ХЕДЕР -->
            <header class="analytics-header">
                <div class="analytics-header-left">
                    <div class="analytics-logo">SkillMap</div>
                    <nav class="analytics-nav">
                        <a href="#" onclick="event.preventDefault(); window.navigateTo('/'); return false;">Главная</a>
                        <a href="#" onclick="event.preventDefault(); window.navigateTo('/matrix'); return false;">Матрица компетенций</a>
                        <a href="#" onclick="event.preventDefault(); window.navigateTo('/ask'); return false;">Кого спросить?</a>
                    </nav>
                </div>
                <div class="analytics-container-avatar">
                    <div class="analytics-avatar"></div>
                    <div class="analytics-arrow-wrapper">
                        <img src="${arrowIcon}" alt="Стрелка" class="analytics-arrow-icon" id="dropdownArrow">
                        <div class="analytics-dropdown-menu" id="dropdownMenu">
                            <div class="analytics-dropdown-header">
                                <div class="analytics-dropdown-avatar"></div>
                                <div class="analytics-dropdown-info">
                                    <div class="analytics-dropdown-name">HR Директор</div>
                                    <div class="analytics-dropdown-role">HR</div>
                                </div>
                            </div>
                            <div class="analytics-dropdown-divider"></div>
                            <button class="analytics-dropdown-item" id="profileBtn">
                                <img src="${menuIcon1}" alt="Профиль" class="analytics-dropdown-icon">
                                Мой профиль
                            </button>
                            <button class="analytics-dropdown-item analytics-logout" id="logoutBtn">
                                <img src="${menuIcon2}" alt="Выйти" class="analytics-dropdown-icon">
                                Выйти
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <main class="analytics-main">


<!-- ФИЛЬТРЫ -->
<div class="analytics-filters">
                <div class="analytics-title">
                    <h1>Аналитика</h1>
                    <p>Дашборд для стратегических решений</p>
                </div>
                <div class="anal-wrapper">
    <div class="analytics-filter-group">
        <button class="analytics-period-btn active" data-period="month">Месяц</button>
        <button class="analytics-period-btn" data-period="quarter">Квартал</button>
        <button class="analytics-period-btn" data-period="year">Год</button>
    </div>

    <div class="analytics-date-range">
        <div class="date-range-display" id="dateRangeDisplay">
            <span class="range-icon">📅</span>
            <span id="rangeText">1 апр - 30 июн 2025</span>
            <span class="range-arrow">▼</span>
        </div>
        <div class="date-range-picker" id="dateRangePicker" style="display: none;">
            <div class="picker-header">
                <button class="picker-prev">◀</button>
                <span class="picker-month-year">Апрель 2025</span>
                <button class="picker-next">▶</button>
            </div>
            <div class="picker-weekdays">
                <span>Пн</span><span>Вт</span><span>Ср</span><span>Чт</span><span>Пт</span><span>Сб</span><span>Вс</span>
            </div>
            <div class="picker-days" id="pickerDays"></div>
            <div class="picker-actions">
                <button class="picker-cancel">Отмена</button>
                <button class="picker-apply">Применить</button>
            </div>
        </div>
    </div>
    </div>
</div>

                <!-- ТОП 3 КАРТОЧКИ -->
                <div class="analytics-top">
                    <!-- Топ навыков компании -->
                    <div class="analytics-card skills-card">
                        <h3>Топ навыков компании</h3>
                        <span>Динамика популярности навыков</span>
                        <ul>
                            <li><span>Языки программирования (Python)</span>
                            <b class="plus"><img src="${arrowUp}" class="up-img">+18%</b></li>
                            <li><span>Работа с диаграммами (Miro)</span><b class="minus">
                            <img src="${arrowDown}" class="down-img">-36%</b></li>
                            <li><span>Базы данных (Redis)</span><b class="plus">
                            <img src="${arrowUp}" class="up-img">+10%</b></li>
                            <li><span>Языки программирования (Golang)</span><b class="plus">
                            <img src="${arrowUp}" class="up-img">+6%</b></li>
                            <li><span>Базы данных (MySQL)</span><b class="minus">
                            <img src="${arrowDown}" class="down-img">-2%</b></li>
                            <li><span>Работа с Figma</span><b class="minus">
                            <img src="${arrowDown}" class="down-img">-15%</b></li>
                        </ul>
                    </div>

                    <!-- Карта разрывов -->
                    <div class="analytics-card gap-card">
                        <h3>Карта разрывов</h3>
                        <span>Навыки с наибольшим дисбалансом</span>
                        <table>
                            <thead>
                                <tr>
                                    <th></th>
                                    <th>Новичков</th>
                                    <th>Экспертов</th>
                                    <th>Срочность</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr><td>Backend-разработка</td><td>12</td><td>2</td><td><span class="high">Высокая</span></td></tr>
                                <tr><td>Frontend-разработка</td><td>15</td><td>4</td><td><span class="high">Высокая</span></td></tr>
                                <tr><td>Data Science / ML / DE</td><td>18</td><td>5</td><td><span class="high">Высокая</span></td></tr>
                                <tr><td>QA</td><td>22</td><td>7</td><td><span class="high">Высокая</span></td></tr>
                                <tr><td>Аналитика</td><td>16</td><td>6</td><td><span class="medium">Средняя</span></td></tr>
                                <tr><td>UI/UX</td><td>7</td><td>5</td><td><span class="low">Низкая</span></td></tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Планирование обучения -->
                    <div class="analytics-card learning-card">
                        <h3>Планирование обучения</h3>
                        <div class="learning-list">
                            ${coursesHtml}
                        </div>
                    </div>
                </div>

                <!-- РАСПРЕДЕЛЕНИЕ ЭКСПЕРТОВ ПО ОТДЕЛАМ -->
                <div class="analytics-bottom">
                    <h3>Распределение экспертов по отделам</h3>
                    <div class="departments-grid">
                        ${createDepartmentTable()}
                        ${createDepartmentTable()}
                        ${createDepartmentTable()}
                    </div>
                </div>
            </main>
        </div>
    `;

    initHrAnalyticsPage();
}

function createDepartmentTable() {
    return `
        <table class="department-table">
            <thead>
                <tr><th>Отдел</th><th>Навык</th></tr>
            </thead>
            <tbody>
                <tr><td>Backend-разработка</td><td>Языки программирования (Python)</td></tr>
                <tr><td>Frontend-разработка</td><td>Инструменты (HTML)</td></tr>
                <tr><td>Data Science / ML / DE</td><td>Библиотеки (Pandas)</td></tr>
                <tr><td>QA</td><td>Инструменты тестирования (Git)</td></tr>
                <tr><td>Аналитика</td><td>Управление проектами</td></tr>
                <tr><td>UI/UX</td><td>Работа с Figma</td></tr>
            </tbody>
        </table>
    `;
}

let currentPeriod = "month";
let currentDateFrom = null;
let currentDateTo = null;

function initHrAnalyticsPage() {
    // ========== ВЫПАДАЮЩЕЕ МЕНЮ ==========
    const dropdownArrow = document.getElementById("dropdownArrow");
    const dropdownMenu = document.getElementById("dropdownMenu");
    const profileBtn = document.getElementById("profileBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    
    if (dropdownArrow && dropdownMenu) {
        dropdownArrow.addEventListener("click", function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle("show");
        });
        document.addEventListener("click", function(e) {
            if (!dropdownArrow.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove("show");
            }
        });
    }
    
    if (profileBtn) {
        profileBtn.addEventListener("click", function() {
            window.navigateTo('/profile');
        });
    }
    
    if (logoutBtn) {
        logoutBtn.addEventListener("click", function() {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            window.navigateTo('/login');
        });
    }

    // ========== ФИЛЬТРЫ ==========
    const buttons = document.querySelectorAll(".analytics-period-btn");
    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            buttons.forEach(x => x.classList.remove("active"));
            btn.classList.add("active");
            currentPeriod = btn.dataset.period;
            loadAnalytics();
        });
    });

    const dateFromInput = document.getElementById("dateFrom");
    const dateToInput = document.getElementById("dateTo");
    
    if (dateFromInput) {
        dateFromInput.addEventListener("change", (e) => {
            currentDateFrom = e.target.value;
            loadAnalytics();
        });
    }
    
    if (dateToInput) {
        dateToInput.addEventListener("change", (e) => {
            currentDateTo = e.target.value;
            loadAnalytics();
        });
    }

    // Навигация по хедеру
    const navLinks = document.querySelectorAll('.analytics-nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('onclick');
            if (href) eval(href);
        });
    });

    // Инициализация календаря
    initDateRangePicker();
}

async function loadAnalytics() {
    if (!API_CONFIG?.ANALYTICS?.GET) {
        console.log("API_CONFIG.ANALYTICS.GET не настроен");
        return;
    }

    const params = new URLSearchParams();
    params.append("period", currentPeriod);
    if (currentDateFrom) params.append("dateFrom", currentDateFrom);
    if (currentDateTo) params.append("dateTo", currentDateTo);

    try {
        const response = await fetch(`${API_CONFIG.ANALYTICS.GET}?${params.toString()}`, {
            credentials: "include"
        });
        const data = await response.json();
        renderAnalytics(data);
    } catch (error) {
        console.error("Ошибка загрузки аналитики:", error);
    }
}

function renderAnalytics(data) {
    console.log("Данные аналитики:", data);
}
// ========== КАЛЕНДАРЬ ==========
let tempStartDate = null;
let tempEndDate = null;

function generateCalendar(year, month) {
    const firstDay = new Date(year, month, 1);
    const startDayOfWeek = firstDay.getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    let daysHtml = '';
    
    // Пустые ячейки для дней предыдущего месяца
    const offset = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1;
    for (let i = 0; i < offset; i++) {
        daysHtml += '<div class="picker-day empty"></div>';
    }
    
    // Ячейки для дней текущего месяца
    for (let d = 1; d <= daysInMonth; d++) {
        const date = new Date(year, month, d);
        const isSelected = isDateInRange(date, tempStartDate, tempEndDate);
        const isStart = tempStartDate && date.toDateString() === tempStartDate.toDateString();
        const isEnd = tempEndDate && date.toDateString() === tempEndDate.toDateString();
        let classNames = 'picker-day';
        if (isStart) classNames += ' start';
        if (isEnd) classNames += ' end';
        if (isSelected && !isStart && !isEnd) classNames += ' in-range';
        daysHtml += `<div class="${classNames}" data-date="${year}-${month + 1}-${d}">${d}</div>`;
    }
    
    return daysHtml;
}

function isDateInRange(date, start, end) {
    if (!start || !end) return false;
    return date >= start && date <= end;
}

function updateCalendarDisplay() {
    const display = document.getElementById("rangeText");
    if (display && tempStartDate && tempEndDate) {
        const options = { day: 'numeric', month: 'short' };
        const startStr = tempStartDate.toLocaleDateString('ru-RU', options);
        const endStr = tempEndDate.toLocaleDateString('ru-RU', options);
        display.textContent = `${startStr} - ${endStr} ${tempEndDate.getFullYear()}`;
    }
}

function initDateRangePicker() {
    const rangeDisplay = document.getElementById("dateRangeDisplay");
    const rangePicker = document.getElementById("dateRangePicker");
    const pickerPrev = document.querySelector(".picker-prev");
    const pickerNext = document.querySelector(".picker-next");
    const pickerCancel = document.querySelector(".picker-cancel");
    const pickerApply = document.querySelector(".picker-apply");
    const monthYearSpan = document.querySelector(".picker-month-year");
    
    let currentDate = new Date();
    let currentMonth = currentDate.getMonth();
    let currentYear = currentDate.getFullYear();
    
    function renderCalendar() {
        const daysContainer = document.getElementById("pickerDays");
        if (daysContainer) {
            daysContainer.innerHTML = generateCalendar(currentYear, currentMonth);
            monthYearSpan.textContent = `${new Date(currentYear, currentMonth).toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}`;
            
            // Обработчики для дней
            document.querySelectorAll('.picker-day:not(.empty)').forEach(day => {
                day.addEventListener('click', () => {
                    const [year, month, dayNum] = day.dataset.date.split('-');
                    const clickedDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(dayNum));
                    
                    if (!tempStartDate || (tempStartDate && tempEndDate)) {
                        tempStartDate = clickedDate;
                        tempEndDate = null;
                    } else if (tempStartDate && !tempEndDate) {
                        if (clickedDate < tempStartDate) {
                            tempEndDate = tempStartDate;
                            tempStartDate = clickedDate;
                        } else {
                            tempEndDate = clickedDate;
                        }
                    }
                    renderCalendar();
                });
            });
        }
    }
    
    if (rangeDisplay) {
        rangeDisplay.addEventListener("click", () => {
            const isVisible = rangePicker.style.display === "flex";
            rangePicker.style.display = isVisible ? "none" : "flex";
            if (!isVisible) {
                tempStartDate = null;
                tempEndDate = null;
                renderCalendar();
            }
        });
    }
    
    if (pickerPrev) {
        pickerPrev.addEventListener("click", () => {
            currentMonth--;
            if (currentMonth < 0) {
                currentMonth = 11;
                currentYear--;
            }
            renderCalendar();
        });
    }
    
    if (pickerNext) {
        pickerNext.addEventListener("click", () => {
            currentMonth++;
            if (currentMonth > 11) {
                currentMonth = 0;
                currentYear++;
            }
            renderCalendar();
        });
    }
    
    if (pickerCancel) {
        pickerCancel.addEventListener("click", () => {
            rangePicker.style.display = "none";
            tempStartDate = null;
            tempEndDate = null;
        });
    }
    
    if (pickerApply) {
        pickerApply.addEventListener("click", () => {
            if (tempStartDate && tempEndDate) {
                currentDateFrom = tempStartDate.toISOString().split('T')[0];
                currentDateTo = tempEndDate.toISOString().split('T')[0];
                updateCalendarDisplay();
                loadAnalytics();
            }
            rangePicker.style.display = "none";
        });
    }
}