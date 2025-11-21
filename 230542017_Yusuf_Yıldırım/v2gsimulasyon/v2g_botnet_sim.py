"""
V2G Botnet Simulation Module
=============================

Professional simulation framework for analyzing V2G (Vehicle-to-Grid) botnet attacks
on electric vehicle charging infrastructure using OCPP protocol.

Author: Research Team
Date: November 2025
Version: 2.0
License: MIT
"""

import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from enum import Enum


# =========================
# Configuration & Constants
# =========================

class OCPPCommand(Enum):
    """OCPP protocol command types."""
    REMOTE_START = "RemoteStartTransaction"
    REMOTE_STOP = "RemoteStopTransaction"


@dataclass
class SimConfig:
    """
    Simulation configuration parameters.
    
    Attributes:
        T_max: Total simulation duration in seconds
        dt: Time step size in seconds
        base_load_kw: Base grid load excluding EVs in kW
        n_stations: Total number of charging stations
        attack_time_s: Attack trigger time in seconds
        initial_discharge_kw: Initial V2G discharge power for stations 1-5 in kW
        attack_charge_kw: Charging power for stations 6-10 after attack in kW
        ramp_rate_kw_per_s: Maximum power change rate in kW/s
        jitter_window_s: Command distribution jitter window in seconds (0=synchronous)
        noise_std_kw: Measurement/power noise standard deviation in kW
        seed: Random number generator seed for reproducibility
    """
    T_max: int = 100
    dt: int = 1
    base_load_kw: float = 500.0
    n_stations: int = 10
    attack_time_s: int = 60
    initial_discharge_kw: float = -10.0
    attack_charge_kw: float = 20.0
    ramp_rate_kw_per_s: float = 10.0
    jitter_window_s: int = 0
    noise_std_kw: float = 0.0
    seed: Optional[int] = 42

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.T_max <= 0:
            raise ValueError("T_max must be positive")
        if self.dt <= 0 or self.dt > self.T_max:
            raise ValueError("dt must be positive and <= T_max")
        if self.n_stations <= 0:
            raise ValueError("n_stations must be positive")
        if self.attack_time_s < 0 or self.attack_time_s >= self.T_max:
            raise ValueError("attack_time_s must be within [0, T_max)")
        if self.ramp_rate_kw_per_s < 0:
            raise ValueError("ramp_rate_kw_per_s must be non-negative")
        if self.jitter_window_s < 0:
            raise ValueError("jitter_window_s must be non-negative")
        if self.noise_std_kw < 0:
            raise ValueError("noise_std_kw must be non-negative")

    def save(self, filepath: Path) -> None:
        """Save configuration to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        logging.info(f"Configuration saved to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> 'SimConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        config = cls(**data)
        logging.info(f"Configuration loaded from {filepath}")
        return config


# =========================
# Station Model
# =========================

@dataclass
class Station:
    """
    Charging station model with power ramping dynamics.
    
    Attributes:
        station_id: Unique station identifier
        power_kw: Current power output/input in kW (negative=discharge, positive=charge)
        target_power_kw: Target power setpoint in kW
        ramp_rate_kw_per_s: Maximum power change rate in kW/s
        history_kw: Time-series history of power values
    """
    station_id: int
    power_kw: float = 0.0
    target_power_kw: float = 0.0
    ramp_rate_kw_per_s: float = 10.0
    history_kw: List[float] = field(default_factory=list)

    def step(self, dt: float, noise_std_kw: float = 0.0, 
             rng: Optional[np.random.Generator] = None) -> None:
        """
        Execute one simulation time step with ramp-rate limiting.
        
        Args:
            dt: Time step size in seconds
            noise_std_kw: Standard deviation of Gaussian noise to add
            rng: Random number generator instance
        """
        # Apply ramp-rate limited power change
        delta = self.target_power_kw - self.power_kw
        max_step = self.ramp_rate_kw_per_s * dt
        
        if delta > 0:
            delta = min(delta, max_step)
        else:
            delta = max(delta, -max_step)
        
        self.power_kw += delta

        # Add measurement noise if specified
        if noise_std_kw > 0 and rng is not None:
            self.power_kw += rng.normal(0.0, noise_std_kw)

        self.history_kw.append(self.power_kw)

    def get_statistics(self) -> Dict[str, float]:
        """Calculate statistical metrics for station power history."""
        history = np.array(self.history_kw)
        return {
            'mean_kw': float(np.mean(history)),
            'std_kw': float(np.std(history)),
            'min_kw': float(np.min(history)),
            'max_kw': float(np.max(history)),
            'final_kw': float(history[-1]) if len(history) > 0 else 0.0
        }


# =========================
# OCPP Event System
# =========================

@dataclass
class OcppEvent:
    """
    OCPP protocol command event.
    
    Attributes:
        time_s: Event trigger time in seconds
        station_ids: List of target station IDs
        command: OCPP command type
        target_power_kw: Target power after command execution
    """
    time_s: int
    station_ids: List[int]
    command: OCPPCommand
    target_power_kw: float

    def __str__(self) -> str:
        """String representation for logging."""
        return (f"[t={self.time_s:04d}s] {self.command.value} -> "
                f"stations {self.station_ids} target={self.target_power_kw:.1f} kW")


# =========================
# Simulation Engine
# =========================

class V2GBotnetSim:
    """
    Main simulation engine for V2G botnet attack scenarios.
    
    This class orchestrates the entire simulation including:
    - Station power dynamics
    - OCPP event scheduling and execution
    - Grid load calculations
    - Data collection and analysis
    """

    def __init__(self, config: SimConfig, output_dir: Optional[Path] = None):
        """
        Initialize simulation engine.
        
        Args:
            config: Simulation configuration object
            output_dir: Directory for output files (default: current directory)
        """
        config.validate()
        self.cfg = config
        self.output_dir = output_dir or Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Time array
        self.times = np.arange(0, self.cfg.T_max + self.cfg.dt, self.cfg.dt)
        
        # Random number generator
        self.rng = (np.random.default_rng(self.cfg.seed) 
                    if self.cfg.seed is not None 
                    else np.random.default_rng())
        
        # Initialize stations
        self.stations = [
            Station(
                station_id=i+1,
                power_kw=0.0,
                target_power_kw=0.0,
                ramp_rate_kw_per_s=self.cfg.ramp_rate_kw_per_s
            ) for i in range(self.cfg.n_stations)
        ]
        
        # Event system
        self.events: List[OcppEvent] = []
        
        # Time-series data
        self.net_ev_power_kw: List[float] = []
        self.total_grid_load_kw: List[float] = []
        
        logging.info("Simulation engine initialized")
        logging.info(f"Configuration: {self.cfg.n_stations} stations, "
                    f"T_max={self.cfg.T_max}s, attack at t={self.cfg.attack_time_s}s")

    def init_conditions(self) -> None:
        """
        Set initial conditions for all stations.
        
        Stations 1-5: V2G discharge mode
        Stations 6-10: Idle mode
        """
        for i in range(self.cfg.n_stations):
            if 0 <= i <= 4:  # Stations 1-5
                self.stations[i].power_kw = self.cfg.initial_discharge_kw
                self.stations[i].target_power_kw = self.cfg.initial_discharge_kw
            else:  # Stations 6-10
                self.stations[i].power_kw = 0.0
                self.stations[i].target_power_kw = 0.0
        
        logging.info("Initial conditions set: Stations 1-5 discharging, 6-10 idle")

    def schedule_attack(self) -> None:
        """
        Schedule botnet attack events with optional command jitter.
        
        Creates two types of events:
        1. RemoteStopTransaction for stations 1-5 (stop discharge)
        2. RemoteStartTransaction for stations 6-10 (start charging)
        """
        # Schedule stop commands for stations 1-5
        stop_offsets = self._jitter_offsets(5, self.cfg.jitter_window_s)
        for idx, sid in enumerate(range(1, 6)):
            t_event = self.cfg.attack_time_s + stop_offsets[idx]
            self.events.append(
                OcppEvent(
                    time_s=t_event,
                    station_ids=[sid],
                    command=OCPPCommand.REMOTE_STOP,
                    target_power_kw=0.0
                )
            )
        
        # Schedule start commands for stations 6-10
        start_offsets = self._jitter_offsets(5, self.cfg.jitter_window_s)
        for idx, sid in enumerate(range(6, 11)):
            t_event = self.cfg.attack_time_s + start_offsets[idx]
            self.events.append(
                OcppEvent(
                    time_s=t_event,
                    station_ids=[sid],
                    command=OCPPCommand.REMOTE_START,
                    target_power_kw=self.cfg.attack_charge_kw
                )
            )
        
        logging.info(f"Attack scheduled: {len(self.events)} OCPP events created")

    def _jitter_offsets(self, n: int, window_s: int) -> List[int]:
        """
        Generate random time offsets for command distribution.
        
        Args:
            n: Number of offsets to generate
            window_s: Jitter window size in seconds
            
        Returns:
            List of time offsets in seconds
        """
        if window_s <= 0:
            return [0] * n
        return list(self.rng.integers(low=0, high=window_s + 1, size=n))

    def apply_events(self, t: int) -> None:
        """
        Apply scheduled events at current time step.
        
        Args:
            t: Current simulation time in seconds
        """
        for event in [e for e in self.events if e.time_s == t]:
            for sid in event.station_ids:
                st = self.stations[sid - 1]
                st.target_power_kw = event.target_power_kw
            logging.info(str(event))

    def step(self, t: int) -> None:
        """
        Execute one simulation time step.
        
        Args:
            t: Current simulation time in seconds
        """
        # Apply scheduled events
        self.apply_events(t)
        
        # Update all stations
        for st in self.stations:
            st.step(self.cfg.dt, noise_std_kw=self.cfg.noise_std_kw, rng=self.rng)
        
        # Calculate aggregate metrics
        net_ev = sum(st.power_kw for st in self.stations)
        total_load = self.cfg.base_load_kw + net_ev
        
        self.net_ev_power_kw.append(net_ev)
        self.total_grid_load_kw.append(total_load)

    def run(self) -> None:
        """Execute complete simulation run."""
        logging.info("=" * 60)
        logging.info("Starting simulation run")
        logging.info("=" * 60)
        
        self.init_conditions()
        self.schedule_attack()
        
        for t in self.times:
            self.step(int(t))
        
        logging.info("Simulation completed successfully")

    # =========================
    # Analysis & Metrics
    # =========================

    def calculate_metrics(self) -> Dict[str, float]:
        """
        Calculate key performance metrics from simulation results.
        
        Returns:
            Dictionary of metric names and values
        """
        baseline_load = self.cfg.base_load_kw + (5 * self.cfg.initial_discharge_kw)
        post_attack_load = self.cfg.base_load_kw + (5 * self.cfg.attack_charge_kw)
        
        # Find actual peak load
        total_load_array = np.array(self.total_grid_load_kw)
        peak_load = float(np.max(total_load_array))
        peak_time = int(np.argmax(total_load_array))
        
        # Calculate load swing
        load_swing = post_attack_load - baseline_load
        
        return {
            'baseline_load_kw': baseline_load,
            'expected_post_attack_load_kw': post_attack_load,
            'peak_load_kw': peak_load,
            'peak_time_s': peak_time,
            'load_swing_kw': load_swing,
            'swing_percentage': (load_swing / baseline_load) * 100,
        }

    def generate_report(self) -> str:
        """
        Generate comprehensive text report of simulation results.
        
        Returns:
            Formatted report string
        """
        metrics = self.calculate_metrics()
        
        report = []
        report.append("=" * 70)
        report.append("V2G BOTNET ATTACK SIMULATION REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        report.append("CONFIGURATION")
        report.append("-" * 70)
        report.append(f"  Simulation duration:        {self.cfg.T_max} seconds")
        report.append(f"  Time step:                  {self.cfg.dt} seconds")
        report.append(f"  Number of stations:         {self.cfg.n_stations}")
        report.append(f"  Attack time:                {self.cfg.attack_time_s} seconds")
        report.append(f"  Base grid load:             {self.cfg.base_load_kw:.1f} kW")
        report.append(f"  Initial discharge power:    {self.cfg.initial_discharge_kw:.1f} kW")
        report.append(f"  Attack charge power:        {self.cfg.attack_charge_kw:.1f} kW")
        report.append(f"  Ramp rate:                  {self.cfg.ramp_rate_kw_per_s:.1f} kW/s")
        report.append(f"  Command jitter window:      {self.cfg.jitter_window_s} seconds")
        report.append(f"  Noise std deviation:        {self.cfg.noise_std_kw:.1f} kW")
        report.append("")
        
        report.append("ATTACK IMPACT METRICS")
        report.append("-" * 70)
        report.append(f"  Baseline load (pre-attack): {metrics['baseline_load_kw']:>10.1f} kW")
        report.append(f"  Expected post-attack load:  {metrics['expected_post_attack_load_kw']:>10.1f} kW")
        report.append(f"  Peak load observed:         {metrics['peak_load_kw']:>10.1f} kW")
        report.append(f"  Peak time:                  {metrics['peak_time_s']:>10d} seconds")
        report.append(f"  Load swing:                 {metrics['load_swing_kw']:>10.1f} kW")
        report.append(f"  Swing percentage:           {metrics['swing_percentage']:>10.1f} %")
        report.append("")
        
        report.append("STATION STATISTICS")
        report.append("-" * 70)
        report.append(f"{'ID':<6} {'Mean (kW)':<12} {'Std (kW)':<12} {'Min (kW)':<12} "
                     f"{'Max (kW)':<12} {'Final (kW)':<12}")
        report.append("-" * 70)
        
        for st in self.stations:
            stats = st.get_statistics()
            report.append(
                f"{st.station_id:<6} "
                f"{stats['mean_kw']:<12.2f} "
                f"{stats['std_kw']:<12.2f} "
                f"{stats['min_kw']:<12.2f} "
                f"{stats['max_kw']:<12.2f} "
                f"{stats['final_kw']:<12.2f}"
            )
        
        report.append("=" * 70)
        
        return "\n".join(report)

    # =========================
    # Visualization
    # =========================

    def plot_total_load(self, save_path: Optional[Path] = None) -> None:
        """
        Plot total grid load over time.
        
        Args:
            save_path: Output file path (default: output_dir/v2g_attack_load.png)
        """
        if save_path is None:
            save_path = self.output_dir / "v2g_attack_load.png"
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.times, self.total_grid_load_kw, 
                color="tab:orange", linewidth=2, label="Total Grid Load")
        plt.axvline(self.cfg.attack_time_s, color="r", linestyle="--", 
                   linewidth=1.5, label=f"Attack Time (t={self.cfg.attack_time_s}s)")
        
        # Add baseline and post-attack reference lines
        metrics = self.calculate_metrics()
        plt.axhline(metrics['baseline_load_kw'], color='g', linestyle=':', 
                   alpha=0.7, label=f"Baseline ({metrics['baseline_load_kw']:.0f} kW)")
        plt.axhline(metrics['expected_post_attack_load_kw'], color='b', 
                   linestyle=':', alpha=0.7, 
                   label=f"Post-Attack ({metrics['expected_post_attack_load_kw']:.0f} kW)")
        
        plt.xlabel("Time (seconds)", fontsize=11)
        plt.ylabel("Grid Load (kW)", fontsize=11)
        plt.title("Grid Load Evolution During V2G Botnet Attack", fontsize=13, fontweight='bold')
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.legend(loc="best", framealpha=0.9)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Total load plot saved to {save_path}")

    def plot_station_powers(self, save_path: Optional[Path] = None) -> None:
        """
        Plot individual station power profiles.
        
        Args:
            save_path: Output file path (default: output_dir/v2g_attack_station_powers.png)
        """
        if save_path is None:
            save_path = self.output_dir / "v2g_attack_station_powers.png"
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot stations 1-5 (discharge group)
        for st in self.stations[:5]:
            ax1.plot(self.times, st.history_kw, linewidth=1.5, 
                    label=f"Station {st.station_id}")
        ax1.axvline(self.cfg.attack_time_s, color="r", linestyle="--", 
                   linewidth=1.5, label="Attack Time")
        ax1.axhline(0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
        ax1.set_xlabel("Time (seconds)", fontsize=10)
        ax1.set_ylabel("Power (kW)", fontsize=10)
        ax1.set_title("Stations 1-5: V2G Discharge Group (Attack Target: Stop)", 
                     fontsize=11, fontweight='bold')
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.legend(ncol=3, fontsize=9, framealpha=0.9)
        
        # Plot stations 6-10 (charge group)
        for st in self.stations[5:]:
            ax2.plot(self.times, st.history_kw, linewidth=1.5, 
                    label=f"Station {st.station_id}")
        ax2.axvline(self.cfg.attack_time_s, color="r", linestyle="--", 
                   linewidth=1.5, label="Attack Time")
        ax2.axhline(0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
        ax2.set_xlabel("Time (seconds)", fontsize=10)
        ax2.set_ylabel("Power (kW)", fontsize=10)
        ax2.set_title("Stations 6-10: Idle Group (Attack Target: Start Charging)", 
                     fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.legend(ncol=3, fontsize=9, framealpha=0.9)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Station power plots saved to {save_path}")

    def plot_ev_contribution(self, save_path: Optional[Path] = None) -> None:
        """
        Plot EV contribution to grid load separately.
        
        Args:
            save_path: Output file path (default: output_dir/v2g_attack_ev_contribution.png)
        """
        if save_path is None:
            save_path = self.output_dir / "v2g_attack_ev_contribution.png"
        
        plt.figure(figsize=(10, 6))
        plt.plot(self.times, self.net_ev_power_kw, 
                color="tab:blue", linewidth=2, label="Net EV Power")
        plt.axvline(self.cfg.attack_time_s, color="r", linestyle="--", 
                   linewidth=1.5, label=f"Attack Time (t={self.cfg.attack_time_s}s)")
        plt.axhline(0, color='k', linestyle='-', linewidth=0.8, alpha=0.5)
        
        plt.xlabel("Time (seconds)", fontsize=11)
        plt.ylabel("EV Power (kW)", fontsize=11)
        plt.title("Net EV Contribution to Grid Load", fontsize=13, fontweight='bold')
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.legend(loc="best", framealpha=0.9)
        
        # Add annotation for discharge/charge regions
        plt.text(self.cfg.attack_time_s / 2, min(self.net_ev_power_kw) * 0.8, 
                'V2G Discharge\n(Grid Support)', 
                ha='center', va='top', fontsize=10, 
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))
        plt.text(self.cfg.attack_time_s + (self.cfg.T_max - self.cfg.attack_time_s) / 2, 
                max(self.net_ev_power_kw) * 0.8, 
                'Charging Mode\n(Grid Load)', 
                ha='center', va='bottom', fontsize=10, 
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logging.info(f"EV contribution plot saved to {save_path}")

    # =========================
    # Output Management
    # =========================

    def save_results(self) -> None:
        """Save all simulation results, plots, and reports."""
        # Save configuration
        self.cfg.save(self.output_dir / "simulation_config.json")
        
        # Save time-series data
        data = {
            'time_s': self.times.tolist(),
            'total_grid_load_kw': self.total_grid_load_kw,
            'net_ev_power_kw': self.net_ev_power_kw,
            'stations': {
                st.station_id: st.history_kw for st in self.stations
            }
        }
        with open(self.output_dir / "simulation_data.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Time-series data saved to {self.output_dir / 'simulation_data.json'}")
        
        # Generate and save report
        report = self.generate_report()
        report_path = self.output_dir / "simulation_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logging.info(f"Report saved to {report_path}")
        print("\n" + report)
        
        # Generate plots
        self.plot_total_load()
        self.plot_station_powers()
        self.plot_ev_contribution()
        
        logging.info("All results saved successfully")


# =========================
# Command Line Interface
# =========================

def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging system.
    
    Args:
        verbose: Enable debug-level logging if True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="V2G Botnet Attack Simulation Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--config', type=Path, default=None,
        help='Path to configuration JSON file'
    )
    parser.add_argument(
        '--output-dir', type=Path, default=Path('simulation_output'),
        help='Output directory for results'
    )
    parser.add_argument(
        '--T-max', type=int, default=100,
        help='Total simulation duration (seconds)'
    )
    parser.add_argument(
        '--n-stations', type=int, default=10,
        help='Number of charging stations'
    )
    parser.add_argument(
        '--attack-time', type=int, default=60,
        help='Attack trigger time (seconds)'
    )
    parser.add_argument(
        '--jitter-window', type=int, default=0,
        help='Command jitter window (seconds, 0=synchronous)'
    )
    parser.add_argument(
        '--noise-std', type=float, default=0.0,
        help='Power measurement noise std deviation (kW)'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed for reproducibility (None for random)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


# =========================
# Main Entry Point
# =========================

def main():
    """Main execution function."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    try:
        # Load or create configuration
        if args.config:
            config = SimConfig.load(args.config)
        else:
            config = SimConfig(
                T_max=args.T_max,
                dt=1,
                base_load_kw=500.0,
                n_stations=args.n_stations,
                attack_time_s=args.attack_time,
                initial_discharge_kw=-10.0,
                attack_charge_kw=20.0,
                ramp_rate_kw_per_s=10.0,
                jitter_window_s=args.jitter_window,
                noise_std_kw=args.noise_std,
                seed=args.seed
            )
        
        # Create and run simulation
        sim = V2GBotnetSim(config, output_dir=args.output_dir)
        sim.run()
        sim.save_results()
        
        logging.info("=" * 60)
        logging.info("Simulation completed successfully!")
        logging.info(f"Results available in: {args.output_dir.absolute()}")
        logging.info("=" * 60)
        
    except Exception as e:
        logging.error(f"Simulation failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
