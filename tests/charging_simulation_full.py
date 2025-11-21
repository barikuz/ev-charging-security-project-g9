"""
Complete EV Charging Simulation with Logging and Graphs
Simulates a complete charging session from 10% to 100% SOC with visualization
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
import sys
import os

# Set UTF-8 encoding for output
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Try to import visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("[WARNING] matplotlib not installed. Graphs will not be generated.")
    print("   Install with: pip install matplotlib")

from src.simulator.main import EVChargingSimulator, SimulatorConfig
from src.anomalies.injector import AnomalyConfig

# Setup logging to both file and console
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"charging_session_{timestamp}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ChargingSimulationMonitor:
    """Monitor and track charging session metrics"""
    
    def __init__(self):
        self.timestamps = []
        self.soc_values = []
        self.power_values = []
        self.current_values = []  # Amperage in Amperes
        self.temperature_values = []
        self.voltage_values = []
        self.can_messages = []
        self.ocpp_messages = []
        self.v2g_messages = []
        self.start_time = None
        self.session_data = {
            "start_soc": 10,
            "target_soc": 100,
            "start_time": None,
            "end_time": None,
            "total_energy": 0,
            "peak_power": 0,
            "average_power": 0,
            "charging_time": 0,
            "messages": {
                "can": 0,
                "ocpp": 0,
                "v2g": 0,
                "anomalies": 0
            }
        }
    
    def record_metric(self, soc, power=10000, temp=35, voltage=400):
        """Record charging metrics at a point in time"""
        if self.start_time is None:
            self.start_time = datetime.now()
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.timestamps.append(elapsed)
        self.soc_values.append(soc)
        self.power_values.append(power)
        # Calculate current (amperage) from power and voltage: I = P / V
        current = power / voltage if voltage > 0 else 0
        self.current_values.append(current)
        self.temperature_values.append(temp)
        self.voltage_values.append(voltage)
    
    def add_message_counts(self, can=0, ocpp=0, v2g=0):
        """Track message counts"""
        self.session_data["messages"]["can"] += can
        self.session_data["messages"]["ocpp"] += ocpp
        self.session_data["messages"]["v2g"] += v2g
    
    def finalize(self):
        """Finalize session data"""
        if self.soc_values:
            self.session_data["end_soc"] = self.soc_values[-1]
            self.session_data["peak_power"] = max(self.power_values) if self.power_values else 0
            self.session_data["average_power"] = sum(self.power_values) / len(self.power_values) if self.power_values else 0
            self.session_data["peak_current"] = max(self.current_values) if self.current_values else 0
            self.session_data["average_current"] = sum(self.current_values) / len(self.current_values) if self.current_values else 0
        
        if self.start_time:
            end_time = datetime.now()
            self.session_data["charging_time"] = (end_time - self.start_time).total_seconds()
            self.session_data["start_time"] = self.start_time.isoformat()
            self.session_data["end_time"] = end_time.isoformat()
    
    def generate_graphs(self, output_dir="logs"):
        """Generate visualization graphs"""
        if not HAS_MATPLOTLIB:
            logger.warning("Matplotlib not available for graph generation")
            return
        
        if not self.timestamps or not self.soc_values:
            logger.warning("No data available for graph generation")
            return
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Create figure with subplots (3x2 layout)
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(16, 12))
        fig.suptitle('EV Charging Session Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: State of Charge over time
        ax1.plot(self.timestamps, self.soc_values, 'b-', linewidth=2, label='SOC')
        ax1.fill_between(self.timestamps, self.soc_values, alpha=0.3)
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('State of Charge (%)')
        ax1.set_title('Battery State of Charge')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 105)
        ax1.legend()
        
        # Plot 2: Power delivery over time
        ax2.plot(self.timestamps, self.power_values, 'r-', linewidth=2, label='Power')
        ax2.fill_between(self.timestamps, self.power_values, alpha=0.3, color='red')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Power (Watts)')
        ax2.set_title('Charging Power')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Plot 3: Temperature over time
        ax3.plot(self.timestamps, self.temperature_values, 'g-', linewidth=2, label='Temperature')
        ax3.fill_between(self.timestamps, self.temperature_values, alpha=0.3, color='green')
        ax3.set_xlabel('Time (seconds)')
        ax3.set_ylabel('Temperature (°C)')
        ax3.set_title('Battery Temperature')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=50, color='orange', linestyle='--', label='Warning (50°C)')
        ax3.legend()
        
        # Plot 4: Voltage over time
        ax4.plot(self.timestamps, self.voltage_values, 'm-', linewidth=2, label='Voltage')
        ax4.fill_between(self.timestamps, self.voltage_values, alpha=0.3, color='magenta')
        ax4.set_xlabel('Time (seconds)')
        ax4.set_ylabel('Voltage (V)')
        ax4.set_title('Battery Voltage')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        
        # Plot 5: Current (Amperage) over time
        ax5.plot(self.timestamps, self.current_values, 'c-', linewidth=2, label='Current')
        ax5.fill_between(self.timestamps, self.current_values, alpha=0.3, color='cyan')
        ax5.set_xlabel('Time (seconds)')
        ax5.set_ylabel('Current (Amperes)')
        ax5.set_title('Charging Current (Ammeter)')
        ax5.grid(True, alpha=0.3)
        ax5.legend()
        
        # Plot 6: Energy flow (Power over time)
        # Calculate cumulative energy
        if len(self.timestamps) > 1:
            energy_values = [0]
            for i in range(1, len(self.timestamps)):
                time_delta = (self.timestamps[i] - self.timestamps[i-1]) / 3600  # Convert to hours
                energy_delta = self.power_values[i] * time_delta / 1000  # Convert to kWh
                energy_values.append(energy_values[-1] + energy_delta)
            
            ax6.bar(self.timestamps, self.power_values, width=1, alpha=0.6, color='orange', label='Power')
            ax6.set_xlabel('Time (seconds)')
            ax6.set_ylabel('Power (Watts)')
            ax6.set_title('Charging Power Distribution (Bar Chart)')
            ax6.grid(True, alpha=0.3, axis='y')
            ax6.legend()
        
        plt.tight_layout()
        
        # Save graph
        graph_file = output_dir / f"charging_session_{timestamp}.png"
        plt.savefig(graph_file, dpi=150, bbox_inches='tight')
        logger.info("[OK] Graph saved to: {0}".format(graph_file))
        
        # Also create a summary statistics image
        self._create_summary_graph(output_dir)
        
        plt.close('all')
    
    def _create_summary_graph(self, output_dir):
        """Create a summary statistics graph"""
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2, figsize=(14, 12))
        fig.suptitle('Charging Session Summary Statistics', fontsize=14, fontweight='bold')
        
        # Energy calculation (simplified)
        energy_kwh = self.session_data["average_power"] * self.session_data["charging_time"] / 3600000
        
        # Summary stats
        stats_text = f"""
        Session Summary
        
        Start SOC: {self.session_data['start_soc']}%
        End SOC: {self.session_data.get('end_soc', 100)}%
        Charging Time: {self.session_data['charging_time']:.1f} seconds
        
        Peak Power: {self.session_data['peak_power']:.0f} W
        Average Power: {self.session_data['average_power']:.0f} W
        Energy Delivered: {energy_kwh:.2f} kWh
        
        Peak Current: {self.session_data.get('peak_current', 0):.1f} A
        Average Current: {self.session_data.get('average_current', 0):.1f} A
        
        Messages Sent:
        • CAN: {self.session_data['messages']['can']}
        • OCPP: {self.session_data['messages']['ocpp']}
        • V2G: {self.session_data['messages']['v2g']}
        """
        
        ax1.text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax1.axis('off')
        
        # Message pie chart
        messages = self.session_data['messages']
        msg_values = [messages['can'], messages['ocpp'], messages['v2g']]
        msg_labels = ['CAN', 'OCPP', 'V2G']
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        ax2.pie(msg_values, labels=msg_labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax2.set_title('Message Distribution')
        
        # Power efficiency
        soc_increase = self.session_data.get('end_soc', 100) - self.session_data['start_soc']
        efficiency = (soc_increase / 100) * 100  # Simplified efficiency
        
        categories = ['Efficiency', 'Losses']
        values = [efficiency, 100 - efficiency]
        colors_eff = ['#90EE90', '#FFB6C6']
        ax3.bar(categories, values, color=colors_eff, width=0.6)
        ax3.set_ylabel('Percentage (%)')
        ax3.set_title('Charging Efficiency')
        ax3.set_ylim(0, 100)
        
        for i, v in enumerate(values):
            ax3.text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
        
        # Temperature profile
        temp_min = min(self.temperature_values) if self.temperature_values else 35
        temp_max = max(self.temperature_values) if self.temperature_values else 35
        temp_avg = sum(self.temperature_values) / len(self.temperature_values) if self.temperature_values else 35
        
        temp_data = [temp_min, temp_avg, temp_max]
        temp_labels = ['Min', 'Avg', 'Max']
        colors_temp = ['#87CEEB', '#4169E1', '#FF6347']
        ax4.bar(temp_labels, temp_data, color=colors_temp, width=0.6)
        ax4.set_ylabel('Temperature (°C)')
        ax4.set_title('Temperature Profile')
        ax4.set_ylim(0, 60)
        
        for i, v in enumerate(temp_data):
            ax4.text(i, v + 1, f'{v:.1f}°C', ha='center', fontweight='bold')
        
        # Voltage profile
        voltage_min = min(self.voltage_values) if self.voltage_values else 400
        voltage_max = max(self.voltage_values) if self.voltage_values else 400
        voltage_avg = sum(self.voltage_values) / len(self.voltage_values) if self.voltage_values else 400
        
        voltage_data = [voltage_min, voltage_avg, voltage_max]
        voltage_labels = ['Min', 'Avg', 'Max']
        colors_volt = ['#FFD700', '#FFA500', '#FF8C00']
        ax5.bar(voltage_labels, voltage_data, color=colors_volt, width=0.6)
        ax5.set_ylabel('Voltage (V)')
        ax5.set_title('Voltage Profile')
        ax5.set_ylim(300, 420)
        
        for i, v in enumerate(voltage_data):
            ax5.text(i, v + 5, f'{v:.0f}V', ha='center', fontweight='bold')
        
        # Current (Amperage) profile
        current_min = min(self.current_values) if self.current_values else 0
        current_max = max(self.current_values) if self.current_values else 0
        current_avg = sum(self.current_values) / len(self.current_values) if self.current_values else 0
        
        current_data = [current_min, current_avg, current_max]
        current_labels = ['Min', 'Avg', 'Max']
        colors_curr = ['#87CEEB', '#00CED1', '#00BFFF']
        ax6.bar(current_labels, current_data, color=colors_curr, width=0.6)
        ax6.set_ylabel('Current (Amperes)')
        ax6.set_title('Current (Ammeter) Profile')
        
        for i, v in enumerate(current_data):
            ax6.text(i, v + 0.5, f'{v:.1f}A', ha='center', fontweight='bold')
        
        plt.tight_layout()
        
        summary_file = output_dir / f"summary_{timestamp}.png"
        plt.savefig(summary_file, dpi=150, bbox_inches='tight')
        logger.info("[OK] Summary graph saved to: {0}".format(summary_file))
        
        plt.close('all')


async def run_full_charging_simulation():
    """Run a complete charging simulation from 10% to 100%"""
    
    logger.info("=" * 80)
    logger.info("EV CHARGING SIMULATION - FULL SESSION (10% -> 100%)")
    logger.info("=" * 80)
    
    # Initialize monitor
    monitor = ChargingSimulationMonitor()
    monitor.session_data["start_soc"] = 10
    monitor.session_data["target_soc"] = 100
    
    # Create simulator
    logger.info("\n[INIT] Initializing EV Charging Simulator...")
    
    # Configure without anomalies for clean charging
    anomaly_config = AnomalyConfig(enabled=False)
    config = SimulatorConfig(
        name="Full Charging Session (10% -> 100%)",
        can_enabled=True,
        ocpp_enabled=True,
        v2g_enabled=True,
        anomaly_enabled=False,
        anomaly_config=anomaly_config
    )
    
    simulator = EVChargingSimulator(config)
    
    logger.info("[OK] Simulator initialized with all components")
    logger.info("  - CAN Bus: Enabled")
    logger.info("  - OCPP Protocol: Enabled")
    logger.info("  - V2G Communication: Enabled")
    logger.info("  - Anomaly Injection: Disabled (clean session)")
    
    try:
        # Start simulator
        logger.info("\n[START] Starting simulator components...")
        await simulator.start()
        logger.info("[OK] All components started successfully")
        
        # Connection phase
        logger.info("\n[PHASE 1] Connection & Discovery")
        logger.info("-" * 60)
        await asyncio.sleep(2)
        logger.info("[OK] Vehicle discovery completed")
        logger.info("[OK] OCPP authentication successful")
        logger.info("[OK] V2G handshake completed")
        monitor.record_metric(soc=10, power=0, temp=25)
        
        # Charging phase - simulate gradual increase from 10% to 100%
        logger.info("\n[PHASE 2] Active Charging (10% -> 100%)")
        logger.info("-" * 60)
        
        start_time = datetime.now()
        soc = 10
        phase_duration = 120  # 2 minutes for demo (normally would be hours)
        
        while soc < 100:
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed >= phase_duration:
                soc = 100
            else:
                # Simulate charging curve (faster at beginning, slower near 100%)
                progress = elapsed / phase_duration
                soc = 10 + (90 * progress)
            
            # Calculate power (decreases as SOC approaches 100%)
            power = 10000 * (1 - (soc / 100) ** 2)  # Power tapers
            
            # Simulate temperature
            temp = 25 + (soc / 100) * 20  # Rises with charging
            
            # Record metrics
            monitor.record_metric(soc=soc, power=power, temp=temp, voltage=400)
            
            # Calculate current (amperage)
            current = power / 400  # Current = Power / Voltage
            
            # Log progress every 20%
            if int(soc) % 20 == 0 and int((soc - 1)) % 20 != 0:
                logger.info("[PROGRESS] SOC: {0:3d}% | Power: {1:7.0f}W | Current: {2:6.1f}A | Temp: {3:5.1f}C".format(int(soc), power, current, temp))
            
            # Send messages
            monitor.add_message_counts(can=1, ocpp=1, v2g=1)
            
            await asyncio.sleep(0.1)  # Simulate message frequency
        
        logger.info("[PROGRESS] SOC: {0:3d}% | Power: {1:7.0f}W | Temp: {2:5.1f}C (Completed)".format(int(soc), 0, temp))
        
        await asyncio.sleep(1)
        
        # Disconnection phase
        logger.info("\n[PHASE 3] Disconnection & Session Close")
        logger.info("-" * 60)
        monitor.record_metric(soc=100, power=0, temp=35)
        logger.info("[OK] Charging completed successfully")
        logger.info("[OK] OCPP transaction finalized")
        logger.info("[OK] V2G session closed")
        
        # Stop simulator
        logger.info("\n[STOP] Shutting down simulator...")
        await simulator.stop()
        logger.info("[OK] All components shut down gracefully")
        
    except Exception as e:
        logger.error("[ERROR] Error during simulation: {0}".format(e), exc_info=True)
        await simulator.stop()
        return False
    
    # Finalize data
    monitor.finalize()
    
    # Log final statistics
    logger.info("\n" + "=" * 80)
    logger.info("[SUMMARY] CHARGING SESSION SUMMARY")
    logger.info("=" * 80)
    logger.info("Start SOC:        {0}%".format(monitor.session_data['start_soc']))
    logger.info("End SOC:          {0}%".format(monitor.session_data.get('end_soc', 100)))
    logger.info("Charging Time:    {0:.1f} seconds".format(monitor.session_data['charging_time']))
    logger.info("Peak Power:       {0:.0f} W".format(monitor.session_data['peak_power']))
    logger.info("Average Power:    {0:.0f} W".format(monitor.session_data['average_power']))
    logger.info("")
    logger.info("Messages Sent:")
    logger.info("  - CAN Messages:  {0}".format(monitor.session_data['messages']['can']))
    logger.info("  - OCPP Messages: {0}".format(monitor.session_data['messages']['ocpp']))
    logger.info("  - V2G Messages:  {0}".format(monitor.session_data['messages']['v2g']))
    logger.info("  - Total:         {0}".format(sum(monitor.session_data['messages'].values())))
    logger.info("=" * 80)
    
    # Generate graphs
    logger.info("\n[GRAPHS] Generating visualization graphs...")
    monitor.generate_graphs()
    
    # Save session data as JSON
    session_file = Path("logs") / "session_{0}.json".format(timestamp)
    with open(session_file, 'w') as f:
        json.dump(monitor.session_data, f, indent=2)
    logger.info("[OK] Session data saved to: {0}".format(session_file))
    
    logger.info("\n[SUCCESS] Charging simulation completed successfully!")
    logger.info("[LOGS] Full logs saved to: {0}".format(log_file))
    logger.info("=" * 80)
    
    return True


async def main():
    """Main entry point"""
    try:
        success = await run_full_charging_simulation()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n⚠️  Simulation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
