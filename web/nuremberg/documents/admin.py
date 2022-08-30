from django.contrib import admin

from .models import *

class DocumentImageInline(admin.TabularInline):
    model = DocumentImage
    fields = ('page_number', 'physical_page_number', 'image_tag',)
    readonly_fields = fields
    extra = 0
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'image_count')
    inlines = [
        DocumentImageInline
    ]

admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentImage)
