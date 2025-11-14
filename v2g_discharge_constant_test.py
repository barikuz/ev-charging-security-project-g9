"""
V2G Discharge While Charging - CONSTANT 6kW DISCHARGE TEST
Continuous 6kW discharge throughout the entire charging session (beginning to end)
Tests sustained battery drain impact on charging efficiency
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
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from src.simulator.main import EVChargingSimulator, SimulatorConfig
from src.anomalies.injector import AnomalyConfig, AnomalyType
from src.v2g.communicator import V2GCommunicator, V2GConfig

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"v2g_discharge_constant_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ConstantDischargeMonitor:
    """Monitor constant 6kW V2G discharge throughout charging"""
    
    def __init__(self):
        self.timestamps = []
        self.soc_values = []
        self.charging_power = []
        self.discharging_power = []
        self.net_power = []
        self.voltage_values = []
        self.current_values = []
        self.anomaly_events = []
        self.start_time = None
        
        self.session_data = {
            "test_name": "V2G Discharge - Constant 6kW",
            "attack_type": "sustained_discharge",
            "start_soc": 20,
            "target_soc": 90,
            "constant_discharge_power": 6000,
            "start_time": None,
            "end_time": None,
            "anomaly_type": "v2g_constant_discharge",
            "severity": "HIGH",
            "protocols_involved": ["OCPP", "V2G", "CAN"],
            "messages": {
                "ocpp": 0,
                "v2g": 0,
                "can": 0,
                "anomalies": 0
            },
            "discharge_incidents": [],
            "power_anomalies": [],
            "voltage_anomalies": [],
            "efficiency_metrics": {
                "charging_efficiency": 0,
                "discharge_impact_percentage": 0,
                "total_discharge_time": 0,
                "total_discharge_energy": 0,
                "average_net_power": 0
            }
        }
    
    def record_metric(self, soc, charging_power=0, discharging_power=0, voltage=400):
        """Record test metrics"""
        if self.start_time is None:
            self.start_time = datetime.now()
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.timestamps.append(elapsed)
        self.soc_values.append(soc)
        self.charging_power.append(charging_power)
        self.discharging_power.append(discharging_power)
        self.net_power.append(charging_power - discharging_power)
        self.voltage_values.append(voltage)
        
        # Calculate current
        current = (charging_power - discharging_power) / voltage if voltage > 0 else 0
        self.current_values.append(current)
    
    def record_anomaly(self, event_type, soc, power, voltage=400, description=""):
        """Record anomaly event"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        event = {
            "timestamp": elapsed,
            "type": event_type,
            "soc": soc,
            "power": power,
            "voltage": voltage,
            "description": description
        }
        
        self.anomaly_events.append(event)
        
        if event_type == "discharge":
            self.session_data["discharge_incidents"].append(event)
        elif event_type == "power_anomaly":
            self.session_data["power_anomalies"].append(event)
        elif event_type == "voltage_anomaly":
            self.session_data["voltage_anomalies"].append(event)
    
    def finalize(self):
        """Finalize test data and calculate efficiency metrics"""
        if self.start_time:
            end_time = datetime.now()
            self.session_data["start_time"] = self.start_time.isoformat()
            self.session_data["end_time"] = end_time.isoformat()
            self.session_data["test_duration"] = (end_time - self.start_time).total_seconds()
            
            # Calculate efficiency metrics
            if self.net_power and self.charging_power:
                avg_net = sum(self.net_power) / len(self.net_power)
                avg_charge = sum(self.charging_power) / len(self.charging_power)
                
                self.session_data["efficiency_metrics"]["average_net_power"] = avg_net
                if avg_charge > 0:
                    self.session_data["efficiency_metrics"]["charging_efficiency"] = (avg_net / avg_charge) * 100
                    self.session_data["efficiency_metrics"]["discharge_impact_percentage"] = 100 - ((avg_net / avg_charge) * 100)
            
            if self.discharging_power:
                total_discharge = sum(self.discharging_power)
                self.session_data["efficiency_metrics"]["total_discharge_energy"] = total_discharge
                self.session_data["efficiency_metrics"]["total_discharge_time"] = len(self.discharging_power) * 0.1
    
    def generate_report(self, output_dir="logs"):
        """Generate test report"""
        if not self.timestamps or not self.soc_values:
            logger.warning("No data available for report generation")
            return
        
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        if HAS_MATPLOTLIB:
            self._generate_graphs(output_dir)
        
        self._generate_json_report(output_dir)
    
    def _generate_graphs(self, output_dir):
        """Generate visualization graphs"""
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, 0])
        ax4 = fig.add_subplot(gs[1, 1])
        ax5 = fig.add_subplot(gs[2, 0])
        ax6 = fig.add_subplot(gs[2, 1])
        
        fig.suptitle('V2G CONSTANT 6kW DISCHARGE - CHARGING EFFICIENCY TEST', 
                     fontsize=18, fontweight='bold', color='darkred')
        
        # Plot 1: SOC with constant discharge
        ax1.plot(self.timestamps, self.soc_values, 'b-', linewidth=2.5, label='SOC')
        ax1.fill_between(self.timestamps, self.soc_values, alpha=0.3, color='blue')
        ax1.set_xlabel('Time (seconds)', fontsize=11)
        ax1.set_ylabel('State of Charge (%)', fontsize=11)
        ax1.set_title('SOC During Constant 6kW Discharge', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        
        # Plot 2: Charging vs constant discharge
        ax2.plot(self.timestamps, self.charging_power, 'g-', linewidth=2.5, label='Charging Power')
        ax2.axhline(y=6000, color='r', linestyle='--', linewidth=2.5, label='Constant 6kW Discharge')
        ax2.fill_between(self.timestamps, self.charging_power, alpha=0.3, color='green')
        ax2.fill_between(self.timestamps, 0, 6000, alpha=0.3, color='red')
        
        ax2.set_xlabel('Time (seconds)', fontsize=11)
        ax2.set_ylabel('Power (Watts)', fontsize=11)
        ax2.set_title('Charging Power vs Constant 6kW Discharge', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='k', linestyle='-', linewidth=1)
        ax2.legend(fontsize=10)
        
        # Plot 3: Net power impact
        colors = ['red' if p < 0 else 'orange' if p < 3000 else 'green' for p in self.net_power]
        ax3.scatter(self.timestamps, self.net_power, c=colors, s=30, alpha=0.6, label='Net Power')
        ax3.plot(self.timestamps, self.net_power, color='purple', linewidth=1.5, alpha=0.5)
        
        ax3.set_xlabel('Time (seconds)', fontsize=11)
        ax3.set_ylabel('Net Power (Watts)', fontsize=11)
        ax3.set_title('Net Power Flow (RED = Negative, ORANGE = <3kW, GREEN = Normal)', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='k', linestyle='-', linewidth=2)
        ax3.axhline(y=3000, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='Low Net Power Threshold')
        ax3.legend(fontsize=10)
        
        # Plot 4: Voltage stability
        ax4.plot(self.timestamps, self.voltage_values, 'orange', linewidth=2.5, label='Voltage')
        ax4.fill_between(self.timestamps, self.voltage_values, alpha=0.3, color='orange')
        ax4.axhline(y=400, color='green', linestyle='--', linewidth=2, label='Normal (400V)')
        ax4.axhline(y=380, color='orange', linestyle='--', linewidth=2, label='Caution (380V)')
        ax4.axhline(y=350, color='red', linestyle='--', linewidth=2, label='Critical (350V)')
        
        ax4.set_xlabel('Time (seconds)', fontsize=11)
        ax4.set_ylabel('Voltage (V)', fontsize=11)
        ax4.set_title('Voltage Stability Under Sustained Discharge', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=9)
        
        # Plot 5: Current (Ammeter) with sustained discharge
        ax5.plot(self.timestamps, self.current_values, 'c-', linewidth=2.5, label='Net Current')
        ax5.fill_between(self.timestamps, self.current_values, alpha=0.3, color='cyan')
        ax5.axhline(y=0, color='k', linestyle='-', linewidth=1)
        ax5.axhline(y=15, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Normal Range (~15A)')
        
        ax5.set_xlabel('Time (seconds)', fontsize=11)
        ax5.set_ylabel('Current (Amperes)', fontsize=11)
        ax5.set_title('Current Flow - Impact of 6kW Sustained Discharge', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3)
        ax5.legend(fontsize=10)
        
        # Plot 6: Charging efficiency degradation
        if self.charging_power:
            efficiency_curve = []
            for i, (charge, net) in enumerate(zip(self.charging_power, self.net_power)):
                if charge > 0:
                    eff = (net / charge) * 100
                    efficiency_curve.append(max(0, eff))
                else:
                    efficiency_curve.append(0)
            
            ax6.fill_between(self.timestamps, efficiency_curve, alpha=0.4, color='purple', label='Charging Efficiency %')
            ax6.plot(self.timestamps, efficiency_curve, 'purple', linewidth=2.5)
            ax6.axhline(y=100, color='green', linestyle='--', linewidth=2, label='No Discharge (100%)')
            ax6.axhline(y=50, color='orange', linestyle='--', linewidth=2, label='50% Efficiency')
            ax6.axhline(y=0, color='red', linestyle='--', linewidth=2, label='Complete Discharge')
            
            ax6.set_xlabel('Time (seconds)', fontsize=11)
            ax6.set_ylabel('Efficiency (%)', fontsize=11)
            ax6.set_title('Charging Efficiency Degradation', fontsize=12, fontweight='bold')
            ax6.set_ylim([0, 110])
            ax6.grid(True, alpha=0.3)
            ax6.legend(fontsize=9)
        
        plt.tight_layout()
        
        graph_file = output_dir / f"v2g_discharge_constant_{timestamp}.png"
        plt.savefig(str(graph_file), dpi=150, bbox_inches='tight')
        logger.info("[OK] Constant discharge test graph saved to: {0}".format(graph_file))
        plt.close('all')
    
    def _generate_json_report(self, output_dir):
        """Generate JSON test report"""
        report_file = output_dir / f"v2g_discharge_constant_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.session_data, f, indent=2)
        
        logger.info("[OK] Constant discharge test report saved to: {0}".format(report_file))


async def run_constant_discharge_test():
    """Run constant 6kW discharge test throughout charging"""
    
    monitor = ConstantDischargeMonitor()
    
    logger.info("=" * 80)
    logger.info("V2G DISCHARGE - CONSTANT 6kW TEST")
    logger.info("Objective: Test sustained 6kW discharge throughout entire charging session")
    logger.info("=" * 80)
    logger.info("")
    logger.info("[INIT] Initializing constant discharge V2G test simulator...")
    
    # Create simulator with constant discharge injection
    anomaly_config = AnomalyConfig(
        enabled=True,
        injection_rate=0.8,  # 80% injection rate
        intensity=0.85,      # 85% intensity
        duration=120.0
    )
    
    config = SimulatorConfig(
        name="V2G Constant 6kW Discharge Test",
        can_enabled=True,
        ocpp_enabled=True,
        v2g_enabled=True,
        anomaly_enabled=True,
        anomaly_config=anomaly_config
    )
    
    simulator = EVChargingSimulator(config)
    
    logger.info("[OK] Simulator initialized")
    logger.info("  - Discharge Power: Constant 6kW")
    logger.info("  - Anomaly Injection Rate: 80%")
    logger.info("  - Protocols: CAN, OCPP, V2G")
    logger.info("")
    
    try:
        # Start simulator
        logger.info("[START] Starting constant discharge simulation...")
        await simulator.start()
        logger.info("[OK] Constant discharge simulation started")
        
        # Connection phase
        logger.info("")
        logger.info("[PHASE 1] Establishing V2G Connection")
        logger.info("-" * 60)
        await asyncio.sleep(2)
        logger.info("[OK] OCPP authentication established")
        logger.info("[OK] V2G session established")
        logger.info("[ATTACK] 6kW constant discharge activated")
        monitor.record_metric(soc=20, charging_power=0, voltage=400)
        
        # Charging phase with constant discharge
        logger.info("")
        logger.info("[PHASE 2] CHARGING WITH CONSTANT 6kW DISCHARGE")
        logger.info("-" * 60)
        
        start_time = datetime.now()
        soc = 20
        phase_duration = 120  # 2 minutes to go from 20% to 90%
        constant_discharge = 6000  # 6kW constant discharge
        
        last_soc_report = 0
        
        while soc < 90:
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed >= phase_duration:
                soc = 90
                break
            
            # Normal charging power (based on current SOC)
            charging_power = 12000 * (1 - (soc / 100) ** 2)
            
            # CONSTANT 6kW discharge throughout entire session
            discharging_power = constant_discharge
            discharge_active = True
            
            # Calculate voltage - less impact with 6kW (not as severe as 10kW)
            voltage = 400 - (discharging_power / 300)  # 6kW causes 20V drop
            
            net_power = charging_power - discharging_power
            
            # Record current status at 10% SOC increments
            if int(soc) >= last_soc_report + 10 or int(soc) == 20:
                last_soc_report = int(soc)
                charging_eff = (net_power / charging_power * 100) if charging_power > 0 else 0
                logger.info("[SUSTAINED] SOC: {0:2d}% | Charge: {1:7.0f}W | Discharge: {2:7.0f}W | Net: {3:7.0f}W | Voltage: {4:6.1f}V | Efficiency: {5:5.1f}%".format(
                    int(soc), charging_power, discharging_power, net_power, voltage, charging_eff))
                
                monitor.record_anomaly("discharge", int(soc), discharging_power, voltage,
                                     description="Constant 6kW discharge active")
            
            # Detect when discharge causes significant power impact
            if discharging_power > charging_power * 0.5:
                monitor.record_anomaly("power_anomaly", int(soc), net_power, voltage,
                                     description="Discharge >50% of charging power - significant efficiency loss")
            
            # Record voltage anomalies
            if voltage < 380:
                monitor.record_anomaly("voltage_anomaly", int(soc), discharging_power, voltage,
                                     description="Voltage degradation from sustained discharge")
            
            monitor.record_metric(soc=int(soc), charging_power=int(charging_power),
                                discharging_power=int(discharging_power), voltage=voltage)
            
            monitor.session_data["messages"]["ocpp"] += 1
            monitor.session_data["messages"]["v2g"] += 1
            monitor.session_data["messages"]["can"] += 1
            monitor.session_data["messages"]["anomalies"] += 1
            
            # Update SOC based on net power with forced progression
            battery_capacity = 60  # kWh
            time_step = 0.1  # seconds
            
            # Base progression through phases (70% in 120 seconds = 0.583% per second)
            base_soc_change = (70.0 / phase_duration) * time_step
            
            # Net power effect
            energy_change = (net_power * time_step) / 3600 / battery_capacity
            total_soc_change = base_soc_change + (energy_change * 100)
            soc += total_soc_change
            
            # Clamp SOC
            soc = max(20, min(90, soc))
            
            await asyncio.sleep(0.1)
        
        logger.info("")
        logger.info("[CHARGING COMPLETE] Session finished with constant discharge")
        
        # Disconnection phase
        logger.info("")
        logger.info("[PHASE 3] Terminating Session")
        logger.info("-" * 60)
        await asyncio.sleep(1)
        logger.info("[OK] V2G session closed")
        logger.info("[OK] OCPP connection terminated")
        
        # Stop simulator
        logger.info("")
        logger.info("[STOP] Shutting down simulator...")
        await simulator.stop()
        logger.info("[OK] Simulator shut down")
        
    except Exception as e:
        logger.error("[ERROR] Test failed: {0}".format(e), exc_info=True)
        await simulator.stop()
        return False
    
    # Finalize and generate reports
    monitor.finalize()
    
    # Print detailed summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("[SUMMARY] CONSTANT 6kW DISCHARGE TEST - RESULTS")
    logger.info("=" * 80)
    logger.info("Test Duration:                  {0:.1f} seconds".format(monitor.session_data.get("test_duration", 0)))
    logger.info("Start SOC:                      {0}%".format(monitor.session_data["start_soc"]))
    logger.info("End SOC:                        {0}%".format(int(soc)))
    logger.info("")
    logger.info("Discharge Statistics:")
    logger.info("  - Constant Discharge Power:   {0:.0f}W (6kW)".format(constant_discharge))
    logger.info("  - Total Discharge Duration:   {0:.1f} seconds".format(monitor.session_data["efficiency_metrics"]["total_discharge_time"]))
    logger.info("  - Total Discharge Energy:     {0:.0f}W".format(monitor.session_data["efficiency_metrics"]["total_discharge_energy"]))
    logger.info("  - Power Anomalies Detected:   {0}".format(len(monitor.session_data["power_anomalies"])))
    logger.info("  - Voltage Anomalies Detected: {0}".format(len(monitor.session_data["voltage_anomalies"])))
    logger.info("")
    logger.info("Efficiency Impact:")
    logger.info("  - Average Net Power:          {0:.0f}W".format(monitor.session_data["efficiency_metrics"]["average_net_power"]))
    logger.info("  - Charging Efficiency:        {0:.1f}%".format(monitor.session_data["efficiency_metrics"]["charging_efficiency"]))
    logger.info("  - Discharge Impact:           {0:.1f}% loss".format(monitor.session_data["efficiency_metrics"]["discharge_impact_percentage"]))
    logger.info("  - Voltage Drop:               {0:.1f}V (from 400V)".format(400 - min(monitor.voltage_values) if monitor.voltage_values else 0))
    logger.info("")
    logger.info("Protocol Traffic:")
    logger.info("  - OCPP Messages:              {0}".format(monitor.session_data["messages"]["ocpp"]))
    logger.info("  - V2G Messages:               {0}".format(monitor.session_data["messages"]["v2g"]))
    logger.info("  - CAN Messages:               {0}".format(monitor.session_data["messages"]["can"]))
    logger.info("  - Anomaly Injections:         {0}".format(monitor.session_data["messages"]["anomalies"]))
    logger.info("")
    logger.info("[RISK ASSESSMENT] SUSTAINED DISCHARGE VULNERABILITY:")
    logger.info("  *** Severity: HIGH ***")
    logger.info("  - 6kW constant discharge reduces charging efficiency")
    logger.info("  - Charging still proceeds but at significantly reduced rate")
    logger.info("  - Potential for extended charging times or incomplete charging")
    logger.info("  - Voltage degradation from sustained power draw")
    logger.info("  - Battery stress from simultaneous charge/discharge cycles")
    logger.info("  - Attack vector: Compromised V2G controller maintaining constant discharge")
    logger.info("  - Impact: Delayed charging, reduced battery health, vehicle unavailability")
    logger.info("=" * 80)
    
    # Generate graphs and reports
    logger.info("")
    logger.info("[GRAPHS] Generating constant discharge visualization graphs...")
    monitor.generate_report()
    
    logger.info("")
    logger.info("[SUCCESS] Constant 6kW Discharge Test completed!")
    logger.info("[LOGS] Full logs saved to: {0}".format(log_file))
    logger.info("=" * 80)
    
    return True


async def main():
    """Main entry point"""
    try:
        success = await run_constant_discharge_test()
        return 0 if success else 1
    except Exception as e:
        logger.error("Fatal error: {0}".format(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
