#!/usr/bin/env python3
"""
Data Collector for ML Training
Reads current data and saves to CSV with labels for training
"""
import json
import time
import csv
import os
from collections import deque

DATA_FILE = "/tmp/ev_current.json"
OUTPUT_CSV = "training_data.csv"

# Keep history for feature extraction
history = deque(maxlen=100)  # Last 10 seconds (100 * 0.1s)

def calculate_features(current_value):
    """Calculate features from current value and history"""
    history.append(current_value)
    
    if len(history) < 2:
        return {
            'current': current_value,
            'current_change': 0,
            'moving_avg_5': current_value,
            'moving_avg_10': current_value,
            'std_dev': 0,
            'max_last_10': current_value,
            'min_last_10': current_value,
            'range_last_10': 0
        }
    
    # Calculate features
    recent_10 = list(history)[-10:]
    recent_5 = list(history)[-5:]
    
    current_change = abs(history[-1] - history[-2])
    moving_avg_5 = sum(recent_5) / len(recent_5)
    moving_avg_10 = sum(recent_10) / len(recent_10)
    
    # Standard deviation
    mean = sum(recent_10) / len(recent_10)
    variance = sum((x - mean) ** 2 for x in recent_10) / len(recent_10)
    std_dev = variance ** 0.5
    
    max_val = max(recent_10)
    min_val = min(recent_10)
    range_val = max_val - min_val
    
    return {
        'current': current_value,
        'current_change': current_change,
        'moving_avg_5': moving_avg_5,
        'moving_avg_10': moving_avg_10,
        'std_dev': std_dev,
        'max_last_10': max_val,
        'min_last_10': min_val,
        'range_last_10': range_val
    }

def is_anomaly(features):
    """
    Label data as anomaly based on rules
    Anomaly = rapid changes, high variation
    """
    # DAHA ESNEK KURALLAR:
    # 1. Rapid change (>3A in 0.1s) - daha hassas
    # 2. High standard deviation (>2A) - daha hassas
    # 3. Large range in last 10 readings (>6A) - daha hassas
    
    if features['current_change'] > 3:  # 5'ten 3'e düşürdük
        return 1
    if features['std_dev'] > 2:  # 3'ten 2'ye düşürdük
        return 1
    if features['range_last_10'] > 6:  # 10'dan 6'ya düşürdük
        return 1
    
    return 0

def main():
    print("=" * 60)
    print("📊 Data Collector for ML Training")
    print("=" * 60)
    print(f"Reading from: {DATA_FILE}")
    print(f"Saving to: {OUTPUT_CSV}")
    print()
    print("🎯 Collecting data for 90 seconds...")
    print("   (This will capture ~3-4 anomaly cycles)")
    print()
    
    # Create CSV file with headers
    file_exists = os.path.exists(OUTPUT_CSV)
    csvfile = open(OUTPUT_CSV, 'a', newline='')
    fieldnames = ['timestamp', 'current', 'current_change', 'moving_avg_5', 
                  'moving_avg_10', 'std_dev', 'max_last_10', 'min_last_10', 
                  'range_last_10', 'label']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    if not file_exists:
        writer.writeheader()
        print("✅ CSV file created with headers")
    
    start_time = time.time()
    sample_count = 0
    anomaly_count = 0
    
    try:
        while time.time() - start_time < 90:  # 90 saniyeye çıkardık
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    current = data.get('current', 0)
                    timestamp = data.get('timestamp', time.time())
                
                # Calculate features
                features = calculate_features(current)
                label = is_anomaly(features)
                
                # Prepare row
                row = {
                    'timestamp': timestamp,
                    **features,
                    'label': label
                }
                
                # Write to CSV
                writer.writerow(row)
                sample_count += 1
                
                if label == 1:
                    anomaly_count += 1
                    print(f"🔴 Sample {sample_count}: {current}A → ANOMALY")
                else:
                    if sample_count % 20 == 0:  # Print every 20 normal samples
                        print(f"✅ Sample {sample_count}: {current}A → Normal")
                
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
    
    finally:
        csvfile.close()
        elapsed = time.time() - start_time
        
        print()
        print("=" * 60)
        print("📊 DATA COLLECTION COMPLETE!")
        print("=" * 60)
        print(f"⏱️  Duration: {elapsed:.1f} seconds")
        print(f"📊 Total samples: {sample_count}")
        print(f"🔴 Anomaly samples: {anomaly_count} ({anomaly_count/sample_count*100:.1f}%)")
        print(f"✅ Normal samples: {sample_count - anomaly_count} ({(sample_count-anomaly_count)/sample_count*100:.1f}%)")
        print(f"💾 Data saved to: {OUTPUT_CSV}")
        print()
        print("🚀 Next step: Run 'python train_model.py' to train the AI model")
        print("=" * 60)

if __name__ == "__main__":
    main()
