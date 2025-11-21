#!/usr/bin/env python3
"""
🧠 MemoryBank Viewer - Database Analysis and Visualization Tool
================================================================

This tool provides a comprehensive view of the MemoryBank database:
- View all events, anomalies, sessions, and patterns
- Generate statistics and analytics
- Export data to JSON/CSV
- Clean old data
- Interactive CLI interface

Usage:
    python3 memory_viewer.py              # Interactive menu
    python3 memory_viewer.py --summary    # Quick summary
    python3 memory_viewer.py --export     # Export to JSON
"""

import argparse
import json
from datetime import datetime, timedelta
from memory_bank import MemoryBank
from tabulate import tabulate


class MemoryViewer:
    """Interactive viewer for MemoryBank database"""
    
    def __init__(self, db_path: str = "ev_charging_memory.db"):
        """Initialize viewer with database path"""
        self.memory = MemoryBank(db_path)
        self.db_path = db_path
    
    def print_header(self, title: str):
        """Print formatted section header"""
        print()
        print("=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def show_summary(self):
        """Display comprehensive system summary"""
        self.print_header("🧠 MemoryBank Summary")
        
        summary = self.memory.get_dashboard_summary()
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total Events:            {summary['total_events']:,}")
        print(f"   Total Anomalies:         {summary['total_anomalies']:,}")
        print(f"   Total Sessions:          {summary['total_sessions']:,}")
        print(f"   Active Sessions:         {summary['active_sessions']}")
        
        print(f"\n⏱️  Recent Activity (Last Hour):")
        print(f"   Events:                  {summary['events_last_hour']:,}")
        print(f"   Anomalies:               {summary['anomalies_last_hour']:,}")
        
        if summary['anomalies_by_severity']:
            print(f"\n⚠️  Anomalies by Severity:")
            for severity, count in summary['anomalies_by_severity'].items():
                print(f"   {severity:15s}      {count:,}")
        
        print(f"\n🕐 Report Time: {summary['timestamp']}")
        print()
    
    def show_recent_events(self, limit: int = 20):
        """Display recent system events"""
        self.print_header(f"📝 Recent Events (Last {limit})")
        
        events = self.memory.get_events(limit=limit)
        
        if not events:
            print("\n  No events found.")
            return
        
        table_data = []
        for event in events:
            timestamp = datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            table_data.append([
                event['id'],
                timestamp,
                event['event_type'],
                event['component'],
                event['message'][:50] if event['message'] else ''
            ])
        
        print()
        print(tabulate(
            table_data,
            headers=['ID', 'Timestamp', 'Type', 'Component', 'Message'],
            tablefmt='grid'
        ))
        print()
    
    def show_recent_anomalies(self, limit: int = 20):
        """Display recent anomalies"""
        self.print_header(f"⚠️  Recent Anomalies (Last {limit})")
        
        anomalies = self.memory.get_anomalies(limit=limit)
        
        if not anomalies:
            print("\n  No anomalies found.")
            return
        
        table_data = []
        for anomaly in anomalies:
            timestamp = datetime.fromtimestamp(anomaly['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            table_data.append([
                anomaly['id'],
                timestamp,
                anomaly['anomaly_type'],
                anomaly['severity'],
                f"{anomaly['current_value']:.1f}" if anomaly['current_value'] else 'N/A',
                f"{anomaly['expected_value']:.1f}" if anomaly['expected_value'] else 'N/A',
                f"{anomaly['deviation']:.1f}" if anomaly['deviation'] else 'N/A'
            ])
        
        print()
        print(tabulate(
            table_data,
            headers=['ID', 'Timestamp', 'Type', 'Severity', 'Current', 'Expected', 'Deviation'],
            tablefmt='grid'
        ))
        print()
    
    def show_sessions(self, limit: int = 10):
        """Display charging sessions"""
        self.print_header(f"🔌 Charging Sessions (Last {limit})")
        
        sessions = self.memory.get_recent_sessions(limit=limit)
        
        if not sessions:
            print("\n  No sessions found.")
            return
        
        table_data = []
        for session in sessions:
            start_time = datetime.fromtimestamp(session['start_time']).strftime('%Y-%m-%d %H:%M:%S')
            
            if session['end_time']:
                end_time = datetime.fromtimestamp(session['end_time']).strftime('%H:%M:%S')
                duration = session['end_time'] - session['start_time']
                duration_str = f"{int(duration)}s"
            else:
                end_time = "ACTIVE"
                duration_str = "N/A"
            
            table_data.append([
                session['session_id'],
                start_time,
                end_time,
                duration_str,
                f"{session['avg_current']:.1f}A" if session['avg_current'] else 'N/A',
                f"{session['max_current']:.1f}A" if session['max_current'] else 'N/A',
                session['anomaly_count']
            ])
        
        print()
        print(tabulate(
            table_data,
            headers=['Session ID', 'Start', 'End', 'Duration', 'Avg Current', 'Max Current', 'Anomalies'],
            tablefmt='grid'
        ))
        print()
    
    def show_patterns(self):
        """Display learned patterns"""
        self.print_header("🔍 Learned Patterns")
        
        patterns = self.memory.get_patterns()
        
        if not patterns:
            print("\n  No patterns learned yet.")
            return
        
        table_data = []
        for pattern in patterns:
            last_seen = datetime.fromtimestamp(pattern['last_seen']).strftime('%Y-%m-%d %H:%M:%S')
            pattern_summary = str(pattern['pattern_data'])[:50]
            
            table_data.append([
                pattern['id'],
                pattern['pattern_type'],
                pattern_summary,
                pattern['frequency'],
                f"{pattern['confidence']:.2f}",
                last_seen
            ])
        
        print()
        print(tabulate(
            table_data,
            headers=['ID', 'Type', 'Pattern', 'Frequency', 'Confidence', 'Last Seen'],
            tablefmt='grid'
        ))
        print()
    
    def show_current_statistics(self):
        """Display current metric statistics"""
        self.print_header("📊 Current Statistics")
        
        # Last hour statistics
        stats_1h = self.memory.get_metric_statistics("current", since=datetime.now() - timedelta(hours=1))
        # Last 10 minutes statistics
        stats_10m = self.memory.get_metric_statistics("current", since=datetime.now() - timedelta(minutes=10))
        # All-time statistics
        stats_all = self.memory.get_metric_statistics("current")
        
        print()
        print("⏱️  Last Hour:")
        print(f"   Samples:      {stats_1h['count']:,}")
        print(f"   Min:          {stats_1h['min']:.2f} A")
        print(f"   Max:          {stats_1h['max']:.2f} A")
        print(f"   Average:      {stats_1h['avg']:.2f} A")
        
        print()
        print("⏱️  Last 10 Minutes:")
        print(f"   Samples:      {stats_10m['count']:,}")
        print(f"   Min:          {stats_10m['min']:.2f} A")
        print(f"   Max:          {stats_10m['max']:.2f} A")
        print(f"   Average:      {stats_10m['avg']:.2f} A")
        
        print()
        print("📈 All-Time:")
        print(f"   Total Samples: {stats_all['count']:,}")
        print(f"   Min:          {stats_all['min']:.2f} A")
        print(f"   Max:          {stats_all['max']:.2f} A")
        print(f"   Average:      {stats_all['avg']:.2f} A")
        print()
    
    def export_data(self, output_file: str = "memory_export.json"):
        """Export all data to JSON"""
        self.print_header("💾 Exporting Data")
        
        print(f"\n📂 Exporting to: {output_file}")
        
        since = datetime.now() - timedelta(days=7)  # Last 7 days
        self.memory.export_to_json(output_file, since=since)
        
        print(f"✅ Data exported successfully!")
        print()
    
    def clean_old_data(self, days: int = 7):
        """Clean data older than specified days"""
        self.print_header("🧹 Cleaning Old Data")
        
        print(f"\n⚠️  This will delete data older than {days} days.")
        confirm = input("Are you sure? (yes/no): ")
        
        if confirm.lower() == 'yes':
            self.memory.clear_old_data(days=days)
            print(f"✅ Data older than {days} days has been deleted.")
        else:
            print("❌ Operation cancelled.")
        print()
    
    def search_events(self, component: str = None, event_type: str = None):
        """Search events by component or type"""
        self.print_header("🔍 Search Events")
        
        events = self.memory.get_events(
            component=component,
            event_type=event_type,
            limit=50
        )
        
        if not events:
            print("\n  No matching events found.")
            return
        
        print(f"\n📊 Found {len(events)} events")
        
        table_data = []
        for event in events[:20]:  # Show first 20
            timestamp = datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            table_data.append([
                timestamp,
                event['event_type'],
                event['component'],
                event['message'][:60] if event['message'] else ''
            ])
        
        print()
        print(tabulate(
            table_data,
            headers=['Timestamp', 'Type', 'Component', 'Message'],
            tablefmt='grid'
        ))
        print()
    
    def interactive_menu(self):
        """Display interactive menu"""
        while True:
            print()
            print("=" * 70)
            print("  🧠 MemoryBank Viewer - Interactive Menu")
            print("=" * 70)
            print()
            print("  1. Show Summary")
            print("  2. Show Recent Events")
            print("  3. Show Recent Anomalies")
            print("  4. Show Sessions")
            print("  5. Show Learned Patterns")
            print("  6. Show Current Statistics")
            print("  7. Search Events")
            print("  8. Export Data to JSON")
            print("  9. Clean Old Data")
            print("  0. Exit")
            print()
            
            choice = input("Select option (0-9): ").strip()
            
            if choice == '1':
                self.show_summary()
            elif choice == '2':
                limit = input("Number of events to show (default 20): ").strip()
                limit = int(limit) if limit else 20
                self.show_recent_events(limit=limit)
            elif choice == '3':
                limit = input("Number of anomalies to show (default 20): ").strip()
                limit = int(limit) if limit else 20
                self.show_recent_anomalies(limit=limit)
            elif choice == '4':
                limit = input("Number of sessions to show (default 10): ").strip()
                limit = int(limit) if limit else 10
                self.show_sessions(limit=limit)
            elif choice == '5':
                self.show_patterns()
            elif choice == '6':
                self.show_current_statistics()
            elif choice == '7':
                print("\nSearch Options:")
                component = input("  Component (CSMS/CP/CHARGER, or leave empty): ").strip() or None
                event_type = input("  Event Type (or leave empty): ").strip() or None
                self.search_events(component=component, event_type=event_type)
            elif choice == '8':
                filename = input("Output filename (default: memory_export.json): ").strip()
                filename = filename if filename else "memory_export.json"
                self.export_data(output_file=filename)
            elif choice == '9':
                days = input("Delete data older than how many days? (default 7): ").strip()
                days = int(days) if days else 7
                self.clean_old_data(days=days)
            elif choice == '0':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid option. Please try again.")
            
            input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MemoryBank Viewer - Analyze EV charging anomaly data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--db',
        default='ev_charging_memory.db',
        help='Path to MemoryBank database (default: ev_charging_memory.db)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary and exit'
    )
    parser.add_argument(
        '--events',
        type=int,
        metavar='N',
        help='Show last N events and exit'
    )
    parser.add_argument(
        '--anomalies',
        type=int,
        metavar='N',
        help='Show last N anomalies and exit'
    )
    parser.add_argument(
        '--sessions',
        type=int,
        metavar='N',
        help='Show last N sessions and exit'
    )
    parser.add_argument(
        '--patterns',
        action='store_true',
        help='Show learned patterns and exit'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show current statistics and exit'
    )
    parser.add_argument(
        '--export',
        metavar='FILE',
        help='Export data to JSON file and exit'
    )
    
    args = parser.parse_args()
    
    # Create viewer
    viewer = MemoryViewer(db_path=args.db)
    
    # Handle command-line options
    if args.summary:
        viewer.show_summary()
    elif args.events:
        viewer.show_recent_events(limit=args.events)
    elif args.anomalies:
        viewer.show_recent_anomalies(limit=args.anomalies)
    elif args.sessions:
        viewer.show_sessions(limit=args.sessions)
    elif args.patterns:
        viewer.show_patterns()
    elif args.stats:
        viewer.show_current_statistics()
    elif args.export:
        viewer.export_data(output_file=args.export)
    else:
        # No arguments - show interactive menu
        viewer.interactive_menu()


if __name__ == "__main__":
    # Check if tabulate is available
    try:
        import tabulate
    except ImportError:
        print("⚠️  Warning: 'tabulate' module not found.")
        print("For better formatting, install it with:")
        print("  pip install tabulate")
        print()
        
        # Define a simple fallback
        def tabulate(data, headers, tablefmt):
            result = " | ".join(headers) + "\n"
            result += "-" * 70 + "\n"
            for row in data:
                result += " | ".join(str(cell) for cell in row) + "\n"
            return result
    
    main()
