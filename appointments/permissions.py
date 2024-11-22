from rest_framework import permissions

class IsPatientOrDoctorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_patient or request.user.is_doctor or request.user.is_staff)

class CanViewAppointment(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if request.user.is_patient:
            return obj.patient == request.user
        if request.user.is_doctor:
            return obj.doctor == request.user
        return False

class CanEditAppointment(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if request.user.is_doctor:
            return obj.doctor == request.user
        return False
