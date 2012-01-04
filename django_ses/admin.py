from django.contrib import admin

from .models import SESStat


class SESStatAdmin(admin.ModelAdmin):
    list_display = ('date', 'delivery_attempts', 'bounces', 'complaints',
    				'rejects')

admin.site.register(SESStat, SESStatAdmin)