from django.contrib import admin
from .models import Income, Expense

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('date', 'source', 'amount', 'user')
    list_filter = ('date', 'source', 'user')
    search_fields = ('source', 'user__username')
    date_hierarchy = 'date'

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'description', 'amount', 'user')
    list_filter = ('date', 'category', 'user')
    search_fields = ('category', 'description', 'user__username')
    date_hierarchy = 'date'