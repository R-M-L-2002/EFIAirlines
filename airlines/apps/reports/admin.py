from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from .views import income_report, flight_passengers_report
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from django.db import models
class ReportLink(models.Model):
    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        managed = False 

@admin.register(ReportLink)
class ReportsAdmin(admin.ModelAdmin):
    change_list_template = "admin/reports_links.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('income/', self.admin_site.admin_view(income_report), name='income_report'),
            path('flight/<int:flight_id>/', self.admin_site.admin_view(flight_passengers_report), name='flight_passengers_report'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['reports'] = [
            {
                'name': _('Income Report'),
                'url': reverse('admin:income_report')
            },
            {
                'name': _('Flight Passengers Report'),
                'url': '#'
            }
        ]
        return super().changelist_view(request, extra_context=extra_context)
