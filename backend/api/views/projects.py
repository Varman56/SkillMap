"""/api/projects — CRUD проектов и управление участниками."""
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
 
from ..models import Project, User, UserProject
from ..permissions import IsHROrManager
from ..serializers import AddMemberRequestSerializer, CreateProjectRequestSerializer
 
 
def _serialize_project_with_members(project: Project) -> dict:
    members = list(project.project_users.select_related("user").all())
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "startDate": project.start_date,
        "endDate": project.end_date,
        "memberCount": len(members),
        "members": [
            {
                "id": m.user.id,
                "fullName": m.user.full_name,
                "position": m.user.position,
                "joinedAt": m.joined_at,
            }
            for m in members
        ],
    }
 
 
class ProjectsListCreateView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        projects = Project.objects.prefetch_related(
            "project_users__user"
        ).order_by("name")
        return Response([_serialize_project_with_members(p) for p in projects])
 
    def post(self, request):
        if not request.user.has_role("HR", "Manager"):
            return Response(
                {"detail": "Только для HR и Manager"},
                status=status.HTTP_403_FORBIDDEN,
            )
 
        serializer = CreateProjectRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        name = (serializer.validated_data.get("name") or "").strip()
        if not name:
            return Response(
                {"error": "Название проекта обязательно"},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        project = Project.objects.create(
            name=name,
            description=(serializer.validated_data.get("description") or "").strip(),
            status=serializer.validated_data.get("status") or "Active",
            start_date=serializer.validated_data.get("startDate"),
            end_date=serializer.validated_data.get("endDate"),
        )
        return Response(
            {"id": project.id, "name": project.name, "status": project.status}
        )
 
 
class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request, project_id: int):
        try:
            project = Project.objects.prefetch_related("project_users__user").get(
                id=project_id
            )
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(_serialize_project_with_members(project))
 
    def put(self, request, project_id: int):
        if not request.user.has_role("HR", "Manager"):
            return Response(
                {"detail": "Только для HR и Manager"},
                status=status.HTTP_403_FORBIDDEN,
            )
 
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
 
        serializer = CreateProjectRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
 
        name = (data.get("name") or "").strip()
        if name:
            project.name = name
        if data.get("description") is not None:
            project.description = data["description"].strip()
        if data.get("status") is not None:
            project.status = data["status"]
        if data.get("startDate") is not None:
            project.start_date = data["startDate"]
        if data.get("endDate") is not None:
            project.end_date = data["endDate"]
 
        project.save()
        return Response(
            {"id": project.id, "name": project.name, "status": project.status}
        )
 
    def delete(self, request, project_id: int):
        if not request.user.has_role("HR", "Manager"):
            return Response(
                {"detail": "Только для HR и Manager"},
                status=status.HTTP_403_FORBIDDEN,
            )
 
        deleted, _ = Project.objects.filter(id=project_id).delete()
        if deleted == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
 
 
class ProjectMembersView(APIView):
    permission_classes = [IsHROrManager]
 
    def post(self, request, project_id: int):
        if not Project.objects.filter(id=project_id).exists():
            return Response(
                {"error": "Проект не найден"}, status=status.HTTP_404_NOT_FOUND
            )
 
        serializer = AddMemberRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
        try:
            user = User.objects.get(id=serializer.validated_data["userId"])
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )
 
        if UserProject.objects.filter(user_id=user.id, project_id=project_id).exists():
            return Response(
                {"error": "Пользователь уже состоит в этом проекте"},
                status=status.HTTP_409_CONFLICT,
            )
 
        try:
            UserProject.objects.create(
                user_id=user.id,
                project_id=project_id,
                joined_at=timezone.now(),
            )
        except IntegrityError:
            return Response(
                {"error": "Пользователь уже состоит в этом проекте"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({"success": True})
 
 
class ProjectMemberDetailView(APIView):
    permission_classes = [IsHROrManager]
 
    def delete(self, request, project_id: int, user_id: int):
        deleted, _ = UserProject.objects.filter(
            user_id=user_id, project_id=project_id
        ).delete()
        if deleted == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
