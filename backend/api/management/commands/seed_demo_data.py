from django.core.management.base import BaseCommand
from django.utils import timezone

from api.helpers import assign_department, assign_role, attach_skill_to_category
from api.models import Project, Skill, User, UserProject, UserSkill

DEMO_PASSWORD = "test1234"

DEMO_USERS = [
    # HR
    {"email": "hr@test.com", "full_name": "Анна Кузнецова", "role": "HR",
     "position": "HR-менеджер", "department": "HR"},
    {"email": "hr2@test.com", "full_name": "Мария Захарова", "role": "HR",
     "position": "HR-специалист", "department": "HR"},

    # Manager
    {"email": "manager@test.com", "full_name": "Игорь Соколов", "role": "Manager",
     "position": "Тимлид Backend", "department": "Разработка"},
    {"email": "manager2@test.com", "full_name": "Дмитрий Волков", "role": "Manager",
     "position": "Тимлид Frontend", "department": "Разработка"},
    {"email": "manager3@test.com", "full_name": "Елена Морозова", "role": "Manager",
     "position": "Product Manager", "department": "Продукт"},

    # Employee
    {"email": "employee@test.com", "full_name": "Пётр Новиков", "role": "Employee",
     "position": "Backend-разработчик", "department": "Разработка"},
    {"email": "employee2@test.com", "full_name": "Александр Лебедев", "role": "Employee",
     "position": "Frontend-разработчик", "department": "Разработка"},
    {"email": "employee3@test.com", "full_name": "Ольга Козлова", "role": "Employee",
     "position": "Fullstack-разработчик", "department": "Разработка"},
    {"email": "employee4@test.com", "full_name": "Сергей Егоров", "role": "Employee",
     "position": "DevOps-инженер", "department": "DevOps"},
    {"email": "employee5@test.com", "full_name": "Наталья Соловьёва", "role": "Employee",
     "position": "QA-инженер", "department": "QA"},
    {"email": "employee6@test.com", "full_name": "Артём Павлов", "role": "Employee",
     "position": "Backend-разработчик", "department": "Разработка"},
    {"email": "employee7@test.com", "full_name": "Виктория Семёнова", "role": "Employee",
     "position": "UX/UI-дизайнер", "department": "Дизайн"},
    {"email": "employee8@test.com", "full_name": "Максим Голубев", "role": "Employee",
     "position": "Продуктовый аналитик", "department": "Аналитика"},
    {"email": "employee9@test.com", "full_name": "Юлия Виноградова", "role": "Employee",
     "position": "Frontend-разработчик", "department": "Разработка"},
    {"email": "employee10@test.com", "full_name": "Иван Богданов", "role": "Employee",
     "position": "Backend-разработчик", "department": "Разработка"},
    {"email": "employee11@test.com", "full_name": "Дарья Воробьёва", "role": "Employee",
     "position": "QA-инженер", "department": "QA"},
    {"email": "employee12@test.com", "full_name": "Роман Фёдоров", "role": "Employee",
     "position": "DevOps-инженер", "department": "DevOps"},
    {"email": "employee13@test.com", "full_name": "Кристина Орлова", "role": "Employee",
     "position": "Fullstack-разработчик", "department": "Разработка"},
]

DEMO_SKILLS = [
    {"category": "Backend", "subcategory": "Языки программирования", "name": "Python"},
    {"category": "Backend", "subcategory": "Фреймворки", "name": "Django"},
    {"category": "Backend", "subcategory": "Фреймворки", "name": "FastAPI"},

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

    {"category": "Управление", "subcategory": "Методологии", "name": "Agile/Scrum"},

    {"category": "Soft Skills", "subcategory": "Языки", "name": "Английский язык"},
]


class Command(BaseCommand):
    help = "Создаёт тестовых пользователей (HR/Manager/Employee), скиллы и проект"

    def handle(self, *args, **options):
        now = timezone.now()

        # --- Пользователи ---
        users = {}
        for data in DEMO_USERS:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "full_name": data["full_name"],
                    "position": data["position"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                assign_role(user, data["role"])
                assign_department(user, data["department"])
                self.stdout.write(self.style.SUCCESS(f"Создан пользователь: {user.email} ({data['role']})"))
            else:
                self.stdout.write(f"Уже существует: {user.email} ({data['role']})")
            users[data["role"]] = user

        # --- Скиллы ---
        skills = []
        for data in DEMO_SKILLS:
            skill, created = Skill.objects.get_or_create(
                name=data["name"],
                defaults={"is_active": True},
            )
            if created:
                attach_skill_to_category(skill, data["category"])
                self.stdout.write(self.style.SUCCESS(f"Создан скилл: {skill.name}"))
            skills.append(skill)

        # --- Скиллы у Manager и Employee ---
        levels = [1, 2, 3]  # Junior, Middle, Senior — по кругу
        for role in ("Manager", "Employee"):
            user = users[role]
            for i, skill in enumerate(skills):
                UserSkill.objects.get_or_create(
                    user=user,
                    skill=skill,
                    defaults={
                        "level": levels[i % len(levels)],
                        "is_approved": True,
                    },
                )
        self.stdout.write(self.style.SUCCESS("Скиллы привязаны к Manager и Employee"))

        # --- Проект ---
        project, created = Project.objects.get_or_create(
            name="SkillMap MVP",
            defaults={
                "description": "Демо-проект для разработки и тестирования",
                "status": "Active",
                "start_date": now,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Создан проект: {project.name}"))

        for role in ("Manager", "Employee"):
            UserProject.objects.get_or_create(
                user=users[role],
                project=project,
                defaults={"joined_at": now},
            )
        self.stdout.write(self.style.SUCCESS("Пользователи привязаны к проекту"))

        self.stdout.write(self.style.SUCCESS("\nГотово. Тестовые аккаунты (пароль у всех: test1234):"))
        for data in DEMO_USERS:
            self.stdout.write(f"  {data['role']:<10} -> {data['email']}")
