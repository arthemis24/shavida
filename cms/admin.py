# -*- coding: utf-8 -*-
from django.contrib import admin
from cms.models import FlatPage, SiteConfig


class FlatPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'show_banner')
    prepopulated_fields = {"slug": ("title",)}


class SiteConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')

    def save_model(self, request, obj, form, change):
        # Ensures that always one and only one SiteConfig remains with is_active=True
        if obj.is_active:
            for config in SiteConfig.objects.filter(is_active=True):
                config.is_active = False
                super(SiteConfig, config).save()
        else:
            if SiteConfig.objects.filter(is_active=True).count() == 1:
                obj.is_active = True
        super(SiteConfigAdmin, self).save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if SiteConfig.objects.all().count() == 1:
            return
        super(SiteConfigAdmin, self).delete(request, obj)


admin.site.register(FlatPage, FlatPageAdmin)
admin.site.register(SiteConfig, SiteConfigAdmin)
