from rest_framework import permissions


class DealPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_staff
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.user.is_salon and obj.salon.user == request.user:
            return view.action == "retrieve"

        if request.user.is_supplier and obj.supplier.user == request.user:
            return view.action == "retrieve"

        if request.user.is_client and obj.client.user == request.user:
            return view.action == "retrieve"

        return False


class IsEmailVerified(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_email_verified
