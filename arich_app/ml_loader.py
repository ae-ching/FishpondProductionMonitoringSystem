# arich_project/arich_app/ml_loader.py
"""
Machine Learning Model Loader

Loads pre-trained Random Forest model and encoders from joblib files.
This module initializes once and caches models in memory for performance.

IMPORTANT: NEVER retrain the model. Use only saved joblib files.

Feature order (DO NOT CHANGE):
1. Fish_Type (encoded)
2. Pond_Size
3. Harvest_Month
4. Previous_Harvest_Quantity
5. Average_Harvest_Last_3_Records
6. Total_Historical_Harvest_Records

NOTE: Pond_ID has been removed as a feature because database IDs are not
meaningful ML features. The model only uses Fish_Type for encoding.
"""

import joblib
import os
from django.conf import settings

# ==============================================================================
# Global Model Cache
# ==============================================================================
_ML_MODELS = {
    'model': None,
    'fish_encoder': None,
    'feature_columns': None,
    'loaded': False,
}

# ==============================================================================
# Model File Paths
# ==============================================================================
ML_MODELS_DIR = os.path.join(settings.BASE_DIR.parent, 'ml-training', 'models')
MODEL_FILES = {
    'model': os.path.join(ML_MODELS_DIR, 'random_forest_model.pkl'),
    'fish_encoder': os.path.join(ML_MODELS_DIR, 'fish_encoder.pkl'),
    'feature_columns': os.path.join(ML_MODELS_DIR, 'feature_columns.pkl'),
}


# ==============================================================================
# Utility: Check If Model Files Exist
# ==============================================================================
def check_model_files_exist():
    """
    Check if all model files exist.
    
    Returns:
        tuple: (bool exists, list missing_files)
    """
    missing = []
    for name, path in MODEL_FILES.items():
        if not os.path.exists(path):
            missing.append(f"{name}: {path}")
    
    return len(missing) == 0, missing


# ==============================================================================
# Load All Models (Called Once at Startup)
# ==============================================================================
def load_models():
    """
    Load all ML models and encoders from joblib files.
    
    This function should be called once at Django startup.
    Subsequent calls use cached models.
    
    Returns:
        bool: True if successful, False if any file is missing
    
    Raises:
        FileNotFoundError: If any model file is missing
    """
    global _ML_MODELS
    
    # Skip if already loaded
    if _ML_MODELS['loaded']:
        return True
    
    try:
        # Check if all files exist
        all_exist, missing_files = check_model_files_exist()
        if not all_exist:
            raise FileNotFoundError(
                f"Missing ML model files:\n" + "\n".join(missing_files)
            )
        
        print(f"[ML Loader] Loading model artifact: {MODEL_FILES['model']}")
        with open(MODEL_FILES['model'], 'rb') as f:
            _ML_MODELS['model'] = joblib.load(f)
        
        print(f"[ML Loader] Loading fish encoder artifact: {MODEL_FILES['fish_encoder']}")
        with open(MODEL_FILES['fish_encoder'], 'rb') as f:
            _ML_MODELS['fish_encoder'] = joblib.load(f)
        
        print(f"[ML Loader] Loading feature columns artifact: {MODEL_FILES['feature_columns']}")
        with open(MODEL_FILES['feature_columns'], 'rb') as f:
            _ML_MODELS['feature_columns'] = joblib.load(f)
        
        _ML_MODELS['loaded'] = True
        return True
    
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error loading ML models: {e}")
        raise


# ==============================================================================
# Getters for Cached Models
# ==============================================================================
def get_model():
    """Get the trained Random Forest model."""
    if not _ML_MODELS['loaded']:
        load_models()
    return _ML_MODELS['model']


def get_fish_encoder():
    """Get the fish type encoder."""
    if not _ML_MODELS['loaded']:
        load_models()
    return _ML_MODELS['fish_encoder']


def get_feature_columns():
    """Get the feature column names."""
    if not _ML_MODELS['loaded']:
        load_models()
    return _ML_MODELS['feature_columns']


# ==============================================================================
# Status Check
# ==============================================================================
def is_model_loaded():
    """Check if models are loaded in memory."""
    return _ML_MODELS['loaded']


def get_model_status():
    """Get detailed status of ML models."""
    status = {
        'loaded': _ML_MODELS['loaded'],
        'files_exist': check_model_files_exist()[0],
        'model': _ML_MODELS['model'] is not None,
        'fish_encoder': _ML_MODELS['fish_encoder'] is not None,
        'feature_columns': _ML_MODELS['feature_columns'] is not None,
    }
    return status
