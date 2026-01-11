from rest_framework import permissions


class SupplierPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if obj.user == request.user:
            return True
        if request.user.is_salon and view.action == "retrieve":
            return True
        return False


class SupplierCarPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ["list", "retrieve"]:
            return request.user.is_authenticated
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if obj.supplier.user == request.user:
            return True
        return view.action in ["retrieve", "list"]
