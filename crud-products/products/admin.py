# products/admin.py
from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price",
                    "stock", "created_at", "updated_at", "owner")
    search_fields = ("name", "category", "description")
    list_filter = ("category",)
    ordering = ("-created_at",)
