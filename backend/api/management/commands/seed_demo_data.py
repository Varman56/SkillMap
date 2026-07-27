from django.core.management.base import BaseCommand
from django.utils import timezone

from api.helpers import assign_department, assign_role, attach_skill_to_category
from api.models import Project, Skill, User, UserProject, UserSkill

DEMO_PASSWORD = "test1234"

DEMO_USERS = [
    {
        "email": "hr@test.com",
        "full_name": "Анна HR",
        "role": "HR",
        "position": "HR-менеджер",
        "department": "HR",
    },
    {
        "email": "manager@test.com",
        "full_name": "Игорь Manager",
        "role": "Manager",
        "position": "Тимлид",
        "department": "Разработка",
    },
    {
        "email": "employee@test.com",
        "full_name": "Пётр Employee",
        "role": "Employee",
        "position": "Backend-разработчик",
        "department": "Разработка",
    },
]

DEMO_SKILLS = [
    {"name": "Python", "category": "Backend"},
    {"name": "Django", "category": "Backend"},
    {"name": "React", "category": "Frontend"},
    {"name": "PostgreSQL", "category": "Database"},
    {"name": "Docker", "category": "DevOps"},
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