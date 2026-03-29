from django.contrib import admin
from .models import Destination

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('id', 'pName', 'province', 'culture', 'adventure','wildlife','sightseeing','history','tags')
    search_fields = ('pName', 'province')
    list_filter = ('province',)
    ordering = ('id',)

    actions = ['delete_selected']