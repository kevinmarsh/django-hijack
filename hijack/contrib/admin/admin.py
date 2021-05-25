from django.middleware.csrf import get_token
from django.shortcuts import resolve_url
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from hijack.conf import settings


class HijackUserAdminMixin:
    """Add hijack button to changelist admin view."""

    hijack_success_url = None
    """Return URL to which one will be forwarded to after hijacking another user."""

    def get_hijack_user(self, obj):
        """
        Return the user based on the current object.

        This method may be overridden to support hijack keys on related objects.
        """
        return obj

    def get_hijack_success_url(self, request, obj):
        """Return URL to which one will be forwarded to after hijacking another user."""
        success_url = settings.LOGIN_REDIRECT_URL
        if self.hijack_success_url:
            success_url = self.hijack_success_url
        elif hasattr(obj, "get_absolute_url"):
            success_url = obj
        return resolve_url(success_url)

    def hijack_button(self, request, obj):
        """
        Render hijack button.

        Should the user only be a related object we include the username in the button
        to ensure deliberate action. However, the name is omitted in the user admin,
        as the table layout suggests that the button targets the current user.
        """
        user = self.get_hijack_user(obj)
        return render_to_string(
            "hijack/contrib/admin/button.html",
            {
                "request": request,
                "another_user": user,
                "username": str(user),
                "is_user_admin": self.model == type(user),
                "next": self.get_hijack_success_url(request, obj),
            },
        )

    def get_list_display(self, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        def hijack_field(obj):
            return self.hijack_button(request, obj)

        hijack_field.short_description = _("hijack user")

        return [*super().get_list_display(request), hijack_field]

    def response_action(self, request, queryset):
        """
        Handle an admin action. This is called if a request is POSTed to the
        changelist; it returns an HttpResponse if the action was handled, and
        None otherwise.
        """
        if "hijack_user" in request.POST:
            from hijack.views import AcquireUserView
            return AcquireUserView.as_view()(request)
        return super().response_action(request, queryset)
