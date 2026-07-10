from django.apps import AppConfig


class ArichAppConfig(AppConfig):
    name = 'arich_app'
    
    def ready(self):
        """
        Called when Django initializes this app.
        Load ML models into memory for fast predictions.
        """
        try:
            from arich_app.ml_loader import load_models, get_model_status
            load_models()
            status = get_model_status()
            print("[ML Loader] ✓ Models initialized successfully")
            print(f"[ML Loader] Status: {status}")
        except Exception as e:
            print(f"[ML Loader] ⚠ WARNING: Could not load ML models: {e}")
            print("[ML Loader] Predictions will not be available until models are loaded")
