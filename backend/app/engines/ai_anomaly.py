"""
KAVACHGRID 3.0 — AI Anomaly Detection Engine
Phase 8: Autoencoder-based anomaly detection

Input: Voltage, Current, Power, Time, Day
Output: Anomaly Score (0-1)

Uses TensorFlow/Keras autoencoder model.
"""

import os
import numpy as np
import joblib
from datetime import timezone

# Disable TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from app.schemas.telemetry import TelemetryCreate

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'ml_models')

class AIAnomalyEngine:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.threshold = 1.0 # Default fallback
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return
        
        if not TF_AVAILABLE:
            print("WARNING: TensorFlow not available. AI Anomaly Engine disabled.")
            self._initialized = True
            return

        model_path = os.path.join(MODEL_DIR, 'autoencoder.keras')
        scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
        threshold_path = os.path.join(MODEL_DIR, 'threshold.txt')

        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                self.model = load_model(model_path)
                self.scaler = joblib.load(scaler_path)
                
                if os.path.exists(threshold_path):
                    with open(threshold_path, 'r') as f:
                        self.threshold = float(f.read().strip())
                else:
                    self.threshold = 0.5 # fallback

            except Exception as e:
                print(f"Error loading AI models: {e}")
        
        self._initialized = True

    def compute_anomaly_score(self, telemetry: TelemetryCreate) -> float:
        self._initialize()
        
        if not self.model or not self.scaler:
            return 0.0 # Return 0 if AI engine is not available
            
        # Features: Voltage, Current, Power, Time_of_day (0-24), Day_of_week (0-6)
        voltage = float(telemetry.voltage)
        current = float(telemetry.current)
        power = float(telemetry.power)
        
        # Calculate time of day (float hours) and day of week from timestamp
        if telemetry.timestamp:
            dt = telemetry.timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            from datetime import datetime
            dt = datetime.now(timezone.utc)
            
        time_of_day = dt.hour + (dt.minute / 60.0) + (dt.second / 3600.0)
        day_of_week = dt.weekday() # 0-6
        
        # Prepare input array
        input_data = np.array([[voltage, current, power, time_of_day, day_of_week]])
        
        # Scale
        scaled_input = self.scaler.transform(input_data)
        
        # Predict
        reconstruction = self.model.predict(scaled_input, verbose=0)
        
        # Calculate MSE
        mse = np.mean(np.power(scaled_input - reconstruction, 2))
        
        # Convert MSE to 0-1 score based on threshold
        # If mse == threshold, score = 0.5. If mse >= 2*threshold, score = 1.0
        score = mse / (self.threshold * 2)
        score = min(max(float(score), 0.0), 1.0)
        
        return score

ai_anomaly_engine = AIAnomalyEngine()
