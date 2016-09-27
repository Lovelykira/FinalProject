from django.contrib import admin

from .models import Tasks, Results


class TasksAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'site',)


class ResultsAdmin(admin.ModelAdmin):
    list_display = ('task_keyword', 'img')

    def task_keyword(self, obj):
        return obj.task.keyword


admin.site.register(Tasks, TasksAdmin)
admin.site.register(Results, ResultsAdmin)
