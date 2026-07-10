# arich_project/arich_app/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Fishpond, Harvest, FishType, FishpondFishType  # ✅ ADDED FishType, FishpondFishType
from .forms import HarvestForm, FishpondForm

from django.http import JsonResponse
import json

from rest_framework.response import Response

# ✅ Import prediction service
from .prediction_service import predict_harvest, PredictionError, InsufficientDataError, InvalidPondError, InvalidFishTypeError

from .serializers import (
    FishpondSerializer,
    HarvestSerializer,
    FishTypeSerializer,
)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated




def normalize_fish_type_name(name):
    """Normalize fish type names before saving."""
    if not name:
        return ""

    cleaned_name = " ".join(name.strip().split())
    if not cleaned_name:
        return ""

    return " ".join(part.capitalize() for part in cleaned_name.replace('_', ' ').split())


@login_required(login_url='login')
def home(request):
    from collections import defaultdict
    
    user_ponds = Fishpond.objects.filter(owner=request.user)
    user_harvests = Harvest.objects.filter(pond__owner=request.user).order_by('-date')
    
    # Calculate statistics
    total_harvest = sum(h.quantity for h in user_harvests) if user_harvests else 0
    total_ponds = user_ponds.count()
    active_ponds = user_ponds.filter(status='active').count()
    
    # Get most recent harvest for KPI card and latest 5 for activity table
    latest_harvest = user_harvests.first()
    latest_harvests = list(user_harvests[:5])
    
    # Prepare data for charts
    # 1. Monthly harvest trend by fish type
    all_months = set()
    all_fish_types = set()
    monthly_fish_data = defaultdict(lambda: defaultdict(float))
    
    for harvest in user_harvests:
        month_key = harvest.date.strftime('%b')
        all_months.add(month_key)
        all_fish_types.add(harvest.fish_type)
        monthly_fish_data[harvest.fish_type][month_key] += float(harvest.quantity)
    
    # Sort months properly
    months = sorted(list(all_months), key=lambda x: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(x) if x in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] else 12)
    
    # Create datasets for each fish type
    fish_types = sorted(
        list(all_fish_types),
        key=lambda fish_type: getattr(fish_type, 'name', '') or ''
    )
    harvest_by_fish_type = {}
    for fish_type in fish_types:
        harvest_by_fish_type[fish_type] = [monthly_fish_data[fish_type].get(month, 0) for month in months]
    
    # 2. Fish species distribution
    species_data = defaultdict(float)
    for harvest in user_harvests:
        species_data[harvest.fish_type] += float(harvest.quantity)
    
    species = list(species_data.keys())
    species_quantities = list(species_data.values())
    species_names = [getattr(s, 'name', str(s)) for s in species]

    # Convert model objects to primitive types for JSON/JS consumption
    fish_type_names = [getattr(ft, 'name', str(ft)) for ft in fish_types]
    harvest_by_fish_type_serializable = {getattr(ft, 'name', str(ft)): harvest_by_fish_type[ft] for ft in fish_types}

    context = {
        'total_harvest': total_harvest or 0,
        'total_ponds': total_ponds or 0,
        'active_ponds': active_ponds or 0,
        'latest_harvest': latest_harvest,
        'latest_harvests': latest_harvests or [],
        'months': months or [],
        'fish_types': fish_types or [],
        'harvest_by_fish_type': harvest_by_fish_type or {},
        'species': species or [],
        'species_quantities': species_quantities or [],
        # JSON-safe strings for templates
        'months_json': json.dumps(months or []),
        'fish_types_json': json.dumps(fish_type_names),
        'harvest_by_fish_type_json': json.dumps(harvest_by_fish_type_serializable),
        'species_json': json.dumps(species_names or []),
        'species_quantities_json': json.dumps(species_quantities or []),
    }
    
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def dashboard(request):
    from collections import defaultdict
    
    user_ponds = Fishpond.objects.filter(owner=request.user)
    user_harvests = Harvest.objects.filter(pond__owner=request.user).order_by('-date')
    
    # Calculate statistics
    total_harvest = sum(h.quantity for h in user_harvests) if user_harvests else 0
    total_ponds = user_ponds.count()
    active_ponds = user_ponds.filter(status='active').count()

    # Get most recent harvest for KPI card
    latest_harvest = user_harvests.first()
    # Get latest 5 harvests for recent activity table
    latest_harvests = user_harvests[:5]
        
    # Prepare data for charts
    # 1. Monthly harvest trend by fish type
    all_months = set()
    all_fish_types = set()
    monthly_fish_data = defaultdict(lambda: defaultdict(float))
    
    for harvest in user_harvests:
        month_key = harvest.date.strftime('%b')
        all_months.add(month_key)
        all_fish_types.add(harvest.fish_type)
        monthly_fish_data[harvest.fish_type][month_key] += float(harvest.quantity)
    
    # Sort months properly
    months = sorted(list(all_months), key=lambda x: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].index(x) if x in ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'] else 12)
    
    # Create datasets for each fish type
    fish_types = sorted(
        list(all_fish_types),
        key=lambda fish_type: getattr(fish_type, 'name', '') or ''
    )
    harvest_by_fish_type = {}
    for fish_type in fish_types:
        harvest_by_fish_type[fish_type] = [monthly_fish_data[fish_type].get(month, 0) for month in months]
    
    # 2. Fish species distribution
    species_data = defaultdict(float)
    for harvest in user_harvests:
        species_data[harvest.fish_type] += float(harvest.quantity)
    
    species = list(species_data.keys())
    species_quantities = list(species_data.values())

    # Convert model objects to primitive types for JSON/JS consumption
    fish_type_names = [getattr(ft, 'name', str(ft)) for ft in fish_types]
    harvest_by_fish_type_serializable = {getattr(ft, 'name', str(ft)): harvest_by_fish_type[ft] for ft in fish_types}
    species_names = [getattr(s, 'name', str(s)) for s in species]

    context = {
        'total_harvest': total_harvest or 0,
        'total_ponds': total_ponds or 0,
        'active_ponds': active_ponds or 0,
        'latest_harvest': latest_harvest,
        'latest_harvests': latest_harvests or [],
        'months': months or [],
        'fish_types': fish_types or [],
        'harvest_by_fish_type': harvest_by_fish_type or {},
        'species': species or [],
        'species_quantities': species_quantities or [],
        # JSON-safe strings for templates
        'months_json': json.dumps(months or []),
        'fish_types_json': json.dumps(fish_type_names),
        'harvest_by_fish_type_json': json.dumps(harvest_by_fish_type_serializable),
        'species_json': json.dumps(species_names or []),
        'species_quantities_json': json.dumps(species_quantities or []),
    }
    
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def ponds(request):
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    ponds = Fishpond.objects.filter(owner=request.user)

    if search:
        ponds = ponds.filter(name__icontains=search)

    if status:
        ponds = ponds.filter(status=status)

    total_ponds = Fishpond.objects.filter(owner=request.user).count()
    active_count = Fishpond.objects.filter(owner=request.user, status='active').count()
    harvesting_count = Fishpond.objects.filter(owner=request.user, status='harvesting').count()
    maintenance_count = Fishpond.objects.filter(owner=request.user, status='maintenance').count()

    paginator = Paginator(ponds, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    ponds = page_obj

    form = FishpondForm()  # ✅ Create blank form for modal

    return render(request, 'ponds.html', {
        'ponds': ponds,
        'form': form,
        'search': search,
        'status': status,
        'total_ponds': total_ponds,
        'active_count': active_count,
        'harvesting_count': harvesting_count,
        'maintenance_count': maintenance_count,
    })

@login_required(login_url='login')
def harvest(request):
    search = request.GET.get('search', '')
    pond_id = request.GET.get('pond', '')
    fish_id = request.GET.get('fish', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    harvests = Harvest.objects.filter(pond__owner=request.user).order_by('-date')

    if search:
        harvests = harvests.filter(
            Q(pond__name__icontains=search) |
            Q(fish_type__name__icontains=search) |
            Q(notes__icontains=search)
        )

    if pond_id:
        harvests = harvests.filter(pond_id=pond_id)

    if fish_id:
        harvests = harvests.filter(fish_type_id=fish_id)

    if start_date:
        harvests = harvests.filter(date__gte=start_date)

    if end_date:
        harvests = harvests.filter(date__lte=end_date)

    ponds = Fishpond.objects.filter(owner=request.user)
    fish_types = FishType.objects.filter(user=request.user).order_by('name')
    form = HarvestForm(user=request.user)

    paginator = Paginator(harvests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate harvest statistics
    total_harvested = sum(h.quantity for h in harvests) if harvests else 0
    total_records = harvests.count()
    avg_harvest = total_harvested / total_records if total_records > 0 else 0
    fish_types_count = len(set(h.fish_type for h in harvests))
    
    context = {
        'harvests': page_obj,
        'ponds': ponds,
        'fish_types': fish_types,
        'form': form,
        'total_harvested': total_harvested,
        'total_records': total_records,
        'avg_harvest': avg_harvest,
        'fish_types_count': fish_types_count,
        'search': search,
        'selected_pond': pond_id,
        'selected_fish': fish_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'harvest.html', context)


@login_required(login_url='login')
def create_harvest(request):
    if request.method == "POST":
        form = HarvestForm(request.POST, user=request.user)
        if form.is_valid():
            pond = form.cleaned_data['pond']
            fish_type = form.cleaned_data['fish_type']
            
            # ✅ VALIDATION: Check if fish_type is in pond
            if not FishpondFishType.objects.filter(
                pond=pond, fish_type=fish_type
            ).exists():
                messages.error(request, 
                    f"{fish_type.name} is not assigned to {pond.name}")
                return redirect('harvest')
            
            if pond.owner == request.user:
                harvest = form.save(commit=False)
                harvest.user = request.user
                harvest.save()
                messages.success(request, f"Harvest record for {harvest.fish_type.name} added successfully!")  # ✅ USE .name
                return redirect('harvest')
            else:
                messages.error(request, "You don't have permission to add harvest to this pond.")
    else:
        form = HarvestForm(user=request.user)
    
    ponds = Fishpond.objects.filter(owner=request.user)
    return render(request, 'harvest.html', {'form': form, 'ponds': ponds})


@login_required(login_url='login')
def analytics(request):
    from django.db.models import Sum
    from collections import defaultdict
    from datetime import datetime
    
    user_ponds = Fishpond.objects.filter(owner=request.user)
    user_harvests = Harvest.objects.filter(pond__owner=request.user).order_by('date')
    
    # Prepare data for charts
    # 1. Monthly harvest trend
    monthly_data = defaultdict(float)
    for harvest in user_harvests:
        month_key = harvest.date.strftime('%b %Y')
        monthly_data[month_key] += float(harvest.quantity)
    
    months = sorted(list(monthly_data.keys()))
    monthly_quantities = [monthly_data[month] for month in months]
    
    # 2. Harvest by pond
    pond_data = defaultdict(float)
    for harvest in user_harvests:
        pond_data[harvest.pond.name] += float(harvest.quantity)
    
    pond_names = list(pond_data.keys())
    pond_quantities = list(pond_data.values())
    
    # 3. Fish species distribution
    species_data = defaultdict(float)
    for harvest in user_harvests:
        species_data[harvest.fish_type.name] += float(harvest.quantity)  # ✅ USE .name
    
    species = list(species_data.keys())
    species_quantities = list(species_data.values())
    
    context = {
        'ponds': user_ponds,
        'harvests': user_harvests,
        'months': months,
        'monthly_quantities': monthly_quantities,
        'pond_names': pond_names,
        'pond_quantities': pond_quantities,
        'species': species,
        'species_quantities': species_quantities,
    }
    
    return render(request, 'analytics.html', context)


@login_required(login_url='login')
def prediction(request):
    # Get user's ponds and fish types for dropdown population
    ponds = Fishpond.objects.filter(owner=request.user).order_by('name')
    fish_types = FishType.objects.filter(user=request.user).order_by('name')
    user_harvests = Harvest.objects.filter(pond__owner=request.user).select_related('pond', 'fish_type').order_by('date', 'id')

    harvest_history = [
        {
            'pond_id': harvest.pond_id,
            'fish_type_id': harvest.fish_type_id,
            'date': harvest.date.isoformat(),
            'quantity': float(harvest.quantity),
            'label': harvest.date.strftime('%b %Y'),
        }
        for harvest in user_harvests
    ]

    context = {
        'ponds': ponds,
        'fish_types': fish_types,
        'harvest_history_json': json.dumps(harvest_history),
    }

    return render(request, 'prediction.html', context)



@login_required(login_url='login')
def settings(request):
    return render(request, 'settings.html')


@login_required(login_url='login')
def create_fishpond(request):
    if request.method == "POST":
        form = FishpondForm(request.POST)
        if form.is_valid():
            fishpond = form.save(commit=False)
            fishpond.owner = request.user
            fishpond.save()

            fish_type_names = request.POST.getlist('fish_type_names[]')
            normalized_names = []
            seen_names = set()

            for raw_name in fish_type_names:
                normalized_name = normalize_fish_type_name(raw_name)
                if normalized_name and normalized_name.lower() not in seen_names:
                    normalized_names.append(normalized_name)
                    seen_names.add(normalized_name.lower())

            if not normalized_names:
                messages.error(request, "Please enter at least one fish type")
                return render(request, 'ponds.html', {'form': form, 'ponds': Fishpond.objects.filter(owner=request.user)})

            for fish_type_name in normalized_names:
                fish_type, created = FishType.objects.get_or_create(
                    user=request.user,
                    name=fish_type_name
                )
                FishpondFishType.objects.get_or_create(
                    pond=fishpond,
                    fish_type=fish_type
                )

            messages.success(request, f"Fishpond '{fishpond.name}' created successfully with fish types!")
            return redirect("ponds")
        else:
            # Show form errors as messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = FishpondForm()
    
    ponds = Fishpond.objects.filter(owner=request.user)
    all_fish_types = FishType.objects.all()  # ✅ PASS to template
    return render(request, 'ponds.html', {'form': form, 'ponds': ponds, 'all_fish_types': all_fish_types})


@login_required(login_url='login')
def edit_fishpond(request, pk):
    pond = get_object_or_404(Fishpond, pk=pk, owner=request.user)

    if request.method == "POST":
        form = FishpondForm(request.POST, instance=pond)
        if form.is_valid():
            updated_pond = form.save()
            messages.success(request, f"Fishpond '{updated_pond.name}' updated successfully!")
            return redirect('ponds')
        else:
            # Show form errors as messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = FishpondForm(instance=pond)

    is_modal_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('modal') == '1'
    return render(request, 'edit_fishpond.html', {'pond': pond, 'form': form, 'modal': is_modal_request})


@login_required(login_url='login')
def delete_fishpond(request, pk):
    pond = get_object_or_404(Fishpond, pk=pk, owner=request.user)

    if request.method == 'POST':
        pond.delete()
        return redirect('ponds')

    is_modal_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('modal') == '1'
    return render(request, 'confirm_delete.html', {'pond': pond, 'modal': is_modal_request})


# ============================================================================
# ✅ NEW AJAX ENDPOINT: Get fish types for a pond
# ============================================================================
@login_required(login_url='login')
def get_pond_fish_types(request, pond_id):
    """AJAX endpoint: return fish types for a pond"""
    pond = get_object_or_404(Fishpond, pk=pond_id, owner=request.user)
    
    fish_types = FishType.objects.filter(
        user=request.user,
        ponds__pond=pond
    ).order_by('name')
    
    data = [
        {
            'id': ft.id,
            'name': ft.name
        }
        for ft in fish_types
    ]
    
    return JsonResponse({'fish_types': data})


@login_required(login_url='login')
def edit_harvest(request, pk):
    harvest = get_object_or_404(Harvest, pk=pk, pond__owner=request.user)
    
    if request.method == 'POST':
        form = HarvestForm(request.POST, instance=harvest, user=request.user)
        if form.is_valid():
            if form.cleaned_data['pond'].owner == request.user:
                updated_harvest = form.save()
                # Check if AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Harvest record updated successfully'})
                else:
                    messages.success(request, f"Harvest record for {updated_harvest.fish_type.name} updated successfully!")  # ✅ USE .name
                    return redirect('harvest')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Permission denied'})
                else:
                    messages.error(request, "You don't have permission to edit this harvest.")
    else:
        form = HarvestForm(instance=harvest, user=request.user)
    
    ponds = Fishpond.objects.filter(owner=request.user)
    return render(request, 'harvest.html', {'form': form, 'ponds': ponds})


@login_required(login_url='login')
def delete_harvest(request, pk):
    harvest = get_object_or_404(Harvest, pk=pk, pond__owner=request.user)

    if request.method == 'POST':
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            harvest.delete()
            return JsonResponse({'success': True, 'message': 'Harvest record deleted successfully'})
        else:
            harvest.delete()
            messages.success(request, "Harvest record deleted successfully!")
            return redirect('harvest')

    is_modal_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('modal') == '1'
    return render(request, 'confirm_delete_harvest.html', {'harvest': harvest, 'modal': is_modal_request})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email    = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid email or password'})

    # Ensure a CSRF cookie/token is set on initial GET so the form token matches
    get_token(request)
    return render(request, 'login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        email      = request.POST.get('email')
        password   = request.POST.get('password')
        terms      = request.POST.get('terms')

        if not all([first_name, last_name, email, password]):
            return render(request, 'signup.html', {'error': 'All fields are required'})

        if len(password) < 8:
            return render(request, 'signup.html', {'error': 'Password must be at least 8 characters'})

        if not terms:
            return render(request, 'signup.html', {'error': 'You must agree to the Terms of Service'})

        username          = email.split('@')[0]
        original_username = username
        counter           = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': 'Email already registered'})

        try:
            user = User.objects.create_user(
                username   = username,
                email      = email,
                password   = password,
                first_name = first_name,
                last_name  = last_name,
            )
            login(request, user)
            return redirect('home')

        except IntegrityError:
            return render(request, 'signup.html', {'error': 'An error occurred during signup. Please try again.'})

    return render(request, 'signup.html')


def toast_test(request):
    """Test view for toast notifications"""
    messages.success(request, "This is a success message!")
    return render(request, 'toast_test.html')

# ============================================================================
# 🌐 API - Fishpond List
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fishpond_api(request):
    fishponds = Fishpond.objects.filter(owner=request.user)
    serializer = FishpondSerializer(fishponds, many=True)
    return Response(serializer.data)

# ============================================================================
# 🌐 API - Harvest List
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def harvest_api(request):
    harvests = Harvest.objects.filter(user=request.user)
    serializer = HarvestSerializer(harvests, many=True)
    return Response(serializer.data)

# ============================================================================
# 🌐 API - Fish Type List
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fishtype_api(request):
    fish_types = FishType.objects.filter(user=request.user)
    serializer = FishTypeSerializer(fish_types, many=True)
    return Response(serializer.data)


# ============================================================================
# 🎯 API - Generate Harvest Prediction
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_harvest_api(request):
    """
    API endpoint for generating harvest predictions.
    
    Expected POST data:
    {
        "pond_id": 1,
        "fish_type_id": 2
    }
    
    Returns:
    {
        "success": true/false,
        "prediction": 15641.49,  (kg, only if success=true)
        "trend": "Increasing",   (only if success=true)
        "previous_harvest": 1150, (kg, only if success=true)
        "history_count": 5,      (only if success=true)
        "message": "..."         (error message if success=false)
    }
    """
    try:
        # Extract parameters from request
        pond_id = request.data.get('pond_id')
        fish_type_id = request.data.get('fish_type_id')
        
        # Validate required fields
        if not pond_id or not fish_type_id:
            return Response(
                {
                    'success': False,
                    'message': 'pond_id and fish_type_id are required'
                },
                status=400
            )
        
        # Call prediction service (all validation happens here)
        result = predict_harvest(pond_id, fish_type_id, request.user)
        
        return Response(result)
    
    except InsufficientDataError as e:
        return Response(
            {
                'success': False,
                'message': str(e)
            },
            status=400
        )
    
    except InvalidPondError as e:
        return Response(
            {
                'success': False,
                'message': str(e)
            },
            status=403
        )
    
    except InvalidFishTypeError as e:
        return Response(
            {
                'success': False,
                'message': str(e)
            },
            status=403
        )
    
    except PredictionError as e:
        return Response(
            {
                'success': False,
                'message': str(e)
            },
            status=500
        )
    
    except Exception as e:
        return Response(
            {
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            },
            status=500
        )