from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read-only access to everyone (GET, HEAD, OPTIONS methods)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow access to the object only if it's the owner's data
        if hasattr(obj, 'user') and obj.user == request.user:
            return True

        # Allow admin/superuser to perform any actions
        return request.user.is_superuser or request.user.is_staff


class IsDoctorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only doctors to perform certain actions.
    """
    def has_permission(self, request, view):
        # Allow read-only access to everyone (GET, HEAD, OPTIONS methods)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow access only to authenticated doctors
        return request.user.is_authenticated and getattr(request.user, 'is_doctor', False)
