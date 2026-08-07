"""/projects/<project_id>/ — HTML-страница проекта, БЕЗ DRF.

Отдельный путь, отдельный рендер — по той же схеме, что и profile_page.py.
Смотреть проект может любой авторизованный, редактировать — только HR/Manager
(та же граница прав, что и в DRF ProjectsListCreateView/ProjectMembersView).

Все POST-запросы этой страницы различаются полем action в форме:
  update_project / add_member / remove_member

GET ?search=... — фильтр списка участников по ФИО (подстрока, без учёта регистра).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import Project, User, UserProject


def _can_edit(user) -> bool:
    """Редактировать проект и управлять участниками может только HR/Manager."""
    return user.has_role("HR", "Manager")


def _handle_update_project(request, project):
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "Название проекта обязательно")
        return

    project.name = name
    project.description = (request.POST.get("description") or "").strip()
    project.status = (request.POST.get("status") or project.status).strip()
    project.save(update_fields=["name", "description", "status"])
    messages.success(request, "Проект обновлён")


def _handle_add_member(request, project):
    user = User.objects.filter(id=request.POST.get("user_id")).first()

    if not user:
        messages.error(request, "Пользователь не найден")
        return

    _, created = UserProject.objects.get_or_create(
        user=user,
        project=project,
        defaults={"joined_at": timezone.now()},
    )
    if created:
        messages.success(request, f"«{user.full_name}» добавлен в проект")
    else:
        messages.error(request, f"«{user.full_name}» уже состоит в проекте")


def _handle_remove_member(request, project):
    deleted, _ = UserProject.objects.filter(
        project=project, user_id=request.POST.get("user_id")
    ).delete()
    if deleted:
        messages.success(request, "Участник удалён из проекта")
    else:
        messages.error(request, "Участник не найден в проекте")


ACTION_HANDLERS = {
    "update_project": _handle_update_project,
    "add_member": _handle_add_member,
    "remove_member": _handle_remove_member,
}


@login_required(login_url="/login/")
def project_page(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("created_by"), id=project_id
    )
    can_edit = _can_edit(request.user)

    if request.method == "POST":
        if not can_edit:
            return HttpResponseForbidden("Недостаточно прав для редактирования этого проекта")

        handler = ACTION_HANDLERS.get(request.POST.get("action"))
        if handler:
            handler(request, project)
        else:
            messages.error(request, "Неизвестное действие")

        return redirect("project-page", project_id=project.id)

    member_links = (
        UserProject.objects.select_related("user")
        .filter(project_id=project.id)
        .order_by("user__full_name")
    )
    member_count = member_links.count()

    search = (request.GET.get("search") or "").strip()
    if search:
        member_links = member_links.filter(user__full_name__icontains=search)

    member_user_ids = [link.user_id for link in member_links]
    available_users_qs = (
        User.objects.filter(is_active=True)
        .exclude(id__in=UserProject.objects.filter(project_id=project.id).values_list("user_id", flat=True))
        .order_by("full_name")
    )

    context = {
        "project": project,
        "owner": project.created_by,
        "can_edit": can_edit,
        "members": [
            {
                "id": link.user.id,
                "full_name": link.user.full_name,
                "position": link.user.position,
                "photo": link.user.photo,
                "joined_at": link.joined_at,
            }
            for link in member_links
        ],
        "member_count": member_count,
        "available_users": available_users_qs,
        "search": search,
    }
    return render(request, "project.html", context)
