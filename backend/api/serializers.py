"""Сериализаторы DRF — DTO между моделями и JSON."""
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
 
from .helpers import skill_category_name
from .models import Skill, User
 
 
class UserPublicSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    fullName = serializers.CharField(source="full_name", read_only=True)
    department = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
 
    class Meta:
        model = User
        fields = ["id", "email", "fullName", "position", "department", "role"]
 
    def get_department(self, obj) -> str:
        return obj.primary_department
 
    def get_role(self, obj) -> str:
        return obj.primary_role
 
 
class CreateUserRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages={"required": "Email обязателен"})
    password = serializers.CharField(min_length=3)
    confirmPassword = serializers.CharField()
    fullName = serializers.CharField()
    position = serializers.CharField(required=False, allow_blank=True, default="")
    department = serializers.CharField(required=False, allow_blank=True, default="")
    role = serializers.CharField()
 
    def validate(self, attrs):
        if attrs["password"] != attrs["confirmPassword"]:
            raise serializers.ValidationError({"message": "Пароли не совпадают"})
        return attrs
 
 
class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    rememberMe = serializers.BooleanField(required=False, default=False)
 
 
class SkillmapTokens(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

 
def issue_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    refresh["email"] = user.email
    refresh["role"] = user.primary_role
    refresh["full_name"] = user.full_name
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
 
 
class SkillSerializer(serializers.ModelSerializer):
    Id = serializers.IntegerField(source="id", read_only=True)
    Name = serializers.CharField(source="name", read_only=True)
    Category = serializers.SerializerMethodField()
    IsActive = serializers.BooleanField(source="is_active", read_only=True)
 
    class Meta:
        model = Skill
        fields = ["Id", "Name", "Category", "IsActive"]
 
    def get_Category(self, obj) -> str:
        return skill_category_name(obj)
 
 
class SkillShortSerializer(serializers.ModelSerializer):
    Id = serializers.IntegerField(source="id", read_only=True)
    Name = serializers.CharField(source="name", read_only=True)
    Category = serializers.SerializerMethodField()
 
    class Meta:
        model = Skill
        fields = ["Id", "Name", "Category"]
 
    def get_Category(self, obj) -> str:
        return skill_category_name(obj)
 
 
class CreateSkillRequestSerializer(serializers.Serializer):
    name = serializers.CharField(error_messages={"required": "Название навыка обязательно"})
    category = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
 
 
class AddUserSkillRequestSerializer(serializers.Serializer):
    skillId = serializers.IntegerField()
    level = serializers.IntegerField(min_value=1, max_value=4)
 
 
class UpdateSkillLevelRequestSerializer(serializers.Serializer):
    level = serializers.IntegerField(min_value=1, max_value=4)
 
 
class CreateProjectRequestSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    startDate = serializers.DateTimeField(required=False, allow_null=True)
    endDate = serializers.DateTimeField(required=False, allow_null=True)
 
 
class AddMemberRequestSerializer(serializers.Serializer):
    userId = serializers.IntegerField()
 
 
# ------------------------------------------------------------------
# Ниже — сериализаторы только для документации (OpenAPI/Swagger).
# Views по-прежнему возвращают обычные dict через Response(...), но
# drf-spectacular использует эти классы, чтобы нарисовать точную схему
# ответа вместо "unable to guess serializer".
# ------------------------------------------------------------------
 
class SuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
 
 
class ErrorResponseSerializer(serializers.Serializer):
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    detail = serializers.CharField(required=False)
 
 
class LoginResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    user = UserPublicSerializer()
    tokens = SkillmapTokens()
 
 
class LogoutRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)
 
 
class YandexClaimRequestSerializer(serializers.Serializer):
    ticket = serializers.CharField()
 
 
class YandexClaimResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    user = UserPublicSerializer()
    tokens = SkillmapTokens()
 
 
class ProjectMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fullName = serializers.CharField()
    position = serializers.CharField(allow_null=True, required=False)
    joinedAt = serializers.DateTimeField()
 
 
class ProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True, required=False)
    status = serializers.CharField()
    startDate = serializers.DateTimeField(allow_null=True, required=False)
    endDate = serializers.DateTimeField(allow_null=True, required=False)
    memberCount = serializers.IntegerField()
    members = ProjectMemberSerializer(many=True)
 
 
class ProjectCreatedSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    status = serializers.CharField()
 
 
class MyDashboardSkillSerializer(serializers.Serializer):
    userSkillId = serializers.IntegerField()
    skillId = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    level = serializers.CharField()
    isApproved = serializers.BooleanField()
    createdAt = serializers.DateTimeField()
    updatedAt = serializers.DateTimeField(allow_null=True)
 
 
class MyDashboardProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True, required=False)
    status = serializers.CharField()
    startDate = serializers.DateTimeField(allow_null=True, required=False)
    endDate = serializers.DateTimeField(allow_null=True, required=False)
    joinedAt = serializers.DateTimeField()
 
 
class MyDashboardStatsSerializer(serializers.Serializer):
    totalSkills = serializers.IntegerField()
    seniorCount = serializers.IntegerField()
    middleCount = serializers.IntegerField()
    juniorCount = serializers.IntegerField()
 
 
class MyDashboardResponseSerializer(serializers.Serializer):
    user = UserPublicSerializer()
    stats = MyDashboardStatsSerializer()
    skills = MyDashboardSkillSerializer(many=True)
    projects = MyDashboardProjectSerializer(many=True)
 
 
class UserSkillActionResponseSerializer(serializers.Serializer):
    Id = serializers.IntegerField()
    SkillId = serializers.IntegerField()
    Name = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    Category = serializers.CharField(required=False)
    category = serializers.CharField(required=False)
    Level = serializers.CharField()
    IsApproved = serializers.BooleanField(required=False)
    CreatedAt = serializers.DateTimeField()
    UpdatedAt = serializers.DateTimeField(allow_null=True)
 
 
class MatrixSkillRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
 
 
class MatrixEmployeeSkillSerializer(serializers.Serializer):
    skillId = serializers.IntegerField()
    skillName = serializers.CharField()
    skillCategory = serializers.CharField()
    level = serializers.CharField()
    createdAt = serializers.DateTimeField()
    updatedAt = serializers.DateTimeField(allow_null=True)
 
 
class MatrixEmployeeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fullName = serializers.CharField()
    position = serializers.CharField(allow_null=True, required=False)
    department = serializers.CharField()
    role = serializers.CharField()
    isIntern = serializers.BooleanField()
    skills = MatrixEmployeeSkillSerializer(many=True)
 
 
class MatrixStatsSerializer(serializers.Serializer):
    totalEmployees = serializers.IntegerField()
    uniqueSkills = serializers.IntegerField()
    experts = serializers.IntegerField()
    interns = serializers.IntegerField()
    seniorCount = serializers.IntegerField()
    middleCount = serializers.IntegerField()
    juniorCount = serializers.IntegerField()
 
 
class MatrixResponseSerializer(serializers.Serializer):
    stats = MatrixStatsSerializer()
    departments = serializers.ListField(child=serializers.CharField())
    skills = MatrixSkillRefSerializer(many=True)
    employees = MatrixEmployeeSerializer(many=True)
 
 
class PublicProfileUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    fullName = serializers.CharField()
    position = serializers.CharField(allow_null=True, required=False)
    department = serializers.CharField()
    role = serializers.CharField()
 
 
class PublicProfileSkillSerializer(serializers.Serializer):
    userSkillId = serializers.IntegerField()
    skillId = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()
    level = serializers.CharField()
    createdAt = serializers.DateTimeField()
    updatedAt = serializers.DateTimeField(allow_null=True)
 
 
class PublicProfileProjectSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True, required=False)
    status = serializers.CharField()
    startDate = serializers.DateTimeField(allow_null=True, required=False)
    endDate = serializers.DateTimeField(allow_null=True, required=False)
    joinedAt = serializers.DateTimeField()
 
 
class PublicProfileResponseSerializer(serializers.Serializer):
    user = PublicProfileUserSerializer()
    skills = PublicProfileSkillSerializer(many=True)
    projects = PublicProfileProjectSerializer(many=True)
 
 
class AskResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    fullName = serializers.CharField()
    position = serializers.CharField(allow_null=True, required=False)
    department = serializers.CharField()
    level = serializers.CharField()
    matchingSkills = serializers.ListField(child=serializers.CharField())