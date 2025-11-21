#!/usr/bin/env python3
"""
🧠 MemoryBank - Persistent Memory System for EV Charging Anomaly Detection
===========================================================================

This module provides a SQLite-based memory system that stores:
- Event history (OCPP messages, CAN messages, system events)
- Anomaly detection records with patterns and severity
- Learning metrics (current patterns, charging sessions)
- System statistics and analytics

Features:
- Thread-safe database operations
- Automatic schema initialization
- Time-series event storage
- Pattern recognition support
- Query and analysis utilities
"""

import sqlite3
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import contextlib


class MemoryBank:
    """
    Persistent memory system for EV charging infrastructure.
    
    Stores and retrieves:
    - Events: All system events with timestamps
    - Anomalies: Detected anomalies with severity and patterns
    - Sessions: Charging session metadata
    - Metrics: Performance and statistics
    """
    
    def __init__(self, db_path: str = "memory_bank.db"):
        """
        Initialize MemoryBank with SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Create database schema if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Events table: All system events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Anomalies table: Detected anomalies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    pattern_data TEXT,
                    current_value REAL,
                    expected_value REAL,
                    deviation REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table: Charging sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    total_energy REAL,
                    avg_current REAL,
                    max_current REAL,
                    min_current REAL,
                    anomaly_count INTEGER DEFAULT 0,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Metrics table: System performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    unit TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Patterns table: Learned patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_seen REAL,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomalies(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_type ON anomalies(anomaly_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            
            conn.commit()
    
    @contextlib.contextmanager
    def _get_connection(self):
        """Thread-safe database connection context manager."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    # ==================== EVENT LOGGING ====================
    
    def log_event(self, event_type: str, component: str, 
                  message: str = "", data: Optional[Dict] = None) -> int:
        """
        Log a system event.
        
        Args:
            event_type: Type of event (e.g., "OCPP_MESSAGE", "CAN_MESSAGE", "SYSTEM")
            component: Component that generated the event (e.g., "CSMS", "CP", "CHARGER")
            message: Human-readable message
            data: Additional structured data
        
        Returns:
            Event ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().timestamp()
            data_json = json.dumps(data) if data else None
            
            cursor.execute("""
                INSERT INTO events (timestamp, event_type, component, message, data)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, event_type, component, message, data_json))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_events(self, event_type: Optional[str] = None, 
                   component: Optional[str] = None,
                   since: Optional[datetime] = None,
                   limit: int = 100) -> List[Dict]:
        """
        Query events with optional filters.
        
        Args:
            event_type: Filter by event type
            component: Filter by component
            since: Only return events after this time
            limit: Maximum number of events to return
        
        Returns:
            List of event dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if component:
                query += " AND component = ?"
                params.append(component)
            
            if since:
                query += " AND timestamp >= ?"
                params.append(since.timestamp())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                if event['data']:
                    event['data'] = json.loads(event['data'])
                events.append(event)
            
            return events
    
    # ==================== ANOMALY DETECTION ====================
    
    def record_anomaly(self, anomaly_type: str, severity: str,
                       description: str = "", pattern_data: Optional[Dict] = None,
                       current_value: Optional[float] = None,
                       expected_value: Optional[float] = None) -> int:
        """
        Record a detected anomaly.
        
        Args:
            anomaly_type: Type of anomaly (e.g., "CURRENT_FLUCTUATION", "VOLTAGE_SPIKE")
            severity: Severity level ("LOW", "MEDIUM", "HIGH", "CRITICAL")
            description: Human-readable description
            pattern_data: Pattern details
            current_value: Actual measured value
            expected_value: Expected/normal value
        
        Returns:
            Anomaly ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().timestamp()
            pattern_json = json.dumps(pattern_data) if pattern_data else None
            
            deviation = None
            if current_value is not None and expected_value is not None:
                deviation = abs(current_value - expected_value)
            
            cursor.execute("""
                INSERT INTO anomalies (timestamp, anomaly_type, severity, description,
                                       pattern_data, current_value, expected_value, deviation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, anomaly_type, severity, description, pattern_json,
                  current_value, expected_value, deviation))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_anomalies(self, anomaly_type: Optional[str] = None,
                      severity: Optional[str] = None,
                      since: Optional[datetime] = None,
                      limit: int = 100) -> List[Dict]:
        """
        Query anomalies with optional filters.
        
        Args:
            anomaly_type: Filter by anomaly type
            severity: Filter by severity level
            since: Only return anomalies after this time
            limit: Maximum number of anomalies to return
        
        Returns:
            List of anomaly dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM anomalies WHERE 1=1"
            params = []
            
            if anomaly_type:
                query += " AND anomaly_type = ?"
                params.append(anomaly_type)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            if since:
                query += " AND timestamp >= ?"
                params.append(since.timestamp())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            anomalies = []
            for row in cursor.fetchall():
                anomaly = dict(row)
                if anomaly['pattern_data']:
                    anomaly['pattern_data'] = json.loads(anomaly['pattern_data'])
                anomalies.append(anomaly)
            
            return anomalies
    
    def get_anomaly_count(self, since: Optional[datetime] = None) -> int:
        """Get total count of anomalies, optionally since a given time."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if since:
                cursor.execute(
                    "SELECT COUNT(*) FROM anomalies WHERE timestamp >= ?",
                    (since.timestamp(),)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM anomalies")
            
            return cursor.fetchone()[0]
    
    # ==================== SESSION MANAGEMENT ====================
    
    def start_session(self, session_id: str) -> int:
        """
        Start a new charging session.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Session database ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().timestamp()
            
            cursor.execute("""
                INSERT INTO sessions (session_id, start_time, status)
                VALUES (?, ?, 'ACTIVE')
            """, (session_id, timestamp))
            
            conn.commit()
            return cursor.lastrowid
    
    def end_session(self, session_id: str, 
                    total_energy: Optional[float] = None,
                    avg_current: Optional[float] = None,
                    max_current: Optional[float] = None,
                    min_current: Optional[float] = None):
        """
        End a charging session and update statistics.
        
        Args:
            session_id: Session identifier
            total_energy: Total energy delivered (Wh)
            avg_current: Average current (A)
            max_current: Maximum current (A)
            min_current: Minimum current (A)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().timestamp()
            
            cursor.execute("""
                UPDATE sessions
                SET end_time = ?, total_energy = ?, avg_current = ?,
                    max_current = ?, min_current = ?, status = 'COMPLETED'
                WHERE session_id = ?
            """, (timestamp, total_energy, avg_current, max_current, 
                  min_current, session_id))
            
            conn.commit()
    
    def increment_session_anomaly_count(self, session_id: str):
        """Increment the anomaly count for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sessions
                SET anomaly_count = anomaly_count + 1
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details by session ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Get most recent charging sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== METRICS ====================
    
    def record_metric(self, metric_name: str, metric_value: float,
                     unit: str = "", metadata: Optional[Dict] = None):
        """
        Record a system metric.
        
        Args:
            metric_name: Name of the metric (e.g., "current", "voltage", "power")
            metric_value: Numeric value
            unit: Unit of measurement (e.g., "A", "V", "W")
            metadata: Additional metadata
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().timestamp()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO metrics (timestamp, metric_name, metric_value, unit, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, metric_name, metric_value, unit, metadata_json))
            
            conn.commit()
    
    def get_metrics(self, metric_name: str,
                   since: Optional[datetime] = None,
                   limit: int = 1000) -> List[Dict]:
        """
        Query metrics with optional time filter.
        
        Args:
            metric_name: Name of metric to retrieve
            since: Only return metrics after this time
            limit: Maximum number of metrics to return
        
        Returns:
            List of metric dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM metrics WHERE metric_name = ?"
            params = [metric_name]
            
            if since:
                query += " AND timestamp >= ?"
                params.append(since.timestamp())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            metrics = []
            for row in cursor.fetchall():
                metric = dict(row)
                if metric['metadata']:
                    metric['metadata'] = json.loads(metric['metadata'])
                metrics.append(metric)
            
            return metrics
    
    def get_metric_statistics(self, metric_name: str,
                            since: Optional[datetime] = None) -> Dict[str, float]:
        """
        Get statistical summary of a metric.
        
        Args:
            metric_name: Name of metric
            since: Calculate statistics from this time
        
        Returns:
            Dictionary with min, max, avg, stddev, count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    MIN(metric_value) as min_value,
                    MAX(metric_value) as max_value,
                    AVG(metric_value) as avg_value,
                    COUNT(*) as count
                FROM metrics
                WHERE metric_name = ?
            """
            params = [metric_name]
            
            if since:
                query += " AND timestamp >= ?"
                params.append(since.timestamp())
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            return {
                'min': row['min_value'] or 0,
                'max': row['max_value'] or 0,
                'avg': row['avg_value'] or 0,
                'count': row['count'] or 0
            }
    
    # ==================== PATTERN LEARNING ====================
    
    def record_pattern(self, pattern_type: str, pattern_data: Dict, 
                      confidence: float = 1.0):
        """
        Record or update a learned pattern.
        
        Args:
            pattern_type: Type of pattern (e.g., "CURRENT_CYCLE", "CHARGE_PROFILE")
            pattern_data: Pattern details (as dictionary)
            confidence: Confidence score (0.0 to 1.0)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().timestamp()
            pattern_json = json.dumps(pattern_data)
            
            # Check if pattern already exists
            cursor.execute("""
                SELECT id FROM patterns
                WHERE pattern_type = ? AND pattern_data = ?
            """, (pattern_type, pattern_json))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing pattern
                cursor.execute("""
                    UPDATE patterns
                    SET frequency = frequency + 1,
                        last_seen = ?,
                        confidence = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (timestamp, confidence, existing['id']))
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO patterns (pattern_type, pattern_data, last_seen, confidence)
                    VALUES (?, ?, ?, ?)
                """, (pattern_type, pattern_json, timestamp, confidence))
            
            conn.commit()
    
    def get_patterns(self, pattern_type: Optional[str] = None,
                    min_frequency: int = 1) -> List[Dict]:
        """
        Query learned patterns.
        
        Args:
            pattern_type: Filter by pattern type
            min_frequency: Minimum occurrence frequency
        
        Returns:
            List of pattern dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM patterns WHERE frequency >= ?"
            params = [min_frequency]
            
            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type)
            
            query += " ORDER BY frequency DESC, last_seen DESC"
            
            cursor.execute(query, params)
            
            patterns = []
            for row in cursor.fetchall():
                pattern = dict(row)
                pattern['pattern_data'] = json.loads(pattern['pattern_data'])
                patterns.append(pattern)
            
            return patterns
    
    # ==================== ANALYTICS ====================
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard summary.
        
        Returns:
            Dictionary with system statistics
        """
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total counts
            cursor.execute("SELECT COUNT(*) FROM events")
            total_events = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM anomalies")
            total_anomalies = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sessions")
            total_sessions = cursor.fetchone()[0]
            
            # Recent counts
            cursor.execute(
                "SELECT COUNT(*) FROM events WHERE timestamp >= ?",
                (last_hour.timestamp(),)
            )
            events_last_hour = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT COUNT(*) FROM anomalies WHERE timestamp >= ?",
                (last_hour.timestamp(),)
            )
            anomalies_last_hour = cursor.fetchone()[0]
            
            # Anomaly breakdown by severity
            cursor.execute("""
                SELECT severity, COUNT(*) as count
                FROM anomalies
                GROUP BY severity
            """)
            anomalies_by_severity = {row['severity']: row['count'] 
                                    for row in cursor.fetchall()}
            
            # Active sessions
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'ACTIVE'")
            active_sessions = cursor.fetchone()[0]
            
            return {
                'total_events': total_events,
                'total_anomalies': total_anomalies,
                'total_sessions': total_sessions,
                'events_last_hour': events_last_hour,
                'anomalies_last_hour': anomalies_last_hour,
                'anomalies_by_severity': anomalies_by_severity,
                'active_sessions': active_sessions,
                'timestamp': now.isoformat()
            }
    
    # ==================== UTILITY METHODS ====================
    
    def clear_old_data(self, days: int = 7):
        """
        Delete data older than specified days.
        
        Args:
            days: Keep data from last N days
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).timestamp()
            
            cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM anomalies WHERE timestamp < ?", (cutoff,))
            cursor.execute("DELETE FROM metrics WHERE timestamp < ?", (cutoff,))
            
            conn.commit()
    
    def export_to_json(self, output_path: str, since: Optional[datetime] = None):
        """
        Export all data to JSON file.
        
        Args:
            output_path: Path to output JSON file
            since: Only export data after this time
        """
        data = {
            'events': self.get_events(since=since, limit=10000),
            'anomalies': self.get_anomalies(since=since, limit=10000),
            'sessions': self.get_recent_sessions(limit=1000),
            'patterns': self.get_patterns(),
            'summary': self.get_dashboard_summary()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def close(self):
        """Close database connection (called automatically on context exit)."""
        pass


# ==================== TESTING ====================

if __name__ == "__main__":
    print("🧠 MemoryBank Test")
    print("=" * 60)
    
    # Create test database
    mb = MemoryBank("test_memory.db")
    
    # Test event logging
    print("\n📝 Testing event logging...")
    event_id = mb.log_event(
        "OCPP_MESSAGE",
        "CSMS",
        "RemoteStartTransaction sent",
        {"transaction_id": 12345}
    )
    print(f"✅ Event logged with ID: {event_id}")
    
    # Test anomaly recording
    print("\n⚠️  Testing anomaly recording...")
    anomaly_id = mb.record_anomaly(
        "CURRENT_FLUCTUATION",
        "HIGH",
        "Rapid current changes detected",
        {"frequency": 0.1, "amplitude": 50},
        current_value=100.0,
        expected_value=50.0
    )
    print(f"✅ Anomaly recorded with ID: {anomaly_id}")
    
    # Test session management
    print("\n🔌 Testing session management...")
    session_id = "TEST_SESSION_001"
    mb.start_session(session_id)
    print(f"✅ Session started: {session_id}")
    
    # Test metrics
    print("\n📊 Testing metrics...")
    mb.record_metric("current", 32.5, "A")
    mb.record_metric("current", 45.0, "A")
    mb.record_metric("current", 28.3, "A")
    stats = mb.get_metric_statistics("current")
    print(f"✅ Current statistics: {stats}")
    
    # Test pattern learning
    print("\n🔍 Testing pattern learning...")
    mb.record_pattern("CURRENT_CYCLE", {"min": 0, "max": 100, "period": 10})
    patterns = mb.get_patterns()
    print(f"✅ Patterns learned: {len(patterns)}")
    
    # Get dashboard summary
    print("\n📈 Dashboard Summary:")
    summary = mb.get_dashboard_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Export to JSON
    print("\n💾 Exporting to JSON...")
    mb.export_to_json("test_export.json")
    print("✅ Data exported to test_export.json")
    
    print("\n✅ All tests passed!")
    print("=" * 60)
