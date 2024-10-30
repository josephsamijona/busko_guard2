# presence/permissions.py

from rest_framework import permissions

class IsManager(permissions.BasePermission):
    """
    Permission permettant aux managers de leur département de gérer les règles de présence et d'accès.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.department:
            return request.user.profile.department.manager == request.user
        return False
