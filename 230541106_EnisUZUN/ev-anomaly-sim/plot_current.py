#!/usr/bin/env python3
"""
Real-time Current Plotter
Reads current data from shared file and plots charging current over time.
Visualizes the anomaly pattern with live updating graph.

🧠 Enhanced with MemoryBank: Shows historical anomaly markers and statistics
"""
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
import json
from datetime import datetime, timedelta
from memory_bank import MemoryBank

# Shared data file
DATA_FILE = "/tmp/ev_current.json"

# Initialize MemoryBank
memory = MemoryBank("ev_charging_memory.db")

# Data storage (keep last 60 seconds)
max_points = 60
timestamps = deque(maxlen=max_points)
currents = deque(maxlen=max_points)

# Start time for relative timestamps
start_time = time.time()

def read_can_data():
    """Read current value from shared file"""
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            current = data.get("current", 0)
            timestamp = data.get("timestamp", 0)
            
            if timestamp > 0:
                elapsed = time.time() - start_time
                print(f"📊 PLOT: Current = {current}A at {elapsed:.1f}s")
                return elapsed, current
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None, None

def animate(frame):
    """Animation function called periodically"""
    # Read new data from CAN
    timestamp, current = read_can_data()
    
    if timestamp is not None and current is not None:
        timestamps.append(timestamp)
        currents.append(current)
        
        # Clear and redraw
        ax.clear()
        
        # Plot the data
        if len(timestamps) > 0:
            ax.plot(list(timestamps), list(currents), 'b-', linewidth=2, label='Charging Current')
            ax.fill_between(list(timestamps), list(currents), alpha=0.3)
        
        # Get and mark historical anomalies from MemoryBank
        try:
            recent_anomalies = memory.get_anomalies(
                anomaly_type="CURRENT_LIMIT_FLUCTUATION",
                since=datetime.now() - timedelta(minutes=2),
                limit=20
            )
            if recent_anomalies:
                anomaly_times = []
                for anomaly in recent_anomalies:
                    anom_time = anomaly['timestamp'] - (time.time() - start_time) + timestamp
                    if min(timestamps) <= anom_time <= max(timestamps):
                        anomaly_times.append(anom_time)
                
                if anomaly_times:
                    for at in anomaly_times:
                        ax.axvline(x=at, color='red', linestyle='--', alpha=0.3, linewidth=1)
        except Exception as e:
            pass
        
        # Styling
        ax.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Current (A)', fontsize=12, fontweight='bold')
        ax.set_title('⚡ EV Charging Current - Live Monitoring\nRepeated Fluctuation Anomaly', 
                     fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper right')
        
        # Set y-axis limits with some padding
        if len(currents) > 0:
            max_current = max(currents)
            ax.set_ylim(-5, max(110, max_current + 10))
        else:
            ax.set_ylim(-5, 110)
        
        # Add anomaly indicator if current is fluctuating
        anomaly_detected = False
        if len(currents) >= 10:
            recent_currents = list(currents)[-10:]
            if max(recent_currents) - min(recent_currents) > 20:
                anomaly_detected = True
                ax.text(0.02, 0.98, '⚠️ ANOMALY DETECTED', 
                       transform=ax.transAxes,
                       bbox=dict(boxstyle='round', facecolor='red', alpha=0.7),
                       verticalalignment='top',
                       fontsize=10,
                       fontweight='bold',
                       color='white')
        
        # Add current value display
        if len(currents) > 0:
            current_val = currents[-1]
            ax.text(0.98, 0.98, f'Current: {current_val:.1f} A', 
                   transform=ax.transAxes,
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                   verticalalignment='top',
                   horizontalalignment='right',
                   fontsize=11,
                   fontweight='bold')
        
        # Add MemoryBank statistics
        try:
            stats = memory.get_metric_statistics("current", since=datetime.now() - timedelta(minutes=1))
            if stats['count'] > 0:
                stats_text = f"Min: {stats['min']:.1f}A | Max: {stats['max']:.1f}A | Avg: {stats['avg']:.1f}A"
                ax.text(0.02, 0.02, stats_text, 
                       transform=ax.transAxes,
                       bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
                       verticalalignment='bottom',
                       fontsize=9)
        except Exception:
            pass

def main():
    global ax, fig, start_time
    
    print("=" * 60)
    print("📈 Real-time Current Plotter Starting...")
    print("🧠 MemoryBank: ev_charging_memory.db")
    print("=" * 60)
    print(f"Reading from: {DATA_FILE}")
    print("Displaying: Real-time charging current")
    print()
    
    # Show MemoryBank statistics
    try:
        summary = memory.get_dashboard_summary()
        print(f"📊 MemoryBank Summary:")
        print(f"   Total Anomalies: {summary['total_anomalies']}")
        print(f"   Last Hour: {summary['anomalies_last_hour']} anomalies")
        print()
    except Exception:
        pass
    
    print("🎯 Close the plot window to stop.")
    print()
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.canvas.manager.set_window_title('EV Charging Anomaly Simulator - MemoryBank Enabled')
    
    # Create animation (update every 100ms for smooth visualization)
    ani = animation.FuncAnimation(fig, animate, interval=100, cache_frame_data=False)
    
    # Show the plot
    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        print("\n⚠️  Plot closed by user")
    finally:
        print("✅ Plotter closed")

if __name__ == "__main__":
    main()
