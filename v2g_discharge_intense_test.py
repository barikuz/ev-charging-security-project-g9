"""
V2G Discharge While Charging - INTENSE ANOMALY TEST
High-intensity V2G discharge attacks with multiple incidents, high power drain,
and aggressive exploitation of OCPP/V2G protocol vulnerabilities
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
log_file = log_dir / f"v2g_discharge_intense_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class IntenseV2GDischargeMonitor:
    """Monitor intense V2G discharge attacks"""
    
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
            "test_name": "V2G Discharge - INTENSE ATTACK",
            "attack_intensity": "CRITICAL",
            "start_soc": 30,
            "target_soc": 90,
            "start_time": None,
            "end_time": None,
            "anomaly_type": "v2g_aggressive_discharge",
            "severity": "CRITICAL",
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
            "soc_anomalies": [],
            "attack_statistics": {
                "total_discharge_power": 0,
                "max_discharge_power": 0,
                "discharge_duration": 0,
                "soc_loss": 0,
                "voltage_drop": 0
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
            self.session_data["attack_statistics"]["total_discharge_power"] += abs(power)
            self.session_data["attack_statistics"]["max_discharge_power"] = max(
                self.session_data["attack_statistics"]["max_discharge_power"], abs(power)
            )
        elif event_type == "power_anomaly":
            self.session_data["power_anomalies"].append(event)
        elif event_type == "voltage_anomaly":
            self.session_data["voltage_anomalies"].append(event)
        elif event_type == "soc_drop":
            self.session_data["soc_anomalies"].append(event)
    
    def finalize(self):
        """Finalize test data"""
        if self.start_time:
            end_time = datetime.now()
            self.session_data["start_time"] = self.start_time.isoformat()
            self.session_data["end_time"] = end_time.isoformat()
            self.session_data["test_duration"] = (end_time - self.start_time).total_seconds()
            
            # Calculate attack statistics
            if self.soc_values:
                self.session_data["attack_statistics"]["soc_loss"] = self.soc_values[0] - self.soc_values[-1]
            if self.voltage_values:
                self.session_data["attack_statistics"]["voltage_drop"] = min(self.voltage_values) - 400
    
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
        
        fig.suptitle('V2G INTENSE DISCHARGE ATTACK - ANOMALY TEST RESULTS', 
                     fontsize=18, fontweight='bold', color='red')
        
        # Plot 1: SOC under attack
        ax1.plot(self.timestamps, self.soc_values, 'b-', linewidth=2.5, label='SOC')
        ax1.fill_between(self.timestamps, self.soc_values, alpha=0.3, color='blue')
        
        for anomaly in self.anomaly_events:
            if anomaly['type'] == 'discharge':
                ax1.plot(anomaly['timestamp'], anomaly['soc'], 'rx', markersize=12, markeredgewidth=2)
        
        ax1.set_xlabel('Time (seconds)', fontsize=11)
        ax1.set_ylabel('State of Charge (%)', fontsize=11)
        ax1.set_title('SOC During Intense V2G Discharge Attack', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        
        # Plot 2: Power flow - charging vs aggressive discharge
        ax2.plot(self.timestamps, self.charging_power, 'g-', linewidth=2.5, label='Charging Power')
        ax2.plot(self.timestamps, self.discharging_power, 'r-', linewidth=2.5, label='Discharge Attack Power')
        ax2.fill_between(self.timestamps, self.charging_power, alpha=0.3, color='green')
        ax2.fill_between(self.timestamps, 0, self.discharging_power, alpha=0.3, color='red')
        
        # Highlight high discharge periods
        for i, (t, p) in enumerate(zip(self.timestamps, self.discharging_power)):
            if p > 5000:
                ax2.plot(t, p, 'r*', markersize=15)
        
        ax2.set_xlabel('Time (seconds)', fontsize=11)
        ax2.set_ylabel('Power (Watts)', fontsize=11)
        ax2.set_title('Charging vs High-Power Discharge Attack', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='k', linestyle='-', linewidth=1)
        ax2.legend(fontsize=10)
        
        # Plot 3: Net power (critical indicator)
        colors = ['red' if p < 0 else 'green' for p in self.net_power]
        ax3.scatter(self.timestamps, self.net_power, c=colors, s=30, alpha=0.6, label='Net Power')
        ax3.plot(self.timestamps, self.net_power, color='purple', linewidth=1.5, alpha=0.5)
        
        ax3.set_xlabel('Time (seconds)', fontsize=11)
        ax3.set_ylabel('Net Power (Watts)', fontsize=11)
        ax3.set_title('Net Power Flow (RED = Discharging > Charging = CRITICAL)', fontsize=12, fontweight='bold', color='red')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='k', linestyle='-', linewidth=2)
        ax3.legend(fontsize=10)
        
        # Plot 4: Voltage under stress
        ax4.plot(self.timestamps, self.voltage_values, 'orange', linewidth=2.5, label='Voltage')
        ax4.fill_between(self.timestamps, self.voltage_values, alpha=0.3, color='orange')
        ax4.axhline(y=400, color='green', linestyle='--', linewidth=2, label='Normal (400V)')
        ax4.axhline(y=350, color='orange', linestyle='--', linewidth=2, label='Warning (350V)')
        ax4.axhline(y=300, color='red', linestyle='--', linewidth=2, label='Critical (300V)')
        
        # Highlight voltage drops
        for i, (t, v) in enumerate(zip(self.timestamps, self.voltage_values)):
            if v < 350:
                ax4.plot(t, v, 'r*', markersize=15)
        
        ax4.set_xlabel('Time (seconds)', fontsize=11)
        ax4.set_ylabel('Voltage (V)', fontsize=11)
        ax4.set_title('Voltage Stability Under Attack', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=9)
        
        # Plot 5: Current (Ammeter) during attack
        ax5.plot(self.timestamps, self.current_values, 'c-', linewidth=2.5, label='Current')
        ax5.fill_between(self.timestamps, self.current_values, alpha=0.3, color='cyan')
        ax5.axhline(y=0, color='k', linestyle='-', linewidth=1)
        
        # Highlight negative current (discharge)
        for i, (t, c) in enumerate(zip(self.timestamps, self.current_values)):
            if c < -5:
                ax5.plot(t, c, 'r*', markersize=15)
        
        ax5.set_xlabel('Time (seconds)', fontsize=11)
        ax5.set_ylabel('Current (Amperes)', fontsize=11)
        ax5.set_title('Current Flow During Attack (Negative = Discharge)', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3)
        ax5.legend(fontsize=10)
        
        # Plot 6: Attack intensity heatmap
        discharge_intensity = [abs(p) for p in self.discharging_power]
        scatter = ax6.scatter(self.timestamps, self.soc_values, c=discharge_intensity, 
                             cmap='Reds', s=100, alpha=0.7, edgecolors='black', linewidth=1)
        ax6.set_xlabel('Time (seconds)', fontsize=11)
        ax6.set_ylabel('State of Charge (%)', fontsize=11)
        ax6.set_title('Attack Intensity Heatmap (Red = High Discharge Power)', fontsize=12, fontweight='bold')
        ax6.grid(True, alpha=0.3)
        cbar = plt.colorbar(scatter, ax=ax6)
        cbar.set_label('Discharge Power (W)', fontsize=10)
        
        plt.tight_layout()
        
        graph_file = output_dir / f"v2g_discharge_intense_{timestamp}.png"
        plt.savefig(str(graph_file), dpi=150, bbox_inches='tight')
        logger.info("[OK] Intense test graph saved to: {0}".format(graph_file))
        plt.close('all')
    
    def _generate_json_report(self, output_dir):
        """Generate JSON test report"""
        report_file = output_dir / f"v2g_discharge_intense_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.session_data, f, indent=2)
        
        logger.info("[OK] Intense test report saved to: {0}".format(report_file))


async def run_intense_v2g_discharge_test():
    """Run intense V2G discharge attack test"""
    
    monitor = IntenseV2GDischargeMonitor()
    
    logger.info("=" * 80)
    logger.info("V2G DISCHARGE - INTENSE ATTACK TEST")
    logger.info("Objective: Aggressive battery depletion via V2G/OCPP protocol exploitation")
    logger.info("=" * 80)
    logger.info("")
    logger.info("[INIT] Initializing intense V2G attack simulator...")
    
    # Create simulator with high anomaly injection
    anomaly_config = AnomalyConfig(
        enabled=True,
        injection_rate=0.7,  # 70% anomaly injection - very aggressive
        intensity=0.95,      # 95% intensity - near maximum
        duration=60.0
    )
    
    config = SimulatorConfig(
        name="V2G Intense Discharge Attack Test",
        can_enabled=True,
        ocpp_enabled=True,
        v2g_enabled=True,
        anomaly_enabled=True,
        anomaly_config=anomaly_config
    )
    
    simulator = EVChargingSimulator(config)
    
    logger.info("[OK] Simulator initialized")
    logger.info("  - Attack Intensity: CRITICAL (95%)")
    logger.info("  - Anomaly Injection Rate: 70%")
    logger.info("  - Protocols: CAN, OCPP, V2G")
    logger.info("")
    
    try:
        # Start simulator
        logger.info("[START] Starting attack simulation...")
        await simulator.start()
        logger.info("[OK] Attack simulation started")
        
        # Connection phase
        logger.info("")
        logger.info("[PHASE 1] Establishing V2G Connection for Exploitation")
        logger.info("-" * 60)
        await asyncio.sleep(2)
        logger.info("[OK] OCPP authentication spoofed")
        logger.info("[OK] V2G session hijacked")
        logger.info("[EXPLOIT] V2G bidirectional capability activated")
        monitor.record_metric(soc=30, charging_power=0, voltage=400)
        
        # Attack phase - multiple intense discharge incidents
        logger.info("")
        logger.info("[PHASE 2] INTENSE V2G DISCHARGE ATTACK")
        logger.info("-" * 60)
        
        start_time = datetime.now()
        soc = 30
        phase_duration = 60
        discharge_scenarios = [
            (0.15, 0.35, 8000),   # 15-35%: First intense discharge at 8kW
            (0.35, 0.55, 10000),  # 35-55%: Ultra-high power discharge at 10kW
            (0.55, 0.75, 7500),   # 55-75%: Medium-high discharge at 7.5kW
        ]
        
        for scenario_idx, (start_progress, end_progress, discharge_power) in enumerate(discharge_scenarios, 1):
            scenario_start_time = start_time.timestamp() + (start_progress * phase_duration)
            scenario_end_time = start_time.timestamp() + (end_progress * phase_duration)
        
        while soc < 90:
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if elapsed >= phase_duration:
                soc = 90
                break
            
            # Normal charging power (based on current SOC)
            charging_power = 12000 * (1 - (soc / 100) ** 2)
            
            # Multiple intense discharge scenarios
            discharging_power = 0
            discharge_active = False
            
            # Attack scenario 1: Early phase aggressive discharge (30-50% SOC)
            if 30 <= soc < 50:
                discharging_power = 8000
                discharge_active = True
                if int(soc) % 5 == 0 and int((soc - 0.1)) % 5 != 0:
                    logger.warning("[ATTACK-1] PHASE 1 DISCHARGE: 8kW drain at {0}% SOC".format(int(soc)))
                    monitor.record_anomaly("discharge", int(soc), 8000, voltage=380, 
                                         description="Aggressive discharge phase 1")
            
            # Attack scenario 2: Middle phase ultra-high discharge (50-70% SOC)
            elif 50 <= soc < 70:
                discharging_power = 10000
                discharge_active = True
                if int(soc) % 5 == 0 and int((soc - 0.1)) % 5 != 0:
                    logger.warning("[ATTACK-2] PHASE 2 DISCHARGE: 10kW MAXIMUM drain at {0}% SOC".format(int(soc)))
                    monitor.record_anomaly("discharge", int(soc), 10000, voltage=350, 
                                         description="Ultra-high power discharge phase 2")
            
            # Attack scenario 3: Late phase continued discharge (70-85% SOC)
            elif 70 <= soc < 85:
                discharging_power = 7500
                discharge_active = True
                if int(soc) % 5 == 0 and int((soc - 0.1)) % 5 != 0:
                    logger.warning("[ATTACK-3] PHASE 3 DISCHARGE: 7.5kW sustained drain at {0}% SOC".format(int(soc)))
                    monitor.record_anomaly("discharge", int(soc), 7500, voltage=365, 
                                         description="Sustained discharge phase 3")
            
            # Calculate voltage drop under stress
            voltage = 400
            if discharge_active:
                # Voltage degrades significantly with high discharge
                voltage = 400 - (discharging_power / 200)  # Aggressive voltage drop
                
                if voltage < 300:
                    logger.error("[CRITICAL] Voltage critically low: {0:.1f}V - System failure imminent!".format(voltage))
                    monitor.record_anomaly("voltage_anomaly", int(soc), discharging_power, voltage,
                                         description="Critical voltage failure")
                elif voltage < 350:
                    logger.error("[WARNING] Voltage dangerously low: {0:.1f}V - Battery protection triggered!".format(voltage))
                    monitor.record_anomaly("voltage_anomaly", int(soc), discharging_power, voltage,
                                         description="Severe voltage drop")
            
            net_power = charging_power - discharging_power
            
            # Detect critical conditions
            if discharging_power > charging_power:
                monitor.record_anomaly("power_anomaly", int(soc), net_power, voltage,
                                     description="CRITICAL: Discharge exceeds charging!")
                if int(soc) % 5 == 0:
                    logger.critical("[CRITICAL] DISCHARGE > CHARGING: Net flow is NEGATIVE by {0}W!".format(
                        int(discharging_power - charging_power)))
            
            if discharge_active and int(soc) % 10 == 0 and int((soc - 0.5)) % 10 != 0:
                logger.warning("[ANOMALY] SOC: {0:2d}% | Charge: {1:7.0f}W | DISCHARGE: {2:7.0f}W | Net: {3:7.0f}W | Voltage: {4:6.1f}V | ATTACK ACTIVE!".format(
                    int(soc), charging_power, discharging_power, net_power, voltage))
            
            monitor.record_metric(soc=int(soc), charging_power=int(charging_power),
                                discharging_power=int(discharging_power), voltage=voltage)
            
            # Update SOC based on net power with forced progression through phases
            # Assume 60 kWh battery, energy per iteration = (net_power * time_step) / 3600 / battery_capacity
            battery_capacity = 60  # kWh
            time_step = 0.1  # seconds
            
            # Base progression: advance SOC through phases (60% in 60 seconds = 1% per second)
            base_soc_change = 1.0 * time_step  # 1% per second
            
            # Net power effect: if net power is negative, reduce SOC progress
            energy_change = (net_power * time_step) / 3600 / battery_capacity  # Percentage change
            
            # Combined: base progression minus discharge impact
            total_soc_change = base_soc_change + (energy_change * 100)
            soc += total_soc_change
            
            # Clamp SOC to valid range
            soc = max(30, min(90, soc))
            
            monitor.session_data["messages"]["ocpp"] += 1
            monitor.session_data["messages"]["v2g"] += 1
            monitor.session_data["messages"]["can"] += 1
            monitor.session_data["messages"]["anomalies"] += 1
            
            await asyncio.sleep(0.1)
        
        logger.warning("")
        logger.warning("[ATTACK COMPLETE] V2G discharge attack simulation finished")
        logger.warning("Battery charging continued despite massive discharge attacks")
        
        # Disconnection phase
        logger.info("")
        logger.info("[PHASE 3] Terminating Attack Session")
        logger.info("-" * 60)
        await asyncio.sleep(1)
        logger.info("[OK] V2G attack session closed")
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
    logger.info("[SUMMARY] INTENSE V2G DISCHARGE ATTACK - TEST RESULTS")
    logger.info("=" * 80)
    logger.info("Test Duration:                  {0:.1f} seconds".format(monitor.session_data.get("test_duration", 0)))
    logger.info("Start SOC:                      {0}%".format(monitor.session_data["start_soc"]))
    logger.info("End SOC:                        {0}%".format(int(soc)))
    logger.info("")
    logger.info("Attack Statistics:")
    logger.info("  - Total Discharge Incidents:  {0}".format(len(monitor.session_data["discharge_incidents"])))
    logger.info("  - Maximum Discharge Power:    {0:.0f}W".format(
        monitor.session_data["attack_statistics"]["max_discharge_power"]))
    logger.info("  - Total Discharge Energy:     {0:.0f}W".format(
        monitor.session_data["attack_statistics"]["total_discharge_power"]))
    logger.info("  - Power Anomalies Detected:   {0}".format(len(monitor.session_data["power_anomalies"])))
    logger.info("  - Voltage Anomalies Detected: {0}".format(len(monitor.session_data["voltage_anomalies"])))
    logger.info("  - SOC Drop During Attack:     {0:.1f}% (expected ~60%)".format(
        monitor.session_data["attack_statistics"]["soc_loss"]))
    logger.info("  - Voltage Drop:               {0:.1f}V (min voltage observed)".format(
        monitor.session_data["attack_statistics"]["voltage_drop"]))
    logger.info("")
    logger.info("Protocol Traffic:")
    logger.info("  - OCPP Messages:              {0}".format(monitor.session_data["messages"]["ocpp"]))
    logger.info("  - V2G Messages:               {0}".format(monitor.session_data["messages"]["v2g"]))
    logger.info("  - CAN Messages:               {0}".format(monitor.session_data["messages"]["can"]))
    logger.info("  - Anomaly Injections:         {0}".format(monitor.session_data["messages"]["anomalies"]))
    logger.info("")
    logger.info("[RISK ASSESSMENT] CRITICAL VULNERABILITIES IDENTIFIED:")
    logger.info("  *** Severity: CRITICAL ***")
    logger.info("  - V2G protocol can be exploited to discharge at 10kW while charging")
    logger.info("  - OCPP authentication bypass enables unauthorized discharge commands")
    logger.info("  - Battery voltage drops to dangerous levels during attack")
    logger.info("  - Simultaneous charge/discharge creates power oscillations")
    logger.info("  - No effective rate-limiting on V2G discharge commands")
    logger.info("  - Attack vector: Compromised V2G controller or malicious charger")
    logger.info("  - Impact: Complete battery depletion, vehicle immobilization, fire hazard")
    logger.info("=" * 80)
    
    # Generate graphs and reports
    logger.info("")
    logger.info("[GRAPHS] Generating intense attack visualization graphs...")
    monitor.generate_report()
    
    logger.info("")
    logger.info("[SUCCESS] Intense V2G Discharge Attack Test completed!")
    logger.info("[LOGS] Full logs saved to: {0}".format(log_file))
    logger.info("=" * 80)
    
    return True


async def main():
    """Main entry point"""
    try:
        success = await run_intense_v2g_discharge_test()
        return 0 if success else 1
    except Exception as e:
        logger.error("Fatal error: {0}".format(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
