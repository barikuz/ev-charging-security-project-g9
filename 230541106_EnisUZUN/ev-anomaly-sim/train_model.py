#!/usr/bin/env python3
"""
ML Model Trainer
Trains a Random Forest model to detect anomalies
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pickle
import os

CSV_FILE = "training_data.csv"
MODEL_FILE = "anomaly_model.pkl"
SCALER_FILE = "scaler.pkl"

def main():
    print("=" * 60)
    print("🤖 ML Model Trainer - Anomaly Detection")
    print("=" * 60)
    print()
    
    # Check if CSV exists
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found!")
        print("   Please run 'python data_collector.py' first")
        return
    
    # Load data
    print(f"📂 Loading data from {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    print(f"✅ Loaded {len(df)} samples")
    print()
    
    # Show data distribution
    normal_count = len(df[df['label'] == 0])
    anomaly_count = len(df[df['label'] == 1])
    print("📊 Data Distribution:")
    print(f"   ✅ Normal:  {normal_count} ({normal_count/len(df)*100:.1f}%)")
    print(f"   🔴 Anomaly: {anomaly_count} ({anomaly_count/len(df)*100:.1f}%)")
    print()
    
    # Prepare features and labels
    feature_columns = ['current', 'current_change', 'moving_avg_5', 'moving_avg_10',
                       'std_dev', 'max_last_10', 'min_last_10', 'range_last_10']
    
    X = df[feature_columns].values
    y = df['label'].values
    
    print("🔧 Preparing data...")
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"✅ Training set: {len(X_train)} samples")
    print(f"✅ Test set: {len(X_test)} samples")
    print()
    
    # Train model
    print("🧠 Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'  # Handle imbalanced data
    )
    
    model.fit(X_train_scaled, y_train)
    print("✅ Model trained!")
    print()
    
    # Evaluate model
    print("📊 Evaluating model performance...")
    y_pred = model.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"🎯 Accuracy: {accuracy*100:.2f}%")
    print()
    
    print("📊 Detailed Classification Report:")
    print(classification_report(y_test, y_pred, 
                                target_names=['Normal', 'Anomaly'],
                                digits=3))
    
    print("📊 Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"              Predicted")
    print(f"              Normal  Anomaly")
    print(f"Actual Normal   {cm[0][0]:4d}    {cm[0][1]:4d}")
    print(f"       Anomaly  {cm[1][0]:4d}    {cm[1][1]:4d}")
    print()
    
    # Feature importance
    print("📊 Feature Importance:")
    feature_importance = sorted(zip(feature_columns, model.feature_importances_),
                                key=lambda x: x[1], reverse=True)
    for feature, importance in feature_importance:
        bar = '█' * int(importance * 50)
        print(f"   {feature:20s} {bar} {importance:.3f}")
    print()
    
    # Save model and scaler
    print("💾 Saving model and scaler...")
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)
    with open(SCALER_FILE, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"✅ Model saved to: {MODEL_FILE}")
    print(f"✅ Scaler saved to: {SCALER_FILE}")
    print()
    
    # Save report
    report_file = "model_report.txt"
    with open(report_file, 'w') as f:
        f.write("ML MODEL TRAINING REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Dataset: {CSV_FILE}\n")
        f.write(f"Total samples: {len(df)}\n")
        f.write(f"Normal samples: {normal_count} ({normal_count/len(df)*100:.1f}%)\n")
        f.write(f"Anomaly samples: {anomaly_count} ({anomaly_count/len(df)*100:.1f}%)\n\n")
        f.write(f"Accuracy: {accuracy*100:.2f}%\n\n")
        f.write("Classification Report:\n")
        f.write(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))
        f.write("\n\nFeature Importance:\n")
        for feature, importance in feature_importance:
            f.write(f"{feature:20s}: {importance:.3f}\n")
    
    print(f"📄 Report saved to: {report_file}")
    print()
    print("=" * 60)
    print("🎉 MODEL TRAINING COMPLETE!")
    print("=" * 60)
    print()
    print("🚀 Next step: Run 'python live_detector.py' for real-time detection")
    print("   or './run_ai.sh' to start the full AI-powered simulation")
    print("=" * 60)

if __name__ == "__main__":
    main()
