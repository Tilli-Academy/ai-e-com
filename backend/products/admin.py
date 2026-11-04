"""Admin registration for products — lets staff manage the catalog via /admin/."""

from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    # Auto-fill the slug field from the name as you type in the admin form.
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_available', 'created_at')
    list_filter = ('is_available', 'category')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock', 'is_available')   # quick edits from the list
    prepopulated_fields = {'slug': ('name',)}
