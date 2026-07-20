"""Модели данных, отображённые на существующую PostgreSQL-схему C# проекта.

Имена таблиц и колонок в PascalCase, как их создавал EF Core, поэтому
используем `db_table` и `db_column` для соответствия.
"""
import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("role", "Employee")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("role", "HR")
        extra_fields.setdefault("full_name", email)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True, db_column="Id")
    public_id = models.UUIDField(
        db_column="PublicId", default=uuid.uuid4, unique=True
    )
    email = models.CharField(db_column="Email", max_length=255, unique=True)
    password = models.CharField(db_column="PasswordHash", max_length=255)
    full_name = models.CharField(db_column="FullName", max_length=255, default="")
    position = models.CharField(db_column="Position", max_length=255, default="")
    department = models.CharField(db_column="Department", max_length=255, default="")
    role = models.CharField(db_column="Role", max_length=50, default="")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    last_login = None

    class Meta:
        db_table = "Users"
        #managed = False

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_staff(self) -> bool:
        return self.role == "HR"

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


class Skill(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    name = models.CharField(db_column="Name", max_length=255)
    category = models.CharField(db_column="Category", max_length=255, default="")
    is_active = models.BooleanField(db_column="IsActive", default=True)

    class Meta:
        db_table = "Skills"
        #managed = False

    def __str__(self) -> str:
        return self.name


class UserSkill(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    user = models.ForeignKey(
        User,
        db_column="UserId",
        on_delete=models.CASCADE,
        related_name="user_skills",
    )
    skill = models.ForeignKey(
        Skill,
        db_column="SkillId",
        on_delete=models.CASCADE,
        related_name="skill_users",
    )
    level = models.CharField(db_column="Level", max_length=50)
    created_at = models.DateTimeField(db_column="CreatedAt")
    updated_at = models.DateTimeField(db_column="UpdatedAt", null=True, blank=True)

    class Meta:
        db_table = "UserSkills"
        #managed = False
        unique_together = (("user", "skill"),)


class Project(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    name = models.CharField(db_column="Name", max_length=255)
    description = models.TextField(db_column="Description", default="")
    status = models.CharField(db_column="Status", max_length=50, default="Active")
    start_date = models.DateTimeField(db_column="StartDate", null=True, blank=True)
    end_date = models.DateTimeField(db_column="EndDate", null=True, blank=True)

    class Meta:
        db_table = "Projects"
        #managed = False

    def __str__(self) -> str:
        return self.name


class UserProject(models.Model):
    id = models.AutoField(primary_key=True, db_column="Id")
    user = models.ForeignKey(
        User,
        db_column="UserId",
        on_delete=models.CASCADE,
        related_name="user_projects",
    )
    project = models.ForeignKey(
        Project,
        db_column="ProjectId",
        on_delete=models.CASCADE,
        related_name="project_users",
    )
    joined_at = models.DateTimeField(db_column="JoinedAt")

    class Meta:
        db_table = "UserProjects"
        #managed = False
        unique_together = (("user", "project"),)
