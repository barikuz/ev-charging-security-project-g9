#!/usr/bin/env python3
"""
Enhanced Real-time Plotter with AI Predictions
Shows current data + AI anomaly predictions
"""
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
import json

# Data files
DATA_FILE = "/tmp/ev_current.json"
PREDICTIONS_FILE = "/tmp/ev_predictions.json"

# Data storage (keep last 60 seconds)
max_points = 600  # 60 seconds * 10 samples/sec
timestamps = deque(maxlen=max_points)
currents = deque(maxlen=max_points)
predictions = deque(maxlen=max_points)
confidences = deque(maxlen=max_points)

# Start time
start_time = time.time()

def read_data():
    """Read current value and AI prediction"""
    current_val = None
    prediction = 0
    confidence = 0
    
    try:
        # Read current data
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            current_val = data.get('current', 0)
        
        # Read AI prediction
        try:
            with open(PREDICTIONS_FILE, 'r') as f:
                pred_data = json.load(f)
                prediction = pred_data.get('prediction', 0)
                confidence = pred_data.get('confidence', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        if current_val is not None:
            elapsed = time.time() - start_time
            return elapsed, current_val, prediction, confidence
    
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    return None, None, None, None

def animate(frame):
    """Animation function"""
    timestamp, current, prediction, confidence = read_data()
    
    if timestamp is not None and current is not None:
        timestamps.append(timestamp)
        currents.append(current)
        predictions.append(prediction)
        confidences.append(confidence)
        
        # Clear and redraw
        ax.clear()
        
        if len(timestamps) > 0:
            # Plot current
            ax.plot(list(timestamps), list(currents), 'b-', linewidth=2, label='Charging Current')
            
            # Highlight anomalies
            for i, (t, c, p) in enumerate(zip(timestamps, currents, predictions)):
                if p == 1:  # Anomaly
                    ax.plot(t, c, 'ro', markersize=8, alpha=0.7)
            
            # Fill normal vs anomaly regions
            ax.fill_between(list(timestamps), 0, list(currents), 
                           where=[p == 0 for p in predictions],
                           alpha=0.2, color='green', label='Normal (AI)')
            ax.fill_between(list(timestamps), 0, list(currents), 
                           where=[p == 1 for p in predictions],
                           alpha=0.3, color='red', label='Anomaly (AI)')
        
        # Styling
        ax.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Current (A)', fontsize=12, fontweight='bold')
        ax.set_title('⚡ EV Charging Current - AI Anomaly Detection\n🤖 Machine Learning Model Active', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper left', fontsize=10)
        
        # Set limits
        if len(currents) > 0:
            max_current = max(currents)
            ax.set_ylim(-5, max(110, max_current + 10))
        else:
            ax.set_ylim(-5, 110)
        
        # Show latest prediction
        if len(predictions) > 0 and len(confidences) > 0:
            latest_pred = predictions[-1]
            latest_conf = confidences[-1]
            latest_current = currents[-1]
            
            if latest_pred == 1:
                status_text = f'🔴 ANOMALY DETECTED\nCurrent: {latest_current:.1f}A\nAI Confidence: {latest_conf*100:.1f}%'
                bbox_color = 'red'
            else:
                status_text = f'✅ Normal Operation\nCurrent: {latest_current:.1f}A\nAI Confidence: {latest_conf*100:.1f}%'
                bbox_color = 'lightgreen'
            
            ax.text(0.98, 0.98, status_text,
                   transform=ax.transAxes,
                   bbox=dict(boxstyle='round', facecolor=bbox_color, alpha=0.8),
                   verticalalignment='top',
                   horizontalalignment='right',
                   fontsize=10,
                   fontweight='bold')
        
        # Show anomaly count
        if len(predictions) > 0:
            anomaly_count = sum(predictions)
            anomaly_rate = anomaly_count / len(predictions) * 100
            
            stats_text = f'📊 Anomaly Rate: {anomaly_rate:.1f}%\n({anomaly_count}/{len(predictions)} samples)'
            
            ax.text(0.02, 0.02, stats_text,
                   transform=ax.transAxes,
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                   verticalalignment='bottom',
                   fontsize=9)

def main():
    global ax, fig
    
    print("=" * 60)
    print("📈 AI-Enhanced Real-time Plotter")
    print("=" * 60)
    print(f"Reading current from: {DATA_FILE}")
    print(f"Reading AI predictions from: {PREDICTIONS_FILE}")
    print()
    print("🎯 Close the plot window to stop.")
    print()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.canvas.manager.set_window_title('🤖 AI-Powered EV Charging Anomaly Detector')
    
    # Create animation (100ms update)
    ani = animation.FuncAnimation(fig, animate, interval=100, cache_frame_data=False)
    
    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        print("\n⚠️  Plot closed by user")
    finally:
        print("✅ Plotter closed")

if __name__ == "__main__":
    main()
