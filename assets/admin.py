from django.contrib import admin

from .models import *
from guardian.admin import GuardedModelAdmin


class GuardianAbstract(GuardedModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Show only owned property"""
        if request.user.is_superuser:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        kwargs["queryset"] = db_field.related_model.objects.filter(id=request.user.id)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AccountAdmin(GuardianAbstract):
    user_can_access_owned_objects_only = True


admin.site.register(Asset)
admin.site.register(Deal)
admin.site.register(Portfolio)
admin.site.register(Transfer)
admin.site.register(Account, AccountAdmin)
