// src/pages/info.js

import arrowIcon from "../assets/Icon.svg";
import avatarIcon from "../assets/icon-avatar.jpg";
import menuIcon1 from "../assets/image-menu1.svg";
import menuIcon2 from "../assets/image-menu2.svg";
import uploadImg from "../assets/upload.svg";
import { renderHeaderHTML, initHeader } from "../components/header.js";
import API_CONFIG from "../config.js";



const userData = {
    name: "Федорова Дарья Викторовна",
    role: "UI/UX дизайнер"
};

export function renderInfoPage() {
    const app = document.getElementById("app");

    app.innerHTML = `
<div class="info-page">

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

    <main class="info-main">

        <div class="info-card">

            <h2 class="info-title">
                Редактирование профиля
            </h2>

            <section class="info-section">

                <h3 class="info-section-title">
                    Фото профиля
                </h3>

                <div class="info-photo-row">

                    <img
                        src="${avatarIcon}"
                        alt="avatar"
                        class="info-avatar"
                    >

                    <div class="info-upload-wrapper">
                        <button class="info-upload-btn">
                                            <img class="upload-img" src="${uploadImg}">

                            Загрузить новое фото
                        </button>

                        <span class="info-upload-text">
                            JPG, PNG, не более 5 МБ
                        </span>

                    </div>

                </div>

            </section>

            <section class="info-section">

                <h3 class="info-section-title">
                    О себе
                </h3>

                <textarea class="info-about">
Занимаюсь UI/UX дизайном более 4 лет. Есть опыт работы продуктовым аналитиком.
Всегда рада делиться опытом и помогать коллегам.
                </textarea>

            </section>

            <section class="info-section">

                <h3 class="info-section-title">
                    Контактные данные
                </h3>

                <div class="info-grid">

                    <div class="info-field">
                        <label>Должность:</label>
                        <input
                            type="text"
                            value="UI/UX дизайнер"
                        >
                    </div>

                    <div class="info-field">
                        <label>Отдел:</label>
                        <input
                            type="text"
                            value="UI/UX"
                        >
                    </div>

                    <div class="info-field">
                        <label>Город:</label>
                        <input
                            type="text"
                            value="г. Екатеринбург"
                        >
                    </div>

                    <div class="info-field">
                        <label></label>
                    </div>

                    <div class="info-field">
                        <label>Контактный телефон:</label>
                        <input
                            type="text"
                            value="+7 919 470 0936"
                        >
                    </div>

                    <div class="info-field">
                        <label>Электронная почта:</label>
                        <input
                            type="email"
                            value="darafedorova790@gmail.com"
                        >
                    </div>

                </div>

            </section>

            <div class="info-actions">

                <button class="info-save-btn">
                    Сохранить
                </button>

                <button class="info-cancel-btn">
                    Отменить
                </button>

            </div>

        </div>

    </main>

</div>
`;

    initInfoPage();
}

function initInfoPage() {
    const arrow = document.getElementById("dropdownArrow");
    const menu = document.getElementById("dropdownMenu");

    if (arrow && menu) {
        arrow.addEventListener("click", (e) => {
            e.stopPropagation();
            menu.classList.toggle("show");
        });

        document.addEventListener("click", () => {
            menu.classList.remove("show");
        });
    }

    document
        .getElementById("profileBtn")
        ?.addEventListener("click", () => {
            window.navigateTo("/profile");
        });

    document
        .getElementById("logoutBtn")
        ?.addEventListener("click", () => {
            localStorage.clear();
            window.navigateTo("/login");
        });
}