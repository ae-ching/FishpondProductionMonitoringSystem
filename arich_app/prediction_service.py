# arich_project/arich_app/prediction_service.py
"""
Machine Learning Prediction Service

Handles all business logic for harvest prediction:
- Database queries (filtered by authenticated user)
- Feature generation (in exact training order)
- Model predictions
- Trend analysis

This service is independent from Django views and HTTP logic.
It returns Python dictionaries, never HTML or HttpResponse.

Feature order (DO NOT CHANGE):
1. Fish_Type (encoded)
2. Pond_Size
3. Harvest_Month
4. Previous_Harvest_Quantity
5. Average_Harvest_Last_3_Records
6. Total_Historical_Harvest_Records

NOTE: Pond_ID has been removed as a feature because database IDs are not
meaningful ML features. The model now only uses Fish_Type for encoding.
"""

import pandas as pd
from datetime import datetime, date
from django.db.models import Q, Avg, Count
from django.contrib.auth.models import User

from .models import Fishpond, FishType, FishpondFishType, Harvest
from .ml_loader import (
    get_model,
    get_fish_encoder,
    get_feature_columns
)


# ==============================================================================
# ERROR HANDLING & VALIDATION
# ==============================================================================

class PredictionError(Exception):
    """Base exception for prediction errors"""
    pass


class InsufficientDataError(PredictionError):
    """Raised when there are fewer than 3 historical records"""
    pass


class InvalidPondError(PredictionError):
    """Raised when pond does not exist or doesn't belong to user"""
    pass


class InvalidFishTypeError(PredictionError):
    """Raised when fish type does not exist or doesn't belong to user"""
    pass


class EncodingError(PredictionError):
    """Raised when encoding fails (pond or fish type unknown to model)"""
    pass


# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================

def validate_pond_access(pond_id, user):
    """
    Validate that the user owns the specified pond.
    
    Args:
        pond_id (int): Fishpond primary key
        user (User): Authenticated Django user
        
    Returns:
        Fishpond: The pond object if validation passes
        
    Raises:
        InvalidPondError: If pond doesn't exist or user doesn't own it
    """
    try:
        # Query: Get pond by ID and verify ownership
        # This ensures user can only access their own ponds
        pond = Fishpond.objects.get(id=pond_id, owner=user)
        return pond
    except Fishpond.DoesNotExist:
        raise InvalidPondError(
            f"Pond with ID {pond_id} does not exist or you don't have access to it."
        )


def validate_fish_type_access(fish_type_id, user):
    """
    Validate that the user owns the specified fish type.
    
    Args:
        fish_type_id (int): FishType primary key
        user (User): Authenticated Django user
        
    Returns:
        FishType: The fish type object if validation passes
        
    Raises:
        InvalidFishTypeError: If fish type doesn't exist or user doesn't own it
    """
    try:
        # Query: Get fish type by ID and verify user ownership
        # This ensures user can only use their own fish types
        fish_type = FishType.objects.get(id=fish_type_id, user=user)
        return fish_type
    except FishType.DoesNotExist:
        raise InvalidFishTypeError(
            f"Fish type with ID {fish_type_id} does not exist or you don't have access to it."
        )


def validate_historical_data(pond, fish_type, user):
    """
    Validate that at least 3 historical harvest records exist.
    
    Args:
        pond (Fishpond): The pond object
        fish_type (FishType): The fish type object
        user (User): Authenticated Django user
        
    Returns:
        tuple: (bool, int) - (has_enough_records, record_count)
        
    Raises:
        InsufficientDataError: If fewer than 3 records exist
    """
    # Query: Count harvest records for this pond + fish_type combination
    # Filtered by authenticated user for security
    record_count = Harvest.objects.filter(
        pond=pond,
        fish_type=fish_type,
        user=user
    ).count()
    
    if record_count < 3:
        raise InsufficientDataError(
            f"Insufficient historical data: {record_count} records found, "
            f"but at least 3 are required for accurate predictions."
        )
    
    return True, record_count


# ==============================================================================
# FEATURE GENERATION FUNCTIONS
# ==============================================================================

def get_harvest_history(pond, fish_type, user):
    """
    Retrieve all harvest records for the given pond and fish type.
    
    Args:
        pond (Fishpond): The pond object
        fish_type (FishType): The fish type object
        user (User): Authenticated Django user
        
    Returns:
        QuerySet: Harvest records ordered by date (most recent last)
    """
    # Query: Get all harvests for this pond + fish_type combination
    # Filtered by authenticated user to prevent cross-user data access
    # Ordered by date ascending so we can easily access previous/recent records
    harvests = Harvest.objects.filter(
        pond=pond,
        fish_type=fish_type,
        user=user
    ).order_by('date')
    
    return harvests


def normalize_fish_type_name(name):
    """Normalize user-entered fish type aliases to the labels used during training."""
    if not name:
        return ""

    normalized = " ".join(str(name).strip().split()).lower()
    alias_map = {
        "milkfish": "Milkfish (Bangus)",
        "bangus": "Milkfish (Bangus)",
        "milkfish (bangus)": "Milkfish (Bangus)",
        "catfish": "Catfish (Hito)",
        "hito": "Catfish (Hito)",
        "catfish (hito)": "Catfish (Hito)",
        "tilapia": "Tilapia",
        "carp": "Carp",
    }

    return alias_map.get(normalized, str(name).strip())


def encode_fish_type(fish_type, fish_encoder):
    """
    Encode fish type using the trained LabelEncoder.

    Args:
        fish_type (FishType): The fish type object
        fish_encoder: LabelEncoder trained on fish types

    Returns:
        int: Encoded fish type

    Raises:
        EncodingError: If fish type is unknown to the encoder
    """
    normalized_name = normalize_fish_type_name(fish_type.name)

    try:
        encoded = fish_encoder.transform([normalized_name])[0]
        return int(encoded)
    except ValueError:
        raise EncodingError(
            f"Fish type '{fish_type.name}' is not recognized by the prediction model. "
            f"This type may not have been included in the training dataset."
        )


def get_pond_size(pond):
    """
    Get pond size from database.
    
    Args:
        pond (Fishpond): The pond object
        
    Returns:
        float: Pond size in m²
    """
    # Pond.size is stored directly in the model
    return float(pond.size) if pond.size else 0.0


def get_harvest_month():
    """
    Get the harvest month for prediction (next month from today).
    
    Returns:
        int: Month number (1-12)
    """
    # For prediction, we use the next month from today
    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1
    return next_month


def get_previous_harvest_quantity(harvests):
    """
    Get the most recent harvest quantity.
    
    Args:
        harvests (QuerySet): Ordered harvest records
        
    Returns:
        float: Quantity in kg from the most recent harvest
    """
    # harvests are ordered by date ascending, so last() gets the most recent
    latest_harvest = harvests.last()
    return float(latest_harvest.quantity) if latest_harvest else 0.0


def get_average_harvest_last_3_records(harvests):
    """
    Calculate the average of the last 3 harvest records.
    
    Args:
        harvests (QuerySet): Ordered harvest records
        
    Returns:
        float: Average quantity in kg
    """
    # Get the 3 most recent harvests (last 3 records)
    last_3_harvests = list(harvests.order_by('-date')[:3])
    
    if not last_3_harvests:
        return 0.0
    
    # Calculate average
    average = sum(h.quantity for h in last_3_harvests) / len(last_3_harvests)
    return float(average)


def get_total_historical_harvest_records(harvests):
    """
    Count total number of harvest records.
    
    Args:
        harvests (QuerySet): Harvest records
        
    Returns:
        int: Total count of records
    """
    # Simple count of all harvests for this pond + fish_type
    return harvests.count()


# ==============================================================================
# FEATURE VECTOR GENERATION
# ==============================================================================

def generate_feature_vector(pond, fish_type, user, harvests):
    """
    Generate complete feature vector for the model.
    
    IMPORTANT: Features must be in EXACT order used during training:
    1. Fish_Type (encoded)
    2. Pond_Size
    3. Harvest_Month
    4. Previous_Harvest_Quantity
    5. Average_Harvest_Last_3_Records
    6. Total_Historical_Harvest_Records
    
    NOTE: Pond_ID has been removed because database IDs are not meaningful ML features.
    
    Args:
        pond (Fishpond): The pond object
        fish_type (FishType): The fish type object
        user (User): Authenticated Django user
        harvests (QuerySet): Harvest records for this pond + fish_type
        
    Returns:
        dict: Feature dictionary with all values
        
    Raises:
        EncodingError: If encoding fails
    """
    # Load encoders
    fish_encoder = get_fish_encoder()
    
    # Generate each feature
    features = {
        'Fish_Type': encode_fish_type(fish_type, fish_encoder),
        'Pond_Size': get_pond_size(pond),
        'Harvest_Month': get_harvest_month(),
        'Previous_Harvest_Quantity': get_previous_harvest_quantity(harvests),
        'Average_Harvest_Last_3_Records': get_average_harvest_last_3_records(harvests),
        'Total_Historical_Harvest_Records': get_total_historical_harvest_records(harvests),
    }
    
    return features


# ==============================================================================
# TREND ANALYSIS
# ==============================================================================

def calculate_trend(predicted_quantity, previous_quantity):
    """
    Determine the production trend.
    
    Compares predicted harvest vs the previous harvest to determine if
    production is increasing, stable, or decreasing.
    
    Args:
        predicted_quantity (float): Predicted harvest quantity
        previous_quantity (float): Most recent actual harvest quantity
        
    Returns:
        str: Trend indicator ('Increasing', 'Stable', or 'Decreasing')
    """
    if previous_quantity == 0:
        # No previous data to compare, assume stable
        return 'Stable'
    
    # Calculate percentage change
    percentage_change = ((predicted_quantity - previous_quantity) / previous_quantity) * 100
    
    # Define thresholds
    INCREASE_THRESHOLD = 5  # More than 5% increase
    DECREASE_THRESHOLD = -5  # More than 5% decrease
    
    if percentage_change > INCREASE_THRESHOLD:
        return 'Increasing'
    elif percentage_change < DECREASE_THRESHOLD:
        return 'Decreasing'
    else:
        return 'Stable'


# ==============================================================================
# MAIN PREDICTION FUNCTION
# ==============================================================================

def predict_harvest(pond_id, fish_type_id, user):
    """
    Generate harvest prediction for a specific pond and fish type.
    
    This is the main entry point for predictions. It:
    1. Validates user access to pond and fish type
    2. Validates sufficient historical data exists
    3. Generates feature vector
    4. Calls the Random Forest model
    5. Calculates trend
    6. Returns structured result
    
    Args:
        pond_id (int): Fishpond ID
        fish_type_id (int): FishType ID
        user (User): Authenticated Django user
        
    Returns:
        dict: Prediction result with keys:
            - success (bool): True if prediction succeeded
            - prediction (float): Predicted harvest quantity (kg)
            - trend (str): 'Increasing', 'Stable', or 'Decreasing'
            - previous_harvest (float): Most recent actual harvest
            - history_count (int): Total historical records used
            - message (str): Result message
            
    Returns (on error):
        dict: Error result with keys:
            - success (bool): False
            - message (str): Error description
    """
    try:
        # ====================================================================
        # STEP 1: VALIDATE ACCESS
        # ====================================================================
        pond = validate_pond_access(pond_id, user)
        fish_type = validate_fish_type_access(fish_type_id, user)
        
        # ====================================================================
        # STEP 2: VALIDATE HISTORICAL DATA
        # ====================================================================
        validate_historical_data(pond, fish_type, user)
        
        # ====================================================================
        # STEP 3: RETRIEVE HARVEST HISTORY
        # ====================================================================
        harvests = get_harvest_history(pond, fish_type, user)
        
        # ====================================================================
        # STEP 4: GENERATE FEATURES
        # ====================================================================
        features = generate_feature_vector(pond, fish_type, user, harvests)
        
        # ====================================================================
        # STEP 5: CALL MODEL
        # ====================================================================
        model = get_model()
        
        # Convert features to a numpy array in the exact order used during training.
        # The saved feature list is loaded from the trained model artifact so this stays
        # compatible with the current dataset even if the order changes later.
        feature_order = get_feature_columns()
        feature_frame = pd.DataFrame(
            [[features[f] for f in feature_order]],
            columns=feature_order,
            dtype=float,
        )
        prediction = model.predict(feature_frame)[0]
        
        # ====================================================================
        # STEP 6: CALCULATE TREND
        # ====================================================================
        previous_harvest = features['Previous_Harvest_Quantity']
        trend = calculate_trend(prediction, previous_harvest)
        
        # ====================================================================
        # STEP 7: RETURN RESULT
        # ====================================================================
        return {
            'success': True,
            'prediction': round(float(prediction), 2),
            'trend': trend,
            'previous_harvest': round(previous_harvest, 2),
            'history_count': features['Total_Historical_Harvest_Records'],
            'message': f"Prediction generated successfully using {features['Total_Historical_Harvest_Records']} historical records.",
        }
    
    except InsufficientDataError as e:
        return {
            'success': False,
            'message': str(e),
        }
    except (InvalidPondError, InvalidFishTypeError) as e:
        return {
            'success': False,
            'message': str(e),
        }
    except EncodingError as e:
        return {
            'success': False,
            'message': str(e),
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Unexpected error during prediction: {str(e)}",
        }


# ==============================================================================
# HELPER FUNCTIONS FOR VIEWS & TEMPLATES
# ==============================================================================

def get_user_ponds_and_fish_types(user):
    """
    Get all ponds and fish types for a user (for populating dropdowns).
    
    Args:
        user (User): Authenticated Django user
        
    Returns:
        dict: With keys 'ponds' and 'fish_types', each with lists of tuples
    """
    # Query: Get all ponds owned by user
    ponds = Fishpond.objects.filter(owner=user).values_list('id', 'name')
    
    # Query: Get all fish types owned by user
    fish_types = FishType.objects.filter(user=user).values_list('id', 'name')
    
    return {
        'ponds': list(ponds),
        'fish_types': list(fish_types),
    }
