# 🧠 MemoryBank Documentation

## Overview

MemoryBank is a persistent memory system for the EV Charging Anomaly Simulator that records, stores, and learns from all system events, anomalies, and patterns. It uses SQLite for reliable, thread-safe data storage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryBank System                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐  ┌─────────────┐  ┌──────────┐  ┌────────┐ │
│  │  Events    │  │  Anomalies  │  │ Sessions │  │Patterns│ │
│  │   Table    │  │    Table    │  │  Table   │  │ Table  │ │
│  └────────────┘  └─────────────┘  └──────────┘  └────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Metrics Table (Time-Series Data)           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│                SQLite Database: ev_charging_memory.db        │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    ┌────┴────┐         ┌─────┴─────┐      ┌──────┴──────┐
    │  CSMS   │         │    CP     │      │  Plotter    │
    │(Logger) │         │ (Logger)  │      │  (Reader)   │
    └─────────┘         └───────────┘      └─────────────┘
```

## Database Schema

### Events Table

Records all system events (OCPP messages, CAN communications, etc.)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | REAL | Unix timestamp |
| event_type | TEXT | Type (OCPP_BOOT, CAN_TX, CAN_RX, etc.) |
| component | TEXT | Component (CSMS, CP, CHARGER) |
| message | TEXT | Human-readable message |
| data | TEXT | JSON-encoded additional data |
| created_at | TIMESTAMP | Database insertion time |

**Indexes**: `timestamp`, `event_type`

### Anomalies Table

Records detected anomalies with severity and pattern data

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | REAL | Unix timestamp |
| anomaly_type | TEXT | Type (CURRENT_FLUCTUATION, etc.) |
| severity | TEXT | Severity (LOW, MEDIUM, HIGH, CRITICAL) |
| description | TEXT | Human-readable description |
| pattern_data | TEXT | JSON-encoded pattern details |
| current_value | REAL | Measured value |
| expected_value | REAL | Expected/normal value |
| deviation | REAL | Absolute deviation |
| created_at | TIMESTAMP | Database insertion time |

**Indexes**: `timestamp`, `anomaly_type`

### Sessions Table

Tracks charging sessions from start to end

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| session_id | TEXT | Unique session identifier |
| start_time | REAL | Session start timestamp |
| end_time | REAL | Session end timestamp |
| total_energy | REAL | Total energy delivered (Wh) |
| avg_current | REAL | Average current (A) |
| max_current | REAL | Maximum current (A) |
| min_current | REAL | Minimum current (A) |
| anomaly_count | INTEGER | Number of anomalies detected |
| status | TEXT | Status (ACTIVE, COMPLETED) |
| created_at | TIMESTAMP | Database insertion time |

**Indexes**: `start_time`

### Metrics Table

Time-series measurements (current, voltage, power, etc.)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| timestamp | REAL | Unix timestamp |
| metric_name | TEXT | Metric name (current, voltage, power) |
| metric_value | REAL | Numeric value |
| unit | TEXT | Unit of measurement (A, V, W) |
| metadata | TEXT | JSON-encoded additional metadata |
| created_at | TIMESTAMP | Database insertion time |

**Indexes**: `timestamp`

### Patterns Table

Learned behavior patterns for anomaly detection

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| pattern_type | TEXT | Pattern type (ANOMALY_CYCLE, etc.) |
| pattern_data | TEXT | JSON-encoded pattern details |
| frequency | INTEGER | Number of occurrences |
| last_seen | REAL | Last occurrence timestamp |
| confidence | REAL | Confidence score (0.0 to 1.0) |
| created_at | TIMESTAMP | Database insertion time |
| updated_at | TIMESTAMP | Last update time |

## API Usage

### Initialization

```python
from memory_bank import MemoryBank

# Initialize with default database
memory = MemoryBank()

# Or specify custom database path
memory = MemoryBank("custom_memory.db")
```

### Logging Events

```python
# Log a system event
event_id = memory.log_event(
    event_type="OCPP_MESSAGE",
    component="CSMS",
    message="RemoteStartTransaction sent",
    data={"transaction_id": 12345, "connector_id": 1}
)

# Query recent events
events = memory.get_events(
    event_type="OCPP_MESSAGE",
    component="CSMS",
    limit=50
)

# Get events since a specific time
from datetime import datetime, timedelta
since = datetime.now() - timedelta(hours=1)
events = memory.get_events(since=since)
```

### Recording Anomalies

```python
# Record an anomaly
anomaly_id = memory.record_anomaly(
    anomaly_type="CURRENT_FLUCTUATION",
    severity="HIGH",
    description="Rapid current changes detected",
    pattern_data={
        "frequency": 0.1,
        "amplitude": 50,
        "type": "oscillation"
    },
    current_value=100.0,
    expected_value=50.0
)

# Query anomalies
anomalies = memory.get_anomalies(
    anomaly_type="CURRENT_FLUCTUATION",
    severity="HIGH",
    limit=20
)

# Get anomaly count
count = memory.get_anomaly_count()
```

### Session Management

```python
# Start a session
memory.start_session("SESSION_001")

# Increment anomaly count for session
memory.increment_session_anomaly_count("SESSION_001")

# End session with statistics
memory.end_session(
    "SESSION_001",
    total_energy=1250.5,
    avg_current=32.5,
    max_current=100.0,
    min_current=0.0
)

# Get session details
session = memory.get_session("SESSION_001")

# Get recent sessions
sessions = memory.get_recent_sessions(limit=10)
```

### Recording Metrics

```python
# Record a metric
memory.record_metric(
    metric_name="current",
    metric_value=32.5,
    unit="A",
    metadata={"connector_id": 1, "phase": "L1"}
)

# Query metrics
metrics = memory.get_metrics(
    metric_name="current",
    since=datetime.now() - timedelta(minutes=10),
    limit=1000
)

# Get statistics
stats = memory.get_metric_statistics(
    metric_name="current",
    since=datetime.now() - timedelta(hours=1)
)
# Returns: {'min': 0.0, 'max': 100.0, 'avg': 45.2, 'count': 3600}
```

### Pattern Learning

```python
# Record a pattern
memory.record_pattern(
    pattern_type="ANOMALY_CYCLE",
    pattern_data={
        "sequence": ["0A", "100A", "START", "STOP"],
        "cycle_time": 8,
        "severity": "HIGH"
    },
    confidence=0.95
)

# Query patterns
patterns = memory.get_patterns(
    pattern_type="ANOMALY_CYCLE",
    min_frequency=5
)
```

### Analytics

```python
# Get comprehensive dashboard summary
summary = memory.get_dashboard_summary()
# Returns:
# {
#     'total_events': 1234,
#     'total_anomalies': 56,
#     'total_sessions': 12,
#     'events_last_hour': 345,
#     'anomalies_last_hour': 8,
#     'anomalies_by_severity': {'HIGH': 23, 'MEDIUM': 18, 'LOW': 15},
#     'active_sessions': 1,
#     'timestamp': '2025-11-21T10:30:00'
# }
```

### Data Management

```python
# Export data to JSON
memory.export_to_json(
    "data_export.json",
    since=datetime.now() - timedelta(days=7)
)

# Clean old data (keep last 7 days)
memory.clear_old_data(days=7)
```

## Integration Examples

### In CSMS (csms.py)

```python
from memory_bank import MemoryBank

memory = MemoryBank("ev_charging_memory.db")

# Log boot notification
memory.log_event(
    "OCPP_BOOT",
    "CSMS",
    f"Charge point {cp_id} connected",
    {"cp_id": cp_id, "model": model, "vendor": vendor}
)

# Record anomaly during cycle
memory.record_anomaly(
    "CURRENT_LIMIT_FLUCTUATION",
    "HIGH",
    f"Rapid charging limit change: 0A → 100A",
    {"cycle": cycle, "cp_id": cp_id},
    current_value=100.0,
    expected_value=32.0
)

# Record learned pattern
memory.record_pattern(
    "ANOMALY_CYCLE",
    {"sequence": ["0A", "100A", "START", "STOP"]},
    confidence=1.0
)
```

### In Charge Point (cp.py)

```python
from memory_bank import MemoryBank

memory = MemoryBank("ev_charging_memory.db")

# Log CAN transmission
memory.log_event(
    "CAN_TX",
    "CP",
    "START command sent to charger",
    {"can_id": "0x200", "data": []}
)

# Log CAN reception and record metric
memory.log_event(
    "CAN_RX",
    "CP",
    f"Current reading: {current}A",
    {"can_id": "0x300", "current": current}
)
memory.record_metric("current", float(current), "A")

# Start/end sessions
memory.start_session(f"TXN_{transaction_id}")
memory.end_session(f"TXN_{transaction_id}")
```

### In Plotter (plot_current.py)

```python
from memory_bank import MemoryBank
from datetime import datetime, timedelta

memory = MemoryBank("ev_charging_memory.db")

# Get statistics for display
stats = memory.get_metric_statistics(
    "current",
    since=datetime.now() - timedelta(minutes=1)
)

# Show historical anomalies
anomalies = memory.get_anomalies(
    since=datetime.now() - timedelta(minutes=2),
    limit=20
)
```

## MemoryBank Viewer

The `memory_viewer.py` tool provides interactive access to the database:

### Command-Line Usage

```bash
# Interactive menu
python3 memory_viewer.py

# Quick summary
python3 memory_viewer.py --summary

# Show events
python3 memory_viewer.py --events 50

# Show anomalies
python3 memory_viewer.py --anomalies 20

# Show sessions
python3 memory_viewer.py --sessions 10

# Show patterns
python3 memory_viewer.py --patterns

# Show statistics
python3 memory_viewer.py --stats

# Export to JSON
python3 memory_viewer.py --export output.json

# Use custom database
python3 memory_viewer.py --db custom_memory.db --summary
```

### Interactive Menu Options

1. **Show Summary** - Overall statistics and recent activity
2. **Show Recent Events** - Last N system events
3. **Show Recent Anomalies** - Last N detected anomalies
4. **Show Sessions** - Charging session history
5. **Show Learned Patterns** - Pattern recognition results
6. **Show Current Statistics** - Statistical analysis of metrics
7. **Search Events** - Filter events by component or type
8. **Export Data** - Export to JSON for external analysis
9. **Clean Old Data** - Remove data older than N days

## Performance Considerations

### Thread Safety

MemoryBank uses thread-level locking to ensure safe concurrent access:

```python
with self.lock:
    # Database operations are protected
    conn = sqlite3.connect(self.db_path)
```

### Indexes

All frequently-queried columns have indexes for fast lookups:
- Events: `timestamp`, `event_type`
- Anomalies: `timestamp`, `anomaly_type`
- Sessions: `start_time`
- Metrics: `timestamp`

### Data Cleanup

Regular cleanup prevents database bloat:

```python
# Clean data older than 7 days
memory.clear_old_data(days=7)

# Or schedule periodic cleanup
import schedule
schedule.every().day.at("03:00").do(lambda: memory.clear_old_data(days=7))
```

## Best Practices

### 1. Consistent Event Types

Use standardized event type names:
- `OCPP_BOOT` - Boot notifications
- `OCPP_COMMAND` - OCPP commands sent
- `OCPP_REMOTE_START` - Remote start received
- `OCPP_REMOTE_STOP` - Remote stop received
- `CAN_TX` - CAN message transmitted
- `CAN_RX` - CAN message received
- `ANOMALY_CYCLE_START` - Anomaly cycle begins
- `ERROR` - Error conditions

### 2. Severity Levels

Use consistent severity classification:
- `LOW` - Minor deviations, informational
- `MEDIUM` - Moderate anomalies, worth investigation
- `HIGH` - Serious anomalies, requires attention
- `CRITICAL` - Severe anomalies, immediate action required

### 3. Pattern Data Structure

Keep pattern data consistent and descriptive:

```python
pattern_data = {
    "type": "current_fluctuation",
    "sequence": ["0A", "100A", "START", "STOP"],
    "cycle_time": 8,
    "severity": "HIGH",
    "frequency": 0.125  # Hz
}
```

### 4. Metadata Usage

Use metadata fields for context-specific information:

```python
metadata = {
    "connector_id": 1,
    "transaction_id": 12345,
    "protocol_version": "1.6",
    "vendor_specific": {...}
}
```

## Troubleshooting

### Database Locked Error

If you see "database is locked" errors:

1. Ensure only one process writes at a time
2. Use shorter database operations
3. Increase timeout if needed:

```python
conn = sqlite3.connect(self.db_path, timeout=20.0)
```

### Large Database Size

If database grows too large:

```python
# Regular cleanup
memory.clear_old_data(days=7)

# Or vacuum database
import sqlite3
conn = sqlite3.connect("ev_charging_memory.db")
conn.execute("VACUUM")
conn.close()
```

### Slow Queries

If queries are slow:

1. Check indexes exist
2. Limit result sets
3. Use time-based filtering
4. Consider archiving old data

## Future Enhancements

Potential future features:

- **Machine Learning Integration**: Automatic pattern recognition
- **Real-time Alerts**: Push notifications for critical anomalies
- **Web Dashboard**: Browser-based visualization
- **Data Streaming**: Real-time data export to external systems
- **Predictive Analytics**: Forecast anomaly likelihood
- **Multi-Database Support**: PostgreSQL, MongoDB support

## Summary

MemoryBank provides:

✅ **Persistent Storage** - SQLite database for reliability  
✅ **Thread-Safe** - Safe concurrent access from multiple components  
✅ **Comprehensive Logging** - Events, anomalies, sessions, metrics  
✅ **Pattern Learning** - Automatic behavior pattern recognition  
✅ **Analytics** - Statistical analysis and reporting  
✅ **Easy Integration** - Simple API for all components  
✅ **Interactive Viewer** - CLI tool for data exploration  
✅ **Export Capability** - JSON export for external analysis

---

**For more information, see the main README.md and source code in `memory_bank.py`**
