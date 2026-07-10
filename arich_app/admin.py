from django.contrib import admin
from .models import Fishpond, Harvest, FishType, FishpondFishType  # ✅ ADDED FishType, FishpondFishType


# ============================================================================
# 🐟 FISHTYPE ADMIN (NEW)
# ============================================================================
@admin.register(FishType)
class FishTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    search_fields = ['name', 'user__username']
    ordering = ['name']
    readonly_fields = ['created_at']


# ============================================================================
# 🔗 FISHPONDFISHTTYPE ADMIN (NEW)
# ============================================================================
@admin.register(FishpondFishType)
class FishpondFishTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'pond', 'fish_type']
    search_fields = ['pond__name', 'fish_type__name']
    ordering = ['pond__name', 'fish_type__name']


class FishpondFishTypeInline(admin.TabularInline):
    """Inline editing of fish types for a pond"""
    model = FishpondFishType
    extra = 1
    fields = ['fish_type', 'stock_count', 'added_at']
    readonly_fields = ['added_at']


# ============================================================================
# 🐟 FISHPOND ADMIN (UPDATED)
# ============================================================================
@admin.register(Fishpond)
class FishpondAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner', 'size', 'status', 'created_at']
    list_filter = ['status', 'owner', 'created_at']
    search_fields = ['name', 'location', 'owner__username']
    inlines = [FishpondFishTypeInline]  # ✅ ADDED inline for fish types
    readonly_fields = ['created_at', 'updated_at']  # ✅ ADDED updated_at
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'location')
        }),
        ('Details', {
            'fields': ('size', 'status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# 📊 HARVEST ADMIN (UPDATED)
# ============================================================================
@admin.register(Harvest)
class HarvestAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'pond', 'fish_type', 'date', 'quantity', 'created_at']
    list_filter = ['user', 'pond', 'fish_type', 'date']
    search_fields = ['user__username', 'pond__name', 'fish_type__name']  # ✅ UPDATED for FK
    readonly_fields = ['created_at', 'updated_at']  # ✅ ADDED updated_at
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Record Information', {
            'fields': ('pond', 'fish_type')
        }),
        ('Details', {
            'fields': ('date', 'quantity', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )