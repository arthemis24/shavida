# -*- coding: utf-8 -*-

from django.contrib import admin
from me.models import is_content_vendor
from sales.models import SalesConfig, RetailBundle, RetailPrepayment, VODBundle, VODPrepayment, Prepayment, \
    ContentUpdate
from import_export import resources
from import_export.admin import ExportMixin


class RetailPrepaymentResource(resources.ModelResource):

    class Meta:
        model = RetailPrepayment
        skip_unchanged = True
        exclude = ('id',)
        export_id_fields = ('member__username', 'created_on', 'paid_on', 'amount', 'duration', 'balance', 'status')


class VODPrepaymentResource(resources.ModelResource):

    class Meta:
        model = VODPrepayment
        skip_unchanged = True
        exclude = ('id',)
        export_id_fields = ('member__username', 'created_on', 'paid_on', 'amount', 'duration', 'balance', 'status')


class SalesConfigAdmin(admin.ModelAdmin):
    list_display = ('max_inactivity', 'free_trial', 'welcome_offer', 'welcome_offer_duration')

    def save_model(self, request, obj, form, change):
        """
        Do not save more than one SalesConfig object.
        """
        configs_count = SalesConfig.objects.all().count()
        if configs_count >= 1:
            if not obj.id:
                return
        super(SalesConfigAdmin, self).save_model(request, obj, form, change)


class RetailBundleAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'cost', 'comment')
    readonly_fields = ('created_on', )
    ordering = ('cost', )


class VODBundleAdmin(admin.ModelAdmin):
    list_display = ('volume', 'cost', 'duration', 'adult_authorized', 'comment')
    readonly_fields = ('created_on', )
    ordering = ('cost', )


class RetailPrepaymentAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = RetailPrepaymentResource
    list_display = ('member', 'created_on', 'paid_on', 'amount', 'balance', 'duration', 'status')
    list_filter = ('created_on', 'amount', 'status', )
    search_fields = ('member__username',)
    readonly_fields = ('member', 'created_on', 'paid_on', 'status', 'amount', 'balance', 'duration')

    # TODO: Add actions to offer a bundle to a VOD Operator
    # actions = ()


class VODPrepaymentAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = VODPrepaymentResource
    list_display = ('member', 'created_on', 'paid_on', 'amount', 'balance', 'duration', 'status')
    list_filter = ('created_on', 'amount', 'status', )
    search_fields = ('member__username',)
    readonly_fields = ('member', 'created_on', 'paid_on', 'status', 'amount')

    # TODO: Add actions to offer a bundle to a customer
    # actions = ()

    def save_model(self, request, obj, form, change):
        if change:
            if obj.status == Prepayment.CONFIRMED:
                obj.provider = request.user
        super(VODPrepaymentAdmin, self).save_model(request, obj, form, change)


class ContentUpdateAdmin(admin.ModelAdmin, ExportMixin):
    list_display = ('member', 'created_on', 'add_list_size',
                    'add_list_duration', 'delete_list_size', 'cost', 'status')
    readonly_fields = ('created_on', )

    def save_model(self, request, obj, form, change):
        if change:
            if obj.status == ContentUpdate.AUTHORIZED:
                obj.provider = request.user
            elif obj.status == ContentUpdate.DELIVERED:
                return
        super(ContentUpdateAdmin, self).save_model(request, obj, form, change)


admin.site.register(SalesConfig, SalesConfigAdmin)
admin.site.register(VODBundle, VODBundleAdmin)
admin.site.register(VODPrepayment, VODPrepaymentAdmin)

if is_content_vendor():
    admin.site.register(RetailBundle, RetailBundleAdmin)
    admin.site.register(RetailPrepayment, RetailPrepaymentAdmin)
    admin.site.register(ContentUpdate, ContentUpdateAdmin)
