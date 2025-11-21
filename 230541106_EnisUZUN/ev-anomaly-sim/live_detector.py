#!/usr/bin/env python3
"""
Live Anomaly Detector
Uses trained ML model to detect anomalies in real-time
"""
import json
import time
import pickle
import numpy as np
from collections import deque

DATA_FILE = "/tmp/ev_current.json"
MODEL_FILE = "anomaly_model.pkl"
SCALER_FILE = "scaler.pkl"
PREDICTIONS_FILE = "/tmp/ev_predictions.json"

class LiveDetector:
    def __init__(self):
        # Load model and scaler
        print("🤖 Loading ML model...")
        with open(MODEL_FILE, 'rb') as f:
            self.model = pickle.load(f)
        with open(SCALER_FILE, 'rb') as f:
            self.scaler = pickle.load(f)
        print("✅ Model loaded successfully")
        
        # Keep history for feature extraction
        self.history = deque(maxlen=100)
        
        # Statistics
        self.total_predictions = 0
        self.anomaly_detections = 0
    
    def calculate_features(self, current_value):
        """Calculate features from current value and history"""
        self.history.append(current_value)
        
        if len(self.history) < 2:
            return None
        
        recent_10 = list(self.history)[-10:]
        recent_5 = list(self.history)[-5:]
        
        current_change = abs(self.history[-1] - self.history[-2])
        moving_avg_5 = sum(recent_5) / len(recent_5)
        moving_avg_10 = sum(recent_10) / len(recent_10)
        
        mean = sum(recent_10) / len(recent_10)
        variance = sum((x - mean) ** 2 for x in recent_10) / len(recent_10)
        std_dev = variance ** 0.5
        
        max_val = max(recent_10)
        min_val = min(recent_10)
        range_val = max_val - min_val
        
        return np.array([[
            current_value,
            current_change,
            moving_avg_5,
            moving_avg_10,
            std_dev,
            max_val,
            min_val,
            range_val
        ]])
    
    def predict(self, current_value):
        """Predict if current reading is anomaly"""
        features = self.calculate_features(current_value)
        
        if features is None:
            return None, None
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.model.predict(features_scaled)[0]
        confidence = self.model.predict_proba(features_scaled)[0]
        
        # Update stats
        self.total_predictions += 1
        if prediction == 1:
            self.anomaly_detections += 1
        
        return prediction, confidence
    
    def run(self):
        print()
        print("=" * 60)
        print("🤖 Live Anomaly Detector - RUNNING")
        print("=" * 60)
        print()
        print("📊 Reading real-time data and making predictions...")
        print("   Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                try:
                    # Read current data
                    with open(DATA_FILE, 'r') as f:
                        data = json.load(f)
                        current = data.get('current', 0)
                        timestamp = data.get('timestamp', time.time())
                    
                    # Make prediction
                    prediction, confidence = self.predict(current)
                    
                    if prediction is not None:
                        # Save prediction to file
                        prediction_data = {
                            'timestamp': timestamp,
                            'current': current,
                            'prediction': int(prediction),
                            'confidence': float(confidence[prediction]),
                            'anomaly_rate': self.anomaly_detections / self.total_predictions
                        }
                        
                        with open(PREDICTIONS_FILE, 'w') as f:
                            json.dump(prediction_data, f)
                        
                        # Display prediction
                        if prediction == 1:
                            print(f"⚡ {current:3d}A → 🔴 ANOMALY (Confidence: {confidence[1]*100:.1f}%)")
                        else:
                            if self.total_predictions % 10 == 0:  # Show every 10th normal
                                print(f"⚡ {current:3d}A → ✅ Normal  (Confidence: {confidence[0]*100:.1f}%)")
                    
                except (FileNotFoundError, json.JSONDecodeError):
                    pass
                
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print()
            print()
            print("=" * 60)
            print("📊 DETECTION STATISTICS")
            print("=" * 60)
            print(f"Total predictions: {self.total_predictions}")
            print(f"Anomalies detected: {self.anomaly_detections} ({self.anomaly_detections/self.total_predictions*100:.1f}%)")
            print(f"Normal readings: {self.total_predictions - self.anomaly_detections} ({(self.total_predictions-self.anomaly_detections)/self.total_predictions*100:.1f}%)")
            print("=" * 60)

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI-Powered Anomaly Detector")
    print("=" * 60)
    
    # Check if model exists
    import os
    if not os.path.exists(MODEL_FILE):
        print()
        print("❌ Error: Model not found!")
        print("   Please run these steps first:")
        print("   1. python data_collector.py  (collect training data)")
        print("   2. python train_model.py     (train the model)")
        print()
        exit(1)
    
    detector = LiveDetector()
    detector.run()
