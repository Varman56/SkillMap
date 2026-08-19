from datetime import datetime
from datetime import timezone as tz

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import (
    Category,
    CategorySubcategory,
    Department,
    Project,
    Role,
    Skill,
    Subcategory,
    SubcategorySkill,
    User,
    UserProject,
    UserRole,
    UserSkill,
)

DEMO_PASSWORD = "test1234"

DEMO_USERS = [
    {"email": "hr@test.com", "full_name": "Анна Кузнецова", "position": "HR-менеджер", "role": "HR", "department": "HR"},
    {"email": "hr2@test.com", "full_name": "Мария Захарова", "position": "HR-специалист", "role": "HR", "department": "HR"},
    {"email": "manager@test.com", "full_name": "Игорь Соколов", "position": "Тимлид Backend", "role": "Manager", "department": "Разработка"},
    {"email": "manager2@test.com", "full_name": "Дмитрий Волков", "position": "Тимлид Frontend", "role": "Manager", "department": "Разработка"},
    {"email": "manager3@test.com", "full_name": "Елена Морозова", "position": "Product Manager", "role": "Manager", "department": "Продукт"},
    {"email": "employee@test.com", "full_name": "Пётр Новиков", "position": "Backend-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "employee2@test.com", "full_name": "Александр Лебедев", "position": "Frontend-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "employee3@test.com", "full_name": "Ольга Козлова", "position": "Fullstack-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "employee4@test.com", "full_name": "Сергей Егоров", "position": "DevOps-инженер", "role": "Employee", "department": "DevOps"},
    {"email": "employee5@test.com", "full_name": "Наталья Соловьёва", "position": "QA-инженер", "role": "Employee", "department": "QA"},
    {"email": "employee6@test.com", "full_name": "Артём Павлов", "position": "Backend-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "employee7@test.com", "full_name": "Виктория Семёнова", "position": "UX/UI-дизайнер", "role": "Employee", "department": "Дизайн"},
    {"email": "employee8@test.com", "full_name": "Максим Голубев", "position": "Продуктовый аналитик", "role": "Employee", "department": "Аналитика"},
    {"email": "employee9@test.com", "full_name": "Юлия Виноградова", "position": "Frontend-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "employee10@test.com", "full_name": "Иван Богданов", "position": "Backend-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "employee11@test.com", "full_name": "Дарья Воробьёва", "position": "QA-инженер", "role": "Employee", "department": "QA"},
    {"email": "employee12@test.com", "full_name": "Роман Фёдоров", "position": "DevOps-инженер", "role": "Employee", "department": "DevOps"},
    {"email": "employee13@test.com", "full_name": "Кристина Орлова", "position": "Fullstack-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "intern1@test.com", "full_name": "Никита Соболев", "position": "Junior Backend-разработчик", "role": "Employee", "department": "Разработка"},
    {"email": "intern2@test.com", "full_name": "Полина Кириллова", "position": "Junior QA-инженер", "role": "Employee", "department": "QA"},
    # Уволенные — для проверки фильтра "Только уволенные" на странице
    # "Кадровый резерв" (only_terminated=1, см. reserve_page.py). У них
    # is_active=False, поэтому по умолчанию (без флага) они больше нигде в
    # активных списках не показываются — только в резерве по этой галочке.
    {"email": "terminated1@test.com", "full_name": "Владимир Кузьмин", "position": "Backend-разработчик", "role": "Employee", "department": "Разработка", "is_active": False},
    {"email": "terminated2@test.com", "full_name": "Светлана Морозова", "position": "QA-инженер", "role": "Employee", "department": "QA", "is_active": False},
    {"email": "terminated3@test.com", "full_name": "Андрей Никитин", "position": "DevOps-инженер", "role": "Employee", "department": "DevOps", "is_active": False},
]

DEMO_SKILLS = [
    {"category": "Backend", "subcategory": "Языки программирования", "name": "Python"},
    {"category": "Backend", "subcategory": "Библиотеки/Фреймворки", "name": "Django"},
    {"category": "Backend", "subcategory": "Библиотеки/Фреймворки", "name": "FastAPI"},
    {"category": "Frontend", "subcategory": "Языки программирования", "name": "JavaScript"},
    {"category": "Frontend", "subcategory": "Языки программирования", "name": "TypeScript"},
    {"category": "Frontend", "subcategory": "Библиотеки/Фреймворки", "name": "React"},
    {"category": "Frontend", "subcategory": "Библиотеки/Фреймворки", "name": "Vue.js"},
    {"category": "Базы данных", "subcategory": "Реляционные СУБД", "name": "PostgreSQL"},
    {"category": "Базы данных", "subcategory": "NoSQL", "name": "MongoDB"},
    {"category": "DevOps", "subcategory": "Контейнеризация", "name": "Docker"},
    {"category": "DevOps", "subcategory": "Оркестрация", "name": "Kubernetes"},
    {"category": "Инструменты", "subcategory": "Системы контроля версий", "name": "Git"},
    {"category": "Дизайн", "subcategory": "UI/UX-инструменты", "name": "Figma"},
    {"category": "Управление", "subcategory": "Методологии", "name": "Agile"},
    {"category": "Управление", "subcategory": "Методологии", "name": "Scrum"},
    {"category": "Soft Skills", "subcategory": "Языки", "name": "Английский язык"},
]

DEMO_PROJECTS = [
    {
        "name": "SkillMap MVP",
        "description": "Демо-проект для разработки и тестирования",
        "status": "Active",
        "start_date": datetime(2026, 1, 15, tzinfo=tz.utc),
        "end_date": None,
    },
    {
        "name": "CRM Обновление",
        "description": "Модернизация внутренней CRM-системы компании",
        "status": "Active",
        "start_date": datetime(2026, 5, 1, tzinfo=tz.utc),
        "end_date": None,
    },
    {
        "name": "Mobile App v2",
        "description": "Второе поколение мобильного приложения компании",
        "status": "Completed",
        "start_date": datetime(2025, 10, 10, tzinfo=tz.utc),
        "end_date": datetime(2026, 7, 1, tzinfo=tz.utc),
    },
    {
        "name": "Внутренний HR-портал",
        "description": "Портал для управления отпусками и профилями сотрудников",
        "status": "On Hold",
        "start_date": datetime(2026, 3, 10, tzinfo=tz.utc),
        "end_date": None,
    },
    {
        "name": "Аналитика продаж",
        "description": "BI-дашборды для отдела продаж и аналитики",
        "status": "Active",
        "start_date": datetime(2026, 6, 5, tzinfo=tz.utc),
        "end_date": None,
    },
    {
        "name": "Редизайн корпоративного сайта",
        "description": "Обновление дизайна и вёрстки публичного сайта компании",
        "status": "Completed",
        "start_date": datetime(2026, 2, 1, tzinfo=tz.utc),
        "end_date": datetime(2026, 6, 20, tzinfo=tz.utc),
    },
    {
        "name": "Миграция на Kubernetes",
        "description": "Перевод инфраструктуры с VM на Kubernetes-кластер",
        "status": "Active",
        "start_date": datetime(2026, 5, 27, tzinfo=tz.utc),
        "end_date": None,
    },
    {
        "name": "Нагрузочное тестирование платформы",
        "description": "Проверка производительности системы перед пиковым сезоном",
        "status": "Completed",
        "start_date": datetime(2026, 6, 16, tzinfo=tz.utc),
        "end_date": datetime(2026, 7, 26, tzinfo=tz.utc),
    },
]


class Command(BaseCommand):
    help = "Заполняет БД тестовыми данными (Пользователи, Категории, Подкатегории, Навыки, Проекты)"

    def handle(self, *args, **options):
        now = timezone.now()

        # 1. Создание пользователей, ролей и отделов
        created_users = []
        for data in DEMO_USERS:
            is_active = data.get("is_active", True)
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "full_name": data["full_name"],
                    "position": data["position"],
                    "is_active": is_active,
                    "is_intern": "intern" in data["email"],
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()

            # На случай повторного запуска seed на уже существующей БД —
            # is_active мог не совпадать с тем, что сейчас задано в
            # DEMO_USERS (например, уволенных добавили уже после первого
            # посева) — синхронизируем.
            if user.is_active != is_active:
                user.is_active = is_active
                user.save(update_fields=["is_active"])

            # Аватарка — рандомная, но стабильная для конкретного email
            # (i.pravatar.cc с одним и тем же ?u= всегда отдаёт одну и ту
            # же картинку). Ставим ВСЕМ, включая уже существующих
            # пользователей с пустым photo — удобно разом визуально
            # проверить, что аватарка отображается на каждой странице
            # (профиль, "кого спросить", кадровый резерв, матрица и т.д.),
            # а не гадать вручную, где её забыли вывести.
            if not user.photo:
                user.photo = f"https://i.pravatar.cc/300?u={user.email}"
                user.save(update_fields=["photo"])

            # Роль
            role, _ = Role.objects.get_or_create(name=data["role"])
            UserRole.objects.get_or_create(user=user, role=role)

            # Отдел (один на пользователя)
            department, _ = Department.objects.get_or_create(name=data["department"])
            if user.department_id != department.id:
                user.department = department
                user.save(update_fields=["department"])

            if created:
                self.stdout.write(self.style.SUCCESS(f"Создан пользователь: {user.email} ({data['role']})"))
            else:
                self.stdout.write(f"Уже существует: {user.email}")

            created_users.append((user, data["role"]))

        # 2. Создание Категорий, Подкатегорий, Навыков и связей между ними
        skills = []
        for data in DEMO_SKILLS:
            # Навык
            skill, _ = Skill.objects.get_or_create(
                name=data["name"],
                defaults={"is_active": True},
            )
            skills.append(skill)

            # Подкатегория
            subcategory, _ = Subcategory.objects.get_or_create(name=data["subcategory"])

            # Категория
            category, _ = Category.objects.get_or_create(name=data["category"])

            # Связи M2M через 중간ные таблицы (through models)
            CategorySubcategory.objects.get_or_create(category=category, subcategory=subcategory)
            SubcategorySkill.objects.get_or_create(subcategory=subcategory, skill=skill)

        self.stdout.write(self.style.SUCCESS("Категории, подкатегории и навыки созданы."))

        # 3. Назначение навыков пользователям.
        #
        # ВАЖНО: раньше у пары (user, skill) была ровно одна строка, и
        # get_or_create(user=user, skill=skill, ...) однозначно её находил.
        # Теперь у пары может быть 2 строки (апрув + заявка, см. docstring
        # UserSkill) — если ниже, в шаге 3.1, уже создали 2 строки для
        # Docker, то при повторном запуске команды тот же
        # get_or_create(user=user, skill=skill) находит 2 совпадения и
        # падает с MultipleObjectsReturned. Поэтому здесь просто проверяем
        # "есть ли вообще хоть одна строка" и не трогаем существующие —
        # идемпотентность за счёт exists()-проверки, а не get_or_create.
        levels = [1, 2, 3, 4]
        target_users = [u for u, role in created_users if role in ("Manager", "Employee")]

        for user_idx, user in enumerate(target_users):
            for skill_idx, skill in enumerate(skills):
                if UserSkill.objects.filter(user=user, skill=skill).exists():
                    continue

                level = levels[(user_idx + skill_idx) % len(levels)]
                is_approved = (user_idx + skill_idx) % 3 != 0

                UserSkill.objects.create(
                    user=user,
                    skill=skill,
                    level=level,
                    is_approved=is_approved,
                )
        self.stdout.write(self.style.SUCCESS("Скиллы привязаны к пользователям."))

        # 3.1. Тестовый набор: у КАЖДОГО сотрудника — сразу НЕСКОЛЬКО навыков
        # (не все, но заметная часть — из разных категорий, чтобы матрица
        # была заполнена такими иконками не одним столбцом, а по всей
        # ширине) в двух статусах одновременно: подтверждённый уровень +
        # отдельная заявка на более высокий (см. includes/skill_icon.html —
        # для такой пары рисуется совмещённая иконка).
        #
        # ВАЖНО: заявка (is_approved=False) ВСЕГДА строго выше уже
        # подтверждённого уровня — это инвариант приложения (см.
        # _approved_level/_handle_add_skill/_handle_update_skill в
        # profile_page.py). Заявка на тот же или более низкий уровень, чем
        # уже подтверждён, бессмысленна и такую строку нельзя завести или
        # сохранить через профиль — соответственно, и здесь, в демо-данных,
        # комбинации level_combos ТОЛЬКО "повышение", без "понижения"/"того
        # же уровня" (раньше тут были ещё комбинации вроде (4, 1) — это и
        # был баг, который показывал на профиле подтверждённый уровень выше
        # заявки на рассмотрении).
        dual_state_skill_names = [
            "Docker", "Kubernetes",       # DevOps
            "Python", "Django",           # Backend
            "JavaScript", "React",        # Frontend
            "PostgreSQL",                 # Базы данных
            "Git",                        # Инструменты
            "Figma",                      # Дизайн
        ]
        # (уровень апрува, уровень заявки) — заявка строго выше апрува
        level_combos = [
            (1, 2), (1, 3), (1, 4),  # повышение с новичка
            (2, 3), (2, 4),          # повышение с опытного
            (3, 4),                  # повышение с продвинутого
        ]

        dual_state_count = 0
        for skill_offset, skill_name in enumerate(dual_state_skill_names):
            dual_skill = next((s for s in skills if s.name == skill_name), None)
            if not dual_skill:
                continue

            for user_idx, user in enumerate(target_users):
                # Сдвиг по навыку — чтобы соседние столбцы не повторяли
                # один и тот же узор комбинаций один в один.
                combo_idx = (user_idx + skill_offset * 3) % len(level_combos)
                approved_level, pending_level = level_combos[combo_idx]

                UserSkill.objects.update_or_create(
                    user=user, skill=dual_skill, is_approved=True,
                    defaults={"level": approved_level},
                )
                UserSkill.objects.update_or_create(
                    user=user, skill=dual_skill, is_approved=False,
                    defaults={"level": pending_level},
                )
                dual_state_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Тестовый набор: {len(dual_state_skill_names)} навыков "
            f"({', '.join(dual_state_skill_names)}) — у каждого сотрудника "
            "подтверждены + есть заявка на другой уровень "
            f"({dual_state_count} пар строк). Видно по всей матрице, не "
            "только в одном столбце."
        ))

        # 4. Создание проектов и привязка пользователей.
        #
        # DEMO_PROJECTS уже содержит 8 проектов (просили "штук 5-7") — все
        # они и раньше создавались в БД, но реально пользователей получала
        # только "SkillMap MVP", остальные 7 висели пустыми. Теперь
        # раздаём пользователей по ВСЕМ проектам, причём КОЛИЧЕСТВО
        # проектов на человека намеренно разное (от 0 до всех сразу) —
        # это специально для проверки вёрстки блока "Проекты" в профиле:
        # пустой список, один проект, и длинный список с прокруткой
        # (см. .public-projects-section в profile.css — max-height:480px
        # с overflow-y:auto) — чтобы визуально проверить, не съезжает ли
        # что-то при разном количестве карточек.
        # У каждого проекта теперь есть владелец (created_by) — им может
        # быть только руководитель (роль Manager), по кругу распределяем
        # трёх менеджеров из DEMO_USERS на 8 проектов. Раньше created_by
        # либо не заполнялся вообще, либо не переустанавливался при
        # повторном запуске сида — из-за этого право редактировать
        # проект (см. project_page.py, теперь оно только у владельца, а
        # не у любого HR/Manager) было бы не у кого проверить в демо.
        manager_users = [u for u, role in created_users if role == "Manager"]

        projects = {}
        for idx, pdata in enumerate(DEMO_PROJECTS):
            owner = manager_users[idx % len(manager_users)] if manager_users else None
            project, _ = Project.objects.get_or_create(
                name=pdata["name"],
                defaults={
                    **{k: v for k, v in pdata.items() if k != "name"},
                    "created_by": owner,
                },
            )
            # get_or_create применяет defaults только при создании — при
            # повторном запуске на уже существующей БД владелец мог бы
            # остаться прежним/пустым, синхронизируем и для уже
            # существующих записей.
            if project.created_by_id != (owner.id if owner else None):
                project.created_by = owner
                project.save(update_fields=["created_by"])
            projects[project.name] = project

        project_names = [pdata["name"] for pdata in DEMO_PROJECTS]
        project_count = len(project_names)

        # Сбрасываем прежние привязки target_users к проектам — иначе при
        # повторном запуске сида на уже заполненной БД старые связи (из
        # прошлых версий этой команды, когда все сидели в одной MVP)
        # остались бы висеть вперемешку с новым распределением, и итоговая
        # картина по пользователю перестала бы соответствовать
        # предсказуемому паттерну ниже.
        UserProject.objects.filter(user__in=target_users).delete()

        for user_idx, user in enumerate(target_users):
            # Количество проектов у пользователя циклически пробегает
            # 0..project_count (0 — пусто, project_count — сразу во всех),
            # чтобы оба крайних случая гарантированно встретились хотя бы
            # у кого-то, а не только "типичные" 1-2 проекта.
            count = user_idx % (project_count + 1)
            for offset in range(count):
                name = project_names[(user_idx + offset) % project_count]
                UserProject.objects.get_or_create(user=user, project=projects[name])

        # Владелец проекта (created_by) должен быть и его участником —
        # иначе получается нелогично: в правой колонке страницы проекта
        # владелец есть, а в списке участников его нет, а в его
        # собственном профиле блок "Проекты" пустой, хотя это его проект.
        # Случайное распределение выше могло не назначить владельца на
        # его же проект — досоздаём недостающие связи отдельно, поверх.
        for project in projects.values():
            if project.created_by_id:
                UserProject.objects.get_or_create(
                    user_id=project.created_by_id,
                    project=project,
                    defaults={"joined_at": timezone.now()},
                )

        self.stdout.write(self.style.SUCCESS(
            f"Проекты созданы ({project_count} шт.), пользователи распределены по ним "
            "(от 0 до всех проектов на человека), у каждого проекта назначен "
            "владелец из руководителей (Manager), владелец всегда состоит "
            "в числе участников своего проекта."
        ))
        self.stdout.write(self.style.SUCCESS("\nГотово. Пароль у всех пользователей: test1234"))