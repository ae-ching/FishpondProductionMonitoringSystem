from django import forms
from django.core.exceptions import ValidationError
from .models import Harvest, Fishpond, FishType, FishpondFishType
import datetime


# ============================================================================
# FISHPOND FORM (UPDATED)
# ============================================================================
class FishpondForm(forms.ModelForm):
    """Form for creating and editing fishpond records"""
    
    class Meta:
        model = Fishpond
        fields = ['name', 'location', 'size', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Pond A-1',
                'required': True,
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., North Section',
            }),
            'size': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Size in m²',
                'step': '0.01',
            }),
            'status': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Additional notes...',
                'rows': 3,
            }),
        }
    
    def clean_name(self):
        """Validate pond name"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError("Pond name is required")
        
        if len(name) < 3:
            raise ValidationError("Pond name must be at least 3 characters")
        
        if len(name) > 100:
            raise ValidationError("Pond name must be at most 100 characters")
        
        return name
    
    def clean_size(self):
        """Validate pond size"""
        size = self.cleaned_data.get('size')
        
        if size is not None and size < 0:
            raise ValidationError("Pond size cannot be negative")
        
        return size
    
    def save(self, commit=True):
        """Save pond record"""
        instance = super().save(commit=commit)
        return instance


# ============================================================================
# HARVEST FORM (UPDATED)
# ============================================================================
class HarvestForm(forms.ModelForm):
    """Form for creating and editing harvest records with validation"""
    
    class Meta:
        model = Harvest
        fields = ['pond', 'fish_type', 'date', 'quantity', 'notes']
        widgets = {
            'pond': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'fish_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 850',
                'step': '0.01',
                'required': True,
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Optional notes about this harvest...',
                'rows': 2,
            }),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter ponds to only show user's ponds
        if user:
            self.fields['pond'].queryset = Fishpond.objects.filter(
                owner=user
            ).order_by('name')
        
        # Initially, don't show fish types (will be populated via AJAX)
        self.fields['fish_type'].queryset = FishType.objects.none()
        self.fields['fish_type'].empty_label = 'Select a fishpond first'
        
        # If editing, populate fish_type with available options
        if self.instance and self.instance.pk:
            pond = self.instance.pond
            self.fields['fish_type'].queryset = FishType.objects.filter(
                user=user,
                ponds__pond=pond
            ).order_by('name')
        
        # If a pond was selected in a POST request, populate fish types for that pond
        if user:
            selected_pond_id = self.data.get('pond') if self.is_bound else None
            if selected_pond_id:
                pond = Fishpond.objects.filter(owner=user, pk=selected_pond_id).first()
                if pond:
                    self.fields['fish_type'].queryset = FishType.objects.filter(
                        user=user,
                        ponds__pond=pond
                    ).order_by('name')
    
    def clean(self):
        """Validate harvest record"""
        cleaned_data = super().clean()
        pond = cleaned_data.get('pond')
        fish_type = cleaned_data.get('fish_type')
        date = cleaned_data.get('date')
        quantity = cleaned_data.get('quantity')
        
        # Check if fish_type is assigned to selected pond
        if pond and fish_type:
            if not FishpondFishType.objects.filter(
                pond=pond,
                fish_type=fish_type
            ).exists():
                raise ValidationError(
                    f"{fish_type.name} is not assigned to {pond.name}. "
                    f"Please select a valid fish type for this pond."
                )
        
        # Check if date is not in future
        if date and date > datetime.date.today():
            raise ValidationError("Harvest date cannot be in the future")
        
        return cleaned_data
    
    def clean_quantity(self):
        """Validate quantity is positive"""
        quantity = self.cleaned_data.get('quantity')
        
        if quantity is not None and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0")
        
        return quantity