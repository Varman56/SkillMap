from datetime import datetime
from datetime import timezone as tz

from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import (
    Category,
    CategorySubcategory,
    Department,
    DepartmentUser,
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
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "full_name": data["full_name"],
                    "position": data["position"],
                    "is_active": True,
                    "is_intern": "intern" in data["email"],
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()

            # Роль
            role, _ = Role.objects.get_or_create(name=data["role"])
            UserRole.objects.get_or_create(user=user, role=role)

            # Отдел
            department, _ = Department.objects.get_or_create(name=data["department"])
            DepartmentUser.objects.get_or_create(user=user, department=department)

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

        # 3. Назначение навыков пользователям
        levels = [1, 2, 3, 4]
        target_users = [u for u, role in created_users if role in ("Manager", "Employee")]

        for user_idx, user in enumerate(target_users):
            for skill_idx, skill in enumerate(skills):
                level = levels[(user_idx + skill_idx) % len(levels)]
                is_approved = (user_idx + skill_idx) % 3 != 0

                UserSkill.objects.get_or_create(
                    user=user,
                    skill=skill,
                    defaults={
                        "level": level,
                        "is_approved": is_approved,
                    },
                )
        self.stdout.write(self.style.SUCCESS("Скиллы привязаны к пользователям."))

        # 4. Создание проектов и привязка пользователей
        projects = {}
        for pdata in DEMO_PROJECTS:
            project, _ = Project.objects.get_or_create(
                name=pdata["name"],
                defaults={k: v for k, v in pdata.items() if k != "name"},
            )
            projects[project.name] = project

        mvp_project = projects["SkillMap MVP"]
        for user in target_users:
            UserProject.objects.get_or_create(
                user=user,
                project=mvp_project,
                defaults={"joined_at": now},
            )

        self.stdout.write(self.style.SUCCESS("Проекты созданы, пользователи привязаны к SkillMap MVP."))
        self.stdout.write(self.style.SUCCESS("\nГотово. Пароль у всех пользователей: test1234"))