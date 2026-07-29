
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator
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
        extra_fields.setdefault("full_name", email)
        return self._create_user(email, password, **extra_fields)
 
    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("full_name", email)
        extra_fields.setdefault("is_active", True)
        user = self._create_user(email, password, **extra_fields)
        hr_role, _ = Role.objects.get_or_create(name="HR")
        UserRole.objects.get_or_create(user=user, role=hr_role)
        return user
 
 
class User(AbstractBaseUser):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    photo = models.TextField(null=True, blank=True)  # путь к файлу, ограничение 5MB проверяется в коде
    resume = models.TextField(null=True, blank=True)  # путь к резюме, формат PDF/DOCX проверяется в коде
    is_active = models.BooleanField(default=False)
    is_intern = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
 
    departments = models.ManyToManyField(
        "Department", through="DepartmentUser", related_name="users"
    )
    roles = models.ManyToManyField(
        "Role", through="UserRole", related_name="users"
    )
 
    objects = UserManager()
 
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]
 
    last_login = None
 
    class Meta:
        db_table = "app_user"
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
    def is_staff(self) -> bool:
        return self.has_role("HR")
 
    def has_role(self, *roles: str) -> bool:
        return self.roles.filter(name__in=roles).exists()
 
    @property
    def primary_role(self) -> str:
        """Имя первой роли — для мест, где старому коду нужна одна строка."""
        role = self.roles.first()
        return role.name if role else ""
 
    @property
    def primary_department(self) -> str:
        """Имя первого департамента — для мест, где старому коду нужна одна строка."""
        department = self.departments.first()
        return department.name if department else ""
 
 
class Department(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
 
    class Meta:
        db_table = "department"
        #managed = False
 
    def __str__(self) -> str:
        return self.name
 
 
class DepartmentUser(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="department_links",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.RESTRICT,
        related_name="user_links",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = "department_user"
        #managed = False
        unique_together = (("user", "department"),)
 
 
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
 
    class Meta:
        db_table = "role"
        #managed = False
 
    def __str__(self) -> str:
        return self.name
 
 
class UserRole(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="role_links",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name="user_links",
    )
 
    class Meta:
        db_table = "user_role"
        #managed = False
        unique_together = (("user", "role"),)
 
 
class Category(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
 
    subcategories = models.ManyToManyField(
        "Subcategory", through="CategorySubcategory", related_name="categories"
    )
 
    class Meta:
        db_table = "category"
        #managed = False
 
    def __str__(self) -> str:
        return self.name
 
 
class Subcategory(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
 
    skills = models.ManyToManyField(
        "Skill", through="SubcategorySkill", related_name="subcategories"
    )
 
    class Meta:
        db_table = "subcategory"
        #managed = False
 
    def __str__(self) -> str:
        return self.name
 
 
class CategorySubcategory(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name="subcategory_links",
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.RESTRICT,
        related_name="category_links",
    )
 
    class Meta:
        db_table = "category_subcategory"
        #managed = False
        unique_together = (("category", "subcategory"),)
 
 
class Skill(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
 
    class Meta:
        db_table = "skill"
        #managed = False
 
    def __str__(self) -> str:
        return self.name
 
 
class SubcategorySkill(models.Model):
    id = models.AutoField(primary_key=True)
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.RESTRICT,
        related_name="skill_links",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.RESTRICT,
        related_name="subcategory_links",
    )
 
    class Meta:
        db_table = "subcategory_skill"
        #managed = False
        unique_together = (("subcategory", "skill"),)
 
 
class UserSkill(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.RESTRICT,
        related_name="skill_users",
    )
    level = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        db_table = "user_skill"
        #managed = False
        unique_together = (("user", "skill"),)
 
 
class Project(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=50, default="Active")
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        db_table = "project"
        #managed = False
 
    def __str__(self) -> str:
        return self.name
 
 
class UserProject(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_projects",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.RESTRICT,
        related_name="project_users",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = "user_project"
        #managed = False
        unique_together = (("user", "project"),)
 
 
class UserComment(models.Model):
    """Комментарии руководителей юзерам."""
 
    id = models.AutoField(primary_key=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="written_comments",
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_comments",
    )
    text = models.TextField()
    level = models.SmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        db_table = "user_comment"
        #managed = False
 
    def __str__(self) -> str:
        return f"{self.author_id} -> {self.target_user_id}: {self.text[:30]}"