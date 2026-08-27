"""
Phase 8: AI Anomaly Detection Engine
Script to generate synthetic training data, train the autoencoder, and save artifacts.
"""

import os
import numpy as np
from datetime import datetime, timedelta
import joblib

# Silence TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'backend', 'ml_models')

def generate_synthetic_data(num_samples=10000):
    print(f"Generating {num_samples} synthetic normal data points...")
    
    # Features: Voltage, Current, Power, Time_of_day (0-24), Day_of_week (0-6)
    
    # Base voltage ~230V, Current ~10A
    np.random.seed(42)
    voltage = np.random.normal(230, 2, num_samples)
    current = np.random.normal(10, 1.5, num_samples)
    power_factor = np.random.normal(0.95, 0.02, num_samples)
    
    # Time and day
    time_of_day = np.random.uniform(0, 24, num_samples)
    day_of_week = np.random.randint(0, 7, num_samples)
    
    # Add some time-of-day correlation to current (e.g., peak at 18:00)
    # Peak multiplier: normally 1, at peak up to 1.5
    peak_effect = 1 + 0.5 * np.exp(-0.5 * ((time_of_day - 18) / 3)**2)
    current = current * peak_effect
    
    # Compute power P = V * I * PF
    power = voltage * current * power_factor
    
    # Stack features
    data = np.column_stack((voltage, current, power, time_of_day, day_of_week))
    return data

def build_model(input_dim):
    model = Sequential([
        Input(shape=(input_dim,)),
        Dense(16, activation='relu'),
        Dense(8, activation='relu'),
        Dense(4, activation='relu'), # bottleneck
        Dense(8, activation='relu'),
        Dense(16, activation='relu'),
        Dense(input_dim, activation='linear')
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 1. Generate Data
    data = generate_synthetic_data(10000)
    
    # 2. Preprocess
    print("Fitting StandardScaler...")
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    
    # 3. Split
    X_train, X_val = train_test_split(data_scaled, test_size=0.2, random_state=42)
    
    # 4. Build Model
    model = build_model(data.shape[1])
    
    # 5. Train
    print("Training autoencoder...")
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    model.fit(
        X_train, X_train,
        epochs=50,
        batch_size=32,
        validation_data=(X_val, X_val),
        callbacks=[early_stop],
        verbose=1
    )
    
    # 6. Save Artifacts
    model_path = os.path.join(MODEL_DIR, 'autoencoder.keras')
    scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
    
    model.save(model_path)
    joblib.dump(scaler, scaler_path)
    print(f"Model saved to {model_path}")
    print(f"Scaler saved to {scaler_path}")
    
    # 7. Evaluate to find a threshold
    val_predictions = model.predict(X_val)
    mse = np.mean(np.power(X_val - val_predictions, 2), axis=1)
    
    # 99th percentile of MSE on validation set as baseline threshold
    threshold = np.percentile(mse, 99)
    print(f"Suggested Anomaly Threshold (99th percentile): {threshold:.4f}")
    
    # Save threshold so backend can load it
    with open(os.path.join(MODEL_DIR, 'threshold.txt'), 'w') as f:
        f.write(str(threshold))
        
if __name__ == "__main__":
    main()
