from django.contrib import admin
from djangocalais.models import *


class EntityDetectionInline(admin.TabularInline):
    model = EntityDetection
    extra = 1

class EventDetectionInline(admin.TabularInline):
    model = EventDetection
    extra = 1
    
class CalaisDocumentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'analysis_date')
    exclude = ('social_tags', 'topics')
    inlines = (EntityDetectionInline, EventDetectionInline)
admin.site.register(CalaisDocument, CalaisDocumentAdmin)

class EntityAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'urlhash')
admin.site.register(Entity, EntityAdmin)

class EventFactAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'urlhash')
admin.site.register(EventFact, EventFactAdmin)

class SocialTagAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'urlhash')
admin.site.register(SocialTag, SocialTagAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'urlhash')
admin.site.register(Topic, TopicAdmin)
