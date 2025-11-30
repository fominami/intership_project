from rest_framework import permissions


class CarPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        action = view.action
        if action in ["create", "update", "partial_update", "deactivate"]:
            if request.user.is_authenticated and (
                request.user.is_staff or request.user.is_supplier
            ):
                return True
            return False
        return True
