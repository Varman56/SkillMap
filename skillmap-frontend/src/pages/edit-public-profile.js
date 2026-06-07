// src/pages/edit-public-profile.js
import arrowIcon from "../assets/Icon.svg";
import avatarIcon from "../assets/icon-avatar.jpg";
import menuIcon1 from "../assets/image-menu1.svg";
import menuIcon2 from "../assets/image-menu2.svg";
import plusIcon from "../assets/plus.svg";
import editIcon from "../assets/edit.svg";
import phone from "../assets/phone.svg";
import email from "../assets/email.svg";
import city from "../assets/city.svg";
import { renderHeaderHTML, initHeader } from "../components/header.js";
import API_CONFIG from "../config.js";


// Импорт иконок для проектов
import projectIcon1 from "../assets/Component-1.svg";
import projectIcon2 from "../assets/Component-2.svg";
import projectIcon3 from "../assets/Component-3.svg";
import projectIcon4 from "../assets/Component-4.svg";
import projectIcon5 from "../assets/Component-5.svg";

const projectIcons = [projectIcon1, projectIcon2, projectIcon3, projectIcon4, projectIcon5];

// Данные пользователя
const userData = {
    name: "Федорова Дарья Викторовна",
    role: "UI/UX дизайнер",
    department: "Отдел UI/UX",
    city: "г. Екатеринбург",
    phone: "+7 919 470 0936",
    email: "darafedorova790@gmail.com",
};

// Данные проектов
let projectsData = [
    { id: 1, title: "Платформа деплоя", description: "Разработка макетов платформы для автоматического деплоя сервисов" },
    { id: 2, title: "Веб-сайт учета мероприятий", description: "UX сценарии и макеты" },
    { id: 3, title: "Платформа трассировки", description: "Интеграция базы данных" },
    { id: 4, title: "SkillMap", description: "UI Kit и главная страница" },
    { id: 5, title: "Обучающая игра", description: "Динамические макеты" }
];

// Функция для получения случайной иконки
function getRandomIcon() {
    const randomIndex = Math.floor(Math.random() * projectIcons.length);
    return projectIcons[randomIndex];
}

export function renderEditPublicProfilePage() {
    const app = document.getElementById("app");
    if (!app) return;
    
    // Генерируем HTML для проектов с иконками
    function renderProjects() {
        let html = '';
        for (let i = 0; i < projectsData.length; i++) {
            const project = projectsData[i];
            const icon = getRandomIcon();
            html += `
                <div class="project" data-id="${project.id}">
                    <div class="project-header">
                        <img src="${icon}" alt="иконка" class="project-icon">
                        <div class="project-title">${project.title}</div>
                    </div>
                    <div class="project-desc">${project.description}</div>
                </div>
            `;
        }
        return html;
    }
    
    app.innerHTML = `
<div class="edit-public-profile-page">

    <!-- ХЕДЕР -->
    <header class="edit-public-header">
        <div class="edit-public-header-left">
            <div class="edit-public-logo">SkillMap</div>
            <nav class="edit-public-nav">
                <a href="#">Главная</a>
                <a href="#">Матрица компетенций</a>
                <a href="#">Кого спросить?</a>
            </nav>
        </div>
       <div class="profile-container-avatar">
                            <div class="profile-avatar"></div>
                            <div class="profile-arrow-wrapper">
                                <img src="${arrowIcon}" alt="Стрелка" class="profile-arrow-icon" id="dropdownArrow">
                                <div class="profile-dropdown-menu" id="dropdownMenu">
                                    <div class="profile-dropdown-header">
                                        <div class="profile-dropdown-avatar"></div>
                                        <div class="profile-dropdown-info">
                                            <div class="profile-dropdown-name">Дарья Федорова</div>
                                            <div class="profile-dropdown-role">Дизайнер</div>
                                        </div>
                                    </div>
                                    <div class="profile-dropdown-divider"></div>
                                    <button class="profile-dropdown-item" id="editProfileBtn">
                                        <img src="${menuIcon1}" alt="Редактировать" class="profile-dropdown-icon">
                                        Редактировать профиль
                                    </button>
                                    <button class="profile-dropdown-item profile-logout" id="logoutBtn">
                                        <img src="${menuIcon2}" alt="Выйти" class="profile-dropdown-icon">
                                        Выйти
                                    </button>
                                </div>
                            </div>
                        </div>
    </header>

    <!-- ОСНОВНОЙ КОНТЕНТ -->
    <main class="edit-public-main">
        <div class="edit-public-profile-wrapper">

            <div class="edit-public-profile-card">

                <!-- TOP -->
                <div class="edit-public-top">
                    <div class="edit-public-avatar-large">
                        <img src="${userData.avatar}">
                    </div>

                    <div class="edit-public-user-info">
                        <div class="edit-public-name-container">
                            <h2 class="edit-public-name" id="userName">${userData.name}</h2>
                            <button class="edit-public-name-edit" id="editNameBtn">
                                <img src="${editIcon}" alt="Редактировать" class="edit-icon-small">
                            </button>
                        </div>

                        <div class="edit-public-title-row">
                            <span>${userData.role}</span>
                            <span> • ${userData.department}</span>
                        </div>

                        <div class="edit-public-info-items">
                            <div class="edit-public-info-item">
                                <img src="${city}" class="edit-public-info-icon" alt="город">
                                <span>${userData.city}</span>
                            </div>
                            <div class="edit-public-info-item">
                                <img src="${phone}" class="edit-public-info-icon" alt="телефон">
                                <span>${userData.phone}</span>
                            </div>
                            <div class="edit-public-info-item">
                                <img src="${email}" class="edit-public-info-icon" alt="почта">
                                <span>${userData.email}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- BOTTOM -->
                <div class="edit-public-bottom">

                    <!-- LEFT -->
                    <div class="edit-public-left">

                        <div class="edit-public-about">
                            <h3>Обо мне</h3>
                            <p>
                                Занимаюсь UI/UX дизайном более 4 лет. Есть опыт работы продуктовым аналитиком.
                                Всегда рада делиться опытом и помогать коллегам.
                            </p>
                        </div>

                        <div class="edit-public-skills-section">
                            <h3>Навыки</h3>

                            <div class="skill-row">
                                <span class="badge expert">Эксперт</span>
                                <span>Работа с диаграммами (Miro)</span>
                            </div>

                            <div class="skill-row">
                                <span class="badge advanced">Продвинутый</span>
                                <span>Работа с Figma</span>
                            </div>

                            <div class="skill-row">
                                <span class="badge advanced">Продвинутый</span>
                                <span>Работа с Webflow</span>
                            </div>

                            <div class="skill-row">
                                <span class="badge novice">Новичок</span>
                                <span>Базы данных (Redis)</span>
                            </div>

                            <div class="skill-row">
                                <span class="badge novice">Новичок</span>
                                <span>Базы данных (MySQL)</span>
                            </div>

                            <div class="skill-row">
                                <span class="badge experienced">Опытный</span>
                                <span>Python</span>
                            </div>

                            <div class="skill-row">
                                <span class="badge novice">Новичок</span>
                                <span>Golang</span>
                            </div>

                        </div>

                    </div>

                    <div class="edit-public-projects-section">
                        <div class="edit-public-projects-header">
                            <h3>Проекты</h3>
                            <button class="edit-public-projects-add" id="addProjectBtn">
                                Добавить проект
                                <img src="${plusIcon}" alt="Плюс" class="plus-icon">
                            </button>
                        </div>
                        <div id="projectsContainer">
                            ${renderProjects()}
                        </div>
                    </div>

                </div>

            </div>

        </div>
    </main>

    <!-- Модальное окно для ДОБАВЛЕНИЯ проекта -->
    <div class="edit-public-modal" id="addProjectModal">
        <div class="edit-public-modal-content">
            <div class="edit-public-modal-header">
                <h3>Добавить проект</h3>
            </div>
            <form id="addProjectForm">
                <div class="edit-public-form-group">
                    <label>Название проекта:</label>
                    <input type="text" id="projectTitle" placeholder="Введите название проекта" required>
                </div>
                <div class="edit-public-form-group">
                    <label>Описание проекта:</label>
                    <textarea id="projectDescription" rows="3" placeholder="Введите описание проекта" required></textarea>
                </div>
                <div class="edit-public-form-buttons">
                    <button type="submit" class="edit-public-btn-submit">Сохранить</button>
                    <button type="button" class="edit-public-btn-cancel add-project-cancel">Отмена</button>
                </div>
            </form>
        </div>
    </div>
</div>
`;
    
    initEditPublicProfilePage();
}

function initEditPublicProfilePage() {
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
    
    // ========== ФУНКЦИЯ ОБНОВЛЕНИЯ ПРОЕКТОВ ==========
    function renderProjects() {
        const container = document.getElementById("projectsContainer");
        if (!container) return;
        
        let html = '';
        for (let i = 0; i < projectsData.length; i++) {
            const project = projectsData[i];
            const icon = getRandomIcon();
            html += `
                <div class="project" data-id="${project.id}">
                    <div class="project-header">
                        <img src="${icon}" alt="иконка" class="project-icon">
                        <div class="project-title">${project.title}</div>
                        <button class="project-delete-btn" data-id="${project.id}">🗑️</button>
                    </div>
                    <div class="project-desc">${project.description}</div>
                </div>
            `;
        }
        container.innerHTML = html;
    }
    
    // ========== МОДАЛЬНОЕ ОКНО ДОБАВЛЕНИЯ ПРОЕКТА ==========
    const addProjectModal = document.getElementById("addProjectModal");
    const addProjectBtn = document.getElementById("addProjectBtn");
    const addProjectCloseBtn = document.querySelector(".add-project-modal-close");
    const addProjectCancelBtn = document.querySelector(".add-project-cancel");
    const addProjectForm = document.getElementById("addProjectForm");
    
    function openAddProjectModal() {
        addProjectModal.classList.add("show");
    }
    
    function closeAddProjectModal() {
        addProjectModal.classList.remove("show");
        if (addProjectForm) addProjectForm.reset();
    }
    
    if (addProjectBtn) addProjectBtn.addEventListener("click", openAddProjectModal);
    if (addProjectCloseBtn) addProjectCloseBtn.addEventListener("click", closeAddProjectModal);
    if (addProjectCancelBtn) addProjectCancelBtn.addEventListener("click", closeAddProjectModal);
    
    if (addProjectModal) {
        addProjectModal.addEventListener("click", (e) => {
            if (e.target === addProjectModal) closeAddProjectModal();
        });
    }
    
    if (addProjectForm) {
        addProjectForm.addEventListener("submit", (e) => {
            e.preventDefault();
            
            const title = document.getElementById("projectTitle")?.value.trim();
            const description = document.getElementById("projectDescription")?.value.trim();
            
            if (!title || !description) {
                closeAddProjectModal();
                return;
            }
            
            const newId = Math.max(...projectsData.map(p => p.id), 0) + 1;
            projectsData.push({ id: newId, title, description });
            
            closeAddProjectModal();
            renderProjects();
        });
    }
    
    // Навигация по хедеру
    const navLinks = document.querySelectorAll('.edit-public-nav a');
    navLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('onclick');
            if (href) {
                eval(href);
            }
        });
    });
}