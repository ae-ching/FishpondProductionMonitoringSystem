# arich_project/arich_app/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def get_default_user():
    """Return the first available user as a safe fallback for existing data."""
    user = User.objects.order_by('pk').first()
    return user.pk if user else 1


# ============================================================================
# 🐟 FISHTYPE MODEL - User-specific catalog
# ============================================================================
class FishType(models.Model):
    """User-specific fish species catalog."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=get_default_user
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Fish Types"
        unique_together = [['user', 'name']]


# ============================================================================
# 🐟 FISHPOND MODEL - Updated
# ============================================================================
class Fishpond(models.Model):
    """User's fishpond with assigned fish types"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('empty', 'Empty'),
    ]
    
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='fishponds'
    )
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, blank=True, null=True)
    size = models.FloatField(blank=True, null=True)  # in m²
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ❌ REMOVED: fish_type (use FishpondFishType instead)
    # ❌ REMOVED: stock_count (moved to FishpondFishType)
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    def get_fish_types(self):
        """Get all fish types in this pond"""
        return self.fish_types.all()  # Through FishpondFishType
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
        ]


# ============================================================================
# 🔗 FISHPONDFISHTTYPE MODEL - M2M Relationship (NEW)
# ============================================================================
class FishpondFishType(models.Model):
    """Junction table: links fishponds to fish types (many-to-many)"""
    
    pond = models.ForeignKey(
        Fishpond,
        on_delete=models.CASCADE,
        related_name='fish_types'  # Access via: pond.fish_types.all()
    )
    fish_type = models.ForeignKey(
        FishType,
        on_delete=models.CASCADE,
        related_name='ponds'
    )
    stock_count = models.IntegerField(default=0)  # Initial stocking
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.pond.name} - {self.fish_type.name}"
    
    class Meta:
        # Prevent duplicate assignments
        unique_together = [['pond', 'fish_type']]
        ordering = ['fish_type__name']
        indexes = [
            models.Index(fields=['pond']),
            models.Index(fields=['fish_type']),
        ]
        verbose_name_plural = "Fishpond Fish Types"


# ============================================================================
# 🌾 HARVEST MODEL - Updated
# ============================================================================
class Harvest(models.Model):
    """Harvest record with validation against pond's fish types"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        default=get_default_user
    )
    pond = models.ForeignKey(
        Fishpond,
        on_delete=models.CASCADE,
        related_name='harvests'
    )
    fish_type = models.ForeignKey(
        FishType,
        on_delete=models.CASCADE
    )
    date = models.DateField()
    quantity = models.FloatField()  # in kg
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.fish_type.name} - {self.quantity} kg ({self.date})"
    
    def clean(self):
        """Validate that fish_type is assigned to this pond"""
        if self.pond and self.fish_type:
            if not FishpondFishType.objects.filter(
                pond=self.pond,
                fish_type=self.fish_type
            ).exists():
                raise ValidationError(
                    f"{self.fish_type.name} is not assigned to pond {self.pond.name}"
                )
    
    def save(self, *args, **kwargs):
        """Call validation before saving"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['pond', '-date']),
            models.Index(fields=['fish_type', '-date']),
        ]