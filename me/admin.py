# -*- coding: utf-8 -*-

from django.contrib import admin
from django.template.defaultfilters import slugify
from import_export.admin import ExportMixin
from me.models import Profile


class ProfileAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ('member', 'is_vod_operator', )
    list_filter = ('is_vod_operator', )
    readonly_fields = ('member', 'adult_authorized', 'created_on', 'updated_on', )
    search_fields = ('member__username', 'phone', )
    ordering = ('-id', )

    def save_model(self, request, obj, form, change):
        if change:
            database = slugify(obj.member.email).replace('.', '_').replace('-', '_')
            obj.database = database
        super(ProfileAdmin, self).save_model(request, obj, form, change)


admin.site.register(Profile, ProfileAdmin)

