from rest_framework import permissions


class PromotionPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_authenticated and (
                request.user.is_staff or request.user.is_supplier
            )
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if obj.user == request.user:
            return view.action in ["retrieve", "update", "partial_update"]

        if request.user.is_salon:
            return view.action == "retrieve"
        return False


class PromotionCarPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_authenticated and (
                request.user.is_staff
                or self._is_promotion_related_to_supplier(request, view)
            )
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if self._is_promotion_related_to_supplier(request, view):
            return view.action in ["retrieve", "update", "partial_update", "destroy"]
        return view.action == "retrieve"

    def _is_promotion_related_to_supplier(self, request, view):
        promotion_id = view.kwargs.get("promotion_pk")
        if promotion_id:
            from .models import Promotion

            try:
                promotion = Promotion.objects.get(id=promotion_id)
                return promotion.cars.filter(
                    suppliercar__supplier__user=request.user
                ).exists()
            except Promotion.DoesNotExist:
                return False
        return False


class PromotionSalonPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_authenticated and (
                request.user.is_staff
                or self._is_promotion_related_to_supplier(request, view)
            )
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if request.user.is_supplier and self._is_promotion_related_to_supplier(
            request, view, obj
        ):
            return view.action in ["retrieve", "update", "partial_update", "destroy"]

        if obj.salon.user == request.user:
            return view.action in ["retrieve", "update", "partial_update"]
        return view.action == "retrieve"

    def _is_promotion_related_to_supplier(self, request, view, obj=None):
        if obj:
            promotion = obj.promotion
        else:
            promotion_id = view.kwargs.get("promotion_pk")
            if promotion_id:
                from .models import Promotion

                try:
                    promotion = Promotion.objects.get(id=promotion_id)
                except Promotion.DoesNotExist:
                    return False
            else:
                return False

        return promotion.cars.filter(suppliercar__supplier__user=request.user).exists()
