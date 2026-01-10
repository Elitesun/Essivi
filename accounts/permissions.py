from rest_framework import permissions


class IsVerifiedUser(permissions.BasePermission):
    """
    Allow access only to verified users.
    """
    message = 'Email verification required. Please verify your email first.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_verified)


class IsAdminUser(permissions.BasePermission):
    """
    Allow access only to admin users.
    """
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'admin')


class IsAgentUser(permissions.BasePermission):
    """
    Allow access only to agent users.
    """
    message = 'Agent access required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'agent')


class IsClientUser(permissions.BasePermission):
    """
    Allow access only to client users.
    """
    message = 'Client access required.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.user_type == 'client')


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allow access if user is the object owner or admin.
    Assumes the model has a 'user' field.
    """
    message = 'You do not have permission to access this resource.'

    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'admin':
            return True
        return obj.user == request.user
