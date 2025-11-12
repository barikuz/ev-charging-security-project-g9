#!/usr/bin/env python3
"""
Enhanced Real-time Plotter with AI Predictions + Automatic Mitigation System
Shows current data + AI anomaly predictions + Action Timeline
"""
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import time
import json
import numpy as np
from datetime import datetime
import os

# Data files
DATA_FILE = "/tmp/ev_current.json"
PREDICTIONS_FILE = "/tmp/ev_predictions.json"

# Log files
LOG_DIR = "/Users/enisuzun/Desktop/ev-anomaly-sim/logs"
os.makedirs(LOG_DIR, exist_ok=True)
SESSION_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
DETAIL_LOG_FILE = f"{LOG_DIR}/ev_session_{SESSION_ID}.log"
JSON_LOG_FILE = f"{LOG_DIR}/ev_session_{SESSION_ID}.json"

# Data storage (keep last 60 seconds)
max_points = 600  # 60 seconds * 10 samples/sec
timestamps = deque(maxlen=max_points)
currents = deque(maxlen=max_points)
predictions = deque(maxlen=max_points)
confidences = deque(maxlen=max_points)
risk_levels = deque(maxlen=max_points)  # Store risk level for each sample
risk_names = deque(maxlen=max_points)   # Store risk name for each sample

# Mitigation system state
current_action = "NO_ACTION"
last_action_change_time = 0
action_log = []  # List of (start_time, end_time, action_name, severity)
action_start_time = None

# Logging state
log_entries = []  # Store all log entries for JSON export
last_logged_action = None
event_counter = 0

# Physical signal parameters
DT = 0.1  # seconds - sampling interval
SAMPLES_PER_SECOND = 10  # samples per second (1 / DT)
NOMINAL_WINDOW_SIZE = 40  # samples (4 seconds at 10 Hz) for rolling median
SMOOTHING_WINDOW_TIME = 0.3  # seconds - time window for risk smoothing
SMOOTHING_WINDOW_SIZE = int(SMOOTHING_WINDOW_TIME * SAMPLES_PER_SECOND)  # 3 samples

# Rule-based thresholds (A and A/s)
SLOPE_HIGH = 8.0      # A/s - high risk threshold
SLOPE_MODERATE = 1.5  # A/s - moderate risk threshold
DEVIATION_HIGH = 18.0    # A - high risk threshold
DEVIATION_MODERATE = 6.0  # A - moderate risk threshold

# Risk-based action mapping
RISK_THRESHOLDS = {
    'NO_ACTION': 0,
    'SMOOTH_CURRENT': 0,   # STABLE (GREEN)
    'LIMIT_CURRENT': 1,    # MODERATE (YELLOW)
    'SAFE_STOP': 2         # HIGH (RED)
}

# Hysteresis & cooldown
COOLDOWN_TIME = 10  # seconds
ESCALATION_IMMEDIATE = True
last_severity = 0

# Start time
start_time = time.time()

def get_nominal_current():
    """
    Calculate nominal current as rolling median over 4-second window.
    Returns: nominal current value (A)
    """
    if len(currents) < NOMINAL_WINDOW_SIZE:
        # Use all available data if window not full
        return np.median(list(currents)) if len(currents) > 0 else 32.0
    else:
        # Use last 4 seconds of data
        window_data = list(currents)[-NOMINAL_WINDOW_SIZE:]
        return np.median(window_data)

def write_log_header():
    """Write detailed log header with session information"""
    with open(DETAIL_LOG_FILE, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("🔋 EV ŞARJ ANOMALİ TESPİT SİSTEMİ - DETAYLI LOG\n")
        f.write("=" * 80 + "\n")
        f.write(f"📅 Oturum Başlangıcı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"📁 Oturum ID: {SESSION_ID}\n")
        f.write(f"⚙️  Örnekleme Hızı: {SAMPLES_PER_SECOND} Hz ({DT}s)\n")
        f.write(f"📊 Risk Eşikleri:\n")
        f.write(f"   - Yüksek Eğim: {SLOPE_HIGH} A/s\n")
        f.write(f"   - Orta Eğim: {SLOPE_MODERATE} A/s\n")
        f.write(f"   - Yüksek Sapma: {DEVIATION_HIGH} A\n")
        f.write(f"   - Orta Sapma: {DEVIATION_MODERATE} A\n")
        f.write("=" * 80 + "\n\n")
    
    print(f"📝 Log dosyası oluşturuldu: {DETAIL_LOG_FILE}")
    print(f"📝 JSON log dosyası: {JSON_LOG_FILE}")

def log_measurement(timestamp, current, risk_level, risk_name, action, 
                   slope, deviation, nominal, is_predicted):
    """Log measurement data - only log significant events or action changes"""
    global last_logged_action, event_counter
    
    # Log if action changed or risk is not STABLE
    should_log = (action != last_logged_action) or (risk_level > 0)
    
    if should_log:
        event_counter += 1
        
        # Create log entry
        log_entry = {
            "event_id": event_counter,
            "timestamp": timestamp,
            "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "current": round(current, 2),
            "nominal": round(nominal, 2),
            "deviation": round(deviation, 2),
            "slope": round(slope, 2),
            "risk_level": risk_level,
            "risk_name": risk_name,
            "action": action,
            "is_predicted": is_predicted
        }
        
        log_entries.append(log_entry)
        
        # Write detailed text log
        with open(DETAIL_LOG_FILE, 'a', encoding='utf-8') as f:
            if action != last_logged_action:
                f.write("\n" + "─" * 80 + "\n")
                f.write(f"⚠️  AKSİYON DEĞİŞİKLİĞİ #{event_counter}\n")
                f.write("─" * 80 + "\n")
            else:
                f.write(f"\n🔍 OLAY #{event_counter}\n")
            
            f.write(f"🕐 Zaman: {log_entry['datetime']} (t={timestamp:.1f}s)\n")
            f.write(f"⚡ Akım: {current:.2f} A (Nominal: {nominal:.2f} A, Sapma: {deviation:.2f} A)\n")
            f.write(f"📈 Eğim: {slope:.2f} A/s {'📍 (Tahminsel)' if is_predicted else ''}\n")
            f.write(f"🚦 Risk: {risk_name} (Seviye: {risk_level})\n")
            f.write(f"🎯 Aksiyon: {action}\n")
            
            if action != last_logged_action:
                f.write(f"   └─ Önceki: {last_logged_action} → Yeni: {action}\n")
        
        last_logged_action = action

def save_json_log():
    """Save all log entries to JSON file"""
    summary = {
        "session_id": SESSION_ID,
        "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_events": event_counter,
        "configuration": {
            "sampling_rate_hz": SAMPLES_PER_SECOND,
            "dt_seconds": DT,
            "slope_high": SLOPE_HIGH,
            "slope_moderate": SLOPE_MODERATE,
            "deviation_high": DEVIATION_HIGH,
            "deviation_moderate": DEVIATION_MODERATE
        },
        "events": log_entries
    }
    
    with open(JSON_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 JSON log kaydedildi: {JSON_LOG_FILE}")
    print(f"📊 Toplam {event_counter} olay kaydedildi")

def smooth_risk(risk_array, window_size):
    """
    Apply rolling mode filter to smooth risk state transitions.
    This prevents rapid flickering by requiring risk changes to persist.
    
    Args:
        risk_array: list/array of risk levels (0=STABLE, 1=MODERATE, 2=HIGH)
        window_size: number of samples to consider for mode calculation
    
    Returns:
        smoothed_risk: array of smoothed risk levels
    """
    if len(risk_array) == 0:
        return []
    
    smoothed = []
    risk_list = list(risk_array)
    
    for i in range(len(risk_list)):
        # Get window of samples [i - window_size : i]
        start_idx = max(0, i - window_size + 1)
        window = risk_list[start_idx:i+1]
        
        # Calculate mode (most common value in window)
        # Use numpy's bincount for efficient mode calculation
        if len(window) > 0:
            counts = np.bincount(window, minlength=3)  # Count 0, 1, 2
            mode_value = np.argmax(counts)
            smoothed.append(mode_value)
        else:
            smoothed.append(risk_list[i])
    
    return smoothed

def classify_risk():
    """
    Proactive rule-based risk classifier using:
    - Real-time slope and deviation thresholds
    - Short-term predictive slope (3 samples ahead)
    
    Returns: (risk_level, risk_name, severity_for_logging)
        risk_level: 0 (STABLE), 1 (MODERATE), 2 (HIGH)
        risk_name: "STABLE", "MODERATE", "HIGH"
        severity_for_logging: 0.0-1.0 for backwards compatibility
    """
    if len(currents) < 2:
        return 0, "STABLE", 0.0
    
    # Get current nominal value (rolling median)
    nominal_current = get_nominal_current()
    
    # Convert to lists for easier indexing
    curr_list = list(currents)
    
    # ========== REAL-TIME RISK ==========
    # 1. Calculate instantaneous SLOPE: rate of change (A/s)
    slope = abs(curr_list[-1] - curr_list[-2]) / DT
    
    # 2. Calculate DEVIATION: distance from nominal current
    deviation = abs(curr_list[-1] - nominal_current)
    
    # 3. Apply rule-based priority classifier
    if slope > SLOPE_HIGH or deviation > DEVIATION_HIGH:
        real_time_risk = 2  # HIGH
    elif slope > SLOPE_MODERATE or deviation > DEVIATION_MODERATE:
        real_time_risk = 1  # MODERATE
    else:
        real_time_risk = 0  # STABLE
    
    # ========== PREDICTIVE RISK (Proactive Control) ==========
    # Calculate short-term predicted slope using 3 samples
    # predicted_slope = (I[t] - I[t-3]) / (3*dt)
    predicted_risk = 0  # Default: STABLE
    
    if len(curr_list) >= 4:
        # Use last 4 samples to predict next step
        predicted_slope = abs(curr_list[-1] - curr_list[-4]) / (3 * DT)
        
        # Proactive classification: anticipate risk one step earlier
        if predicted_slope > SLOPE_HIGH:
            predicted_risk = 2  # HIGH
        elif predicted_slope > SLOPE_MODERATE:
            predicted_risk = 1  # MODERATE
        else:
            predicted_risk = 0  # STABLE
    
    # ========== COMBINED RISK ==========
    # Take maximum risk between real-time and predictive
    # This allows proactive response to developing situations
    final_risk_level = max(real_time_risk, predicted_risk)
    
    # Map to risk name and severity
    if final_risk_level == 2:
        risk_name = "HIGH"
        severity = 0.9
    elif final_risk_level == 1:
        risk_name = "MODERATE"
        severity = 0.6
    else:
        risk_name = "STABLE"
        severity = 0.2
    
    return final_risk_level, risk_name, severity

def get_risk_color_and_action(risk_level):
    """
    Map risk level to color and action.
    
    Returns: (color, action_name)
    """
    if risk_level == 2:  # HIGH
        return 'red', 'SAFE_STOP'
    elif risk_level == 1:  # MODERATE
        return 'yellow', 'LIMIT_CURRENT'
    else:  # STABLE
        return 'lightgreen', 'SMOOTH_CURRENT'

def select_action(risk_level, severity, current_time):
    """
    Select appropriate action based on risk level with hysteresis and cooldown
    
    Args:
        risk_level: 0 (STABLE), 1 (MODERATE), 2 (HIGH)
        severity: 0.0-1.0 for logging purposes
        current_time: current timestamp
    """
    global current_action, last_action_change_time, action_start_time, last_severity
    
    # Determine target action based on risk level
    if risk_level == 2:  # HIGH
        target_action = 'SAFE_STOP'
    elif risk_level == 1:  # MODERATE
        target_action = 'LIMIT_CURRENT'
    else:  # STABLE (0)
        target_action = 'SMOOTH_CURRENT'
    
    # Check if action change is needed
    if target_action != current_action:
        time_since_last_change = current_time - last_action_change_time
        
        # Escalation (more severe): immediate
        action_levels = ['NO_ACTION', 'SMOOTH_CURRENT', 'LIMIT_CURRENT', 'SAFE_STOP']
        current_level = action_levels.index(current_action)
        target_level = action_levels.index(target_action)
        
        can_change = False
        
        if target_level > current_level:
            # Escalating - immediate
            can_change = True
        elif time_since_last_change >= COOLDOWN_TIME:
            # De-escalating - only after cooldown
            can_change = True
        
        if can_change:
            # Log previous action
            if action_start_time is not None and current_action != "NO_ACTION":
                action_log.append((action_start_time, current_time, current_action, last_severity))
            
            # Change action
            current_action = target_action
            last_action_change_time = current_time
            action_start_time = current_time
            
            # Print action change
            print(f"⚠️  ACTION CHANGE: {target_action} (risk level: {risk_level}, severity: {severity:.2f})")
    
    last_severity = severity
    return current_action

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
        
        # Calculate risk using rule-based classifier
        risk_level, risk_name, severity = classify_risk()
        risk_color, risk_action = get_risk_color_and_action(risk_level)
        action = select_action(risk_level, severity, timestamp)
        
        # Store risk for timeline visualization
        risk_levels.append(risk_level)
        risk_names.append(risk_name)
        
        # Log the measurement if significant
        if len(currents) >= 2:
            nominal = get_nominal_current()
            slope = abs(list(currents)[-1] - list(currents)[-2]) / DT
            deviation = abs(current - nominal)
            
            # Check if this was predicted risk
            is_predicted = False
            if len(currents) >= 4:
                predicted_slope = abs(list(currents)[-1] - list(currents)[-4]) / (3 * DT)
                is_predicted = predicted_slope > SLOPE_HIGH or predicted_slope > SLOPE_MODERATE
            
            log_measurement(timestamp, current, risk_level, risk_name, action,
                          slope, deviation, nominal, is_predicted)
        
        # Clear and redraw both subplots
        ax1.clear()
        ax2.clear()
        
        if len(timestamps) > 0:
            # ============== SUBPLOT 1: Current + Rule-Based Risk Coloring ==============
            # Plot current
            ax1.plot(list(timestamps), list(currents), 'b-', linewidth=2, label='Charging Current')
            
            # Color regions based on RULE-BASED CLASSIFICATION
            # Calculate risk for each point to create color transitions
            risk_colors_per_point = []
            for i in range(len(currents)):
                if i < 1:
                    risk_colors_per_point.append(0)  # GREEN (STABLE)
                    continue
                
                # Get nominal current for this window
                if i < NOMINAL_WINDOW_SIZE:
                    nominal = np.median(list(currents)[:i+1])
                else:
                    nominal = np.median(list(currents)[i-NOMINAL_WINDOW_SIZE+1:i+1])
                
                # Calculate slope and deviation for this point
                slope = abs(list(currents)[i] - list(currents)[i-1]) / DT
                deviation = abs(list(currents)[i] - nominal)
                
                # Apply rule-based classifier
                if slope > SLOPE_HIGH or deviation > DEVIATION_HIGH:
                    risk_colors_per_point.append(2)  # RED (HIGH)
                elif slope > SLOPE_MODERATE or deviation > DEVIATION_MODERATE:
                    risk_colors_per_point.append(1)  # YELLOW (MODERATE)
                else:
                    risk_colors_per_point.append(0)  # GREEN (STABLE)
            
            # Fill regions by risk color
            ax1.fill_between(list(timestamps), 0, list(currents), 
                           where=[c == 0 for c in risk_colors_per_point],
                           alpha=0.3, color='green', label='Stable')
            ax1.fill_between(list(timestamps), 0, list(currents), 
                           where=[c == 1 for c in risk_colors_per_point],
                           alpha=0.3, color='yellow', label='Moderate Risk')
            ax1.fill_between(list(timestamps), 0, list(currents), 
                           where=[c == 2 for c in risk_colors_per_point],
                           alpha=0.3, color='red', label='High Risk')
            
            # Optionally show AI anomaly markers (informational only)
            for i, (t, c, p) in enumerate(zip(timestamps, currents, predictions)):
                if p == 1:  # AI detected anomaly
                    ax1.plot(t, c, 'r^', markersize=6, alpha=0.5, markeredgecolor='darkred')
        
            # Styling
            ax1.set_ylabel('Current (A)', fontsize=12, fontweight='bold')
            ax1.set_title('⚡ EV Charging Current - Rule-Based Risk Classification + Automatic Mitigation\n� Slope & Deviation Thresholds + Protection System Active', 
                         fontsize=14, fontweight='bold', pad=20)
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.legend(loc='upper left', fontsize=10)
            
            # Set limits
            if len(currents) > 0:
                max_current = max(currents)
                ax1.set_ylim(-5, max(110, max_current + 10))
            else:
                ax1.set_ylim(-5, 110)
            
            # Show latest status with rule-based risk
            if len(currents) > 0:
                latest_current = currents[-1]
                nominal = get_nominal_current()
                
                # Calculate current slope and deviation for display
                if len(currents) >= 2:
                    current_slope = abs(list(currents)[-1] - list(currents)[-2]) / DT
                else:
                    current_slope = 0.0
                current_deviation = abs(latest_current - nominal)
                
                # Determine status based on risk level
                if risk_level == 2:  # HIGH
                    status_text = f'🔴 HIGH RISK\nCurrent: {latest_current:.1f}A\nSlope: {current_slope:.1f} A/s\nDeviation: {current_deviation:.1f}A\nNominal: {nominal:.1f}A\nAction: {risk_action}'
                    bbox_color = 'red'
                elif risk_level == 1:  # MODERATE
                    status_text = f'🟡 MODERATE RISK\nCurrent: {latest_current:.1f}A\nSlope: {current_slope:.1f} A/s\nDeviation: {current_deviation:.1f}A\nNominal: {nominal:.1f}A\nAction: {risk_action}'
                    bbox_color = 'yellow'
                else:  # STABLE
                    status_text = f'✅ STABLE\nCurrent: {latest_current:.1f}A\nSlope: {current_slope:.1f} A/s\nDeviation: {current_deviation:.1f}A\nNominal: {nominal:.1f}A\nAction: {risk_action}'
                    bbox_color = 'lightgreen'
                
                ax1.text(0.98, 0.98, status_text,
                       transform=ax1.transAxes,
                       bbox=dict(boxstyle='round', facecolor=bbox_color, alpha=0.8),
                       verticalalignment='top',
                       horizontalalignment='right',
                       fontsize=9,
                       fontweight='bold')
            
            # Show thresholds and AI stats (informational)
            if len(predictions) > 0:
                anomaly_count = sum(predictions)
                anomaly_rate = anomaly_count / len(predictions) * 100
                
                stats_text = f'📏 Thresholds:\nSlope: {SLOPE_MODERATE:.1f}/{SLOPE_HIGH:.1f} A/s\nDeviation: {DEVIATION_MODERATE:.1f}/{DEVIATION_HIGH:.1f}A\n\n🤖 AI: {anomaly_rate:.1f}% anomalies\n(Informational)'
                
                ax1.text(0.02, 0.02, stats_text,
                       transform=ax1.transAxes,
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                       verticalalignment='bottom',
                       fontsize=8)
            
            # ============== SUBPLOT 2: Risk Timeline (Real-Time Classification) ==============
            # Group consecutive samples with same risk level into segments
            risk_colors = {
                0: 'lightgreen',  # STABLE
                1: 'yellow',       # MODERATE
                2: 'red'          # HIGH
            }
            
            risk_names_map = {
                0: 'STABLE',
                1: 'MODERATE',
                2: 'HIGH'
            }
            
            # Build risk segments by grouping consecutive same-risk samples
            # Apply smoothing to prevent flickering in timeline
            if len(risk_levels) > 0:
                # Smooth risk levels using rolling mode filter
                smoothed_risk_levels = smooth_risk(list(risk_levels), SMOOTHING_WINDOW_SIZE)
                
                segments = []  # (start_time, end_time, risk_level)
                current_risk = smoothed_risk_levels[0]
                segment_start = timestamps[0]
                
                for i in range(1, len(smoothed_risk_levels)):
                    if smoothed_risk_levels[i] != current_risk:
                        # Risk changed, save previous segment
                        segments.append((segment_start, timestamps[i-1], current_risk))
                        segment_start = timestamps[i]
                        current_risk = smoothed_risk_levels[i]
                
                # Add final segment
                segments.append((segment_start, timestamps[-1], current_risk))
                
                # Draw risk segments as colored bars
                for start_t, end_t, risk_lvl in segments:
                    color = risk_colors.get(risk_lvl, 'gray')
                    duration = end_t - start_t
                    
                    ax2.barh(0, duration, left=start_t, height=0.8, 
                            color=color, alpha=0.7, edgecolor='black', linewidth=1)
                    
                    # Add risk label if segment is wide enough
                    if duration > 2.0:  # Only label if > 2 seconds
                        mid_t = (start_t + end_t) / 2
                        risk_label = risk_names_map.get(risk_lvl, '?')
                        ax2.text(mid_t, 0, risk_label, ha='center', va='center', 
                                fontsize=9, fontweight='bold', color='black')
            
            # Styling
            ax2.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Risk\nLevel', fontsize=11, fontweight='bold')
            ax2.set_yticks([0])
            ax2.set_yticklabels(['Smoothed\nRisk'])
            ax2.set_ylim(-0.5, 0.5)
            ax2.grid(True, alpha=0.3, linestyle='--', axis='x')
            
            # Sync x-axis with main plot (CRITICAL for synchronization)
            if len(timestamps) > 0:
                ax2.set_xlim(min(timestamps), max(timestamps))
            
            # Show current action as TEXT LABEL only (not color)
            action_emoji = {
                'NO_ACTION': '✅',
                'SMOOTH_CURRENT': '🔄',
                'LIMIT_CURRENT': '⚠️',
                'SAFE_STOP': '🛑'
            }
            
            if len(risk_names) > 0:
                current_risk_name = risk_names[-1]
                # Show both raw and smoothed risk
                if len(risk_levels) > 0 and 'smoothed_risk_levels' in locals():
                    smoothed_risk_name = risk_names_map.get(smoothed_risk_levels[-1], '?')
                    action_status = f"Raw: {current_risk_name} → Smoothed: {smoothed_risk_name}  |  {action_emoji.get(current_action, '❓')} Action: {current_action}"
                else:
                    action_status = f"Risk: {current_risk_name}  |  {action_emoji.get(current_action, '❓')} Action: {current_action}"
            else:
                action_status = f"{action_emoji.get(current_action, '❓')} Action: {current_action}"
                
            ax2.text(0.02, 0.98, action_status,
                    transform=ax2.transAxes,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                    verticalalignment='top',
                    fontsize=8,
                    fontweight='bold')
            
            # Legend for risk colors (matching upper plot)
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='lightgreen', alpha=0.7, label='🟢 Stable'),
                Patch(facecolor='yellow', alpha=0.7, label='🟡 Moderate'),
                Patch(facecolor='red', alpha=0.7, label='🔴 High')
            ]
            ax2.legend(handles=legend_elements, loc='upper right', fontsize=8)
            
            # Add smoothing info indicator
            smoothing_text = f'Smoothing: {SMOOTHING_WINDOW_TIME}s ({SMOOTHING_WINDOW_SIZE} samples)'
            ax2.text(0.98, 0.02, smoothing_text,
                    transform=ax2.transAxes,
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.6),
                    verticalalignment='bottom',
                    horizontalalignment='right',
                    fontsize=7)

def main():
    global ax1, ax2, fig
    
    print("=" * 60)
    print("📈 Physics-Based Real-time Protection System")
    print("=" * 60)
    print(f"Reading current from: {DATA_FILE}")
    print(f"Reading AI predictions from: {PREDICTIONS_FILE} (informational)")
    print()
    print("� Physics-Based Severity Calculation:")
    print("   Severity = 0.6×slope + 0.3×deviation + 0.1×variance")
    print()
    print("🛡️  Automatic Protection Actions:")
    print("   ✅ SMOOTH_CURRENT (<40%) - Stable operation")
    print("   ⚠️  LIMIT_CURRENT (40-75%) - Moderate risk")
    print("   🛑 SAFE_STOP (>75%) - High risk, emergency stop")
    print()
    print("📊 Color Coding:")
    print("   🟢 GREEN: Severity ≤ 40% (stable)")
    print("   🟡 YELLOW: Severity 40-75% (moderate deviation)")
    print("   🔴 RED: Severity > 75% (immediate risk)")
    print()
    print("🎯 Close the plot window to stop.")
    print()
    
    # Initialize logging
    write_log_header()
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), 
                                     gridspec_kw={'height_ratios': [3, 1]})
    fig.canvas.manager.set_window_title('🔬 Physics-Based EV Charging Protection System')
    
    # Create animation (100ms update)
    ani = animation.FuncAnimation(fig, animate, interval=100, cache_frame_data=False)
    
    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        print("\n⚠️  Plot closed by user")
    finally:
        # Log final action
        if action_start_time is not None and current_action != "NO_ACTION":
            action_log.append((action_start_time, time.time() - start_time, 
                             current_action, last_severity))
        
        # Save JSON log
        save_json_log()
        
        # Write session end to detail log
        with open(DETAIL_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"🏁 Oturum Sonu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"📊 Toplam Olay: {event_counter}\n")
            f.write("=" * 80 + "\n")
        
        # Print action summary
        print("\n" + "=" * 60)
        print("📊 ACTION LOG SUMMARY (Physics-Based)")
        print("=" * 60)
        if action_log:
            for start_t, end_t, act_name, act_severity in action_log:
                duration = end_t - start_t
                print(f"⏱️  {start_t:.1f}s - {end_t:.1f}s ({duration:.1f}s): "
                      f"{act_name} (severity: {act_severity*100:.0f}%)")
        else:
            print("✅ No mitigation actions were triggered")
        print("=" * 60)
        print("✅ Plotter closed")

if __name__ == "__main__":
    main()
