# presence/permissions.py

from rest_framework import permissions

class IsManager(permissions.BasePermission):
    """
    Permission permettant aux managers de leur département de gérer les demandes de congé.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if hasattr(request.user, 'profile') and request.user.profile.department:
            return request.user.profile.department.manager == request.user
        return False

class IsRecipient(permissions.BasePermission):
    """
    Permet uniquement au destinataire de la notification d'y accéder.
    """

    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user
