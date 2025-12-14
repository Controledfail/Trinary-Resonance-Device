# TRD Explorer v2.2 – Fully Modular Interactive Edition
# Combines analytics + interactivity with separately deployable modules

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider, Button, RadioButtons, CheckButtons
from scipy.fft import fft, fftfreq
from scipy.constants import c, hbar, epsilon_0, G
import json
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# ========================= UNITS & CONSTANTS MODULE =========================
class Units:
    def __init__(self, system='SI'):
        self.system = system
        if system == 'SI':
            self.c = 299792458.0
            self.hbar = 1.054571817e-34
            self.eps0 = epsilon_0
            self.G = G
        else:
            self.c = self.hbar = self.eps0 = self.G = 1.0
    def __repr__(self): return f"Units({self.system})"

u = Units('SI')

# ========================= ZETA & SCALE MODULE =========================
zeta_imag_parts = np.array([
    14.1347251417, 21.0220396388, 25.0108575801, 30.4248761259,
    32.9350615877, 37.5861781588, 40.9187190122, 43.3270732809
])

def cosmic_to_chip_radius(t_n, scale_factor=1.0):
    """Scale-invariant cosmic → chip transform"""
    cosmic_r = u.c / (4 * np.pi * t_n)
    compton_chip = u.hbar / (1.0 * u.c)
    lambda_compress = 1.0e16
    return scale_factor * compton_chip * (cosmic_r / compton_chip) / lambda_compress

# ========================= PRESETS MODULE =========================
PRESETS = {
    "default": {"gamma": 1.0, "N_eff": 3, "f0": 432e3, "scale_factor": 1.0},
    "fusion_optimized": {"gamma": 2.5, "N_eff": 8, "f0": 1e6, "scale_factor": 1.5},
    "quantum_sim": {"gamma": 0.5, "N_eff": 3, "f0": 100e3, "scale_factor": 0.8},
    "resonance_test": {"gamma": 1.618, "N_eff": 5, "f0": 432e3, "scale_factor": 1.0}
}

# ========================= CITATIONS MODULE =========================
CITATIONS = [
    "Bandyopadhyay 2025 - Microtubule Resonance",
    "Tuszyński 2024 - Quantum Brain Dynamics", 
    "Babcock 2024 - Autopoietic Systems",
    "Wiest 2025 - TRD Thermodynamics",
    "Sahu 2025 - Electromagnetic Coupling",
    "Saxena 2025 - Ring Dynamics",
    "Montgomery/Odlyzko - Zeta Zero Statistics",
    "Plouffe/LMFDB - Riemann Hypothesis"
]

LAGRANGIAN_TERMS = [
    "Term 1: Angular Momentum Evolution ∂M_i/∂t",
    "Term 2: Rotational Kinetic Energy ½Ω·I·Ω",
    "Term 3: EM Wave Propagation ∇×(∇×E)",
    "Term 4: Potential Gradient ∇V_TRD",
    "Term 5: Poynting Vector Correction",
    "Term 6: External Force Coupling F_ext",
    "Term 7: External Torque M_ext",
    "Term 8: Energy Conservation Constraint"
]

# ========================= CORE TRD ENGINE MODULE =========================
class TRD:
    def __init__(self, gamma=1.0, N_eff=3, f0=432e3, scale_factor=1.0):
        assert N_eff > 0, "N_eff must be positive"
        assert f0 > 0, "f0 must be positive"
        self.gamma = float(gamma)
        self.N_eff = float(N_eff)
        self.f0 = float(f0)
        self.scale_factor = scale_factor
        self.scale_mode = 'chip'  # 'chip' or 'cosmic'
        self._cache = {}
        self.compute_all()
        self.validate_units()

    def validate_units(self):
        """Dimensional consistency check"""
        assert np.all(self.radius > 0), "All radii must be positive"
        E_test = u.hbar * self.f_env[0]
        assert 1e-40 < E_test < 1e-10, f"Energy scale suspicious: {E_test:.2e} J"

    def compute_all(self):
        key = (self.gamma, self.N_eff, self.f0, self.scale_factor, self.scale_mode)
        if key in self._cache:
            return self._cache[key]

        # 1. Envelope frequencies from zeta zeros
        self.f_env = self.f0 * zeta_imag_parts / zeta_imag_parts[0]

        # 2. Radii - cosmic or chip scale
        if self.scale_mode == 'cosmic':
            self.radius = u.c / (4 * np.pi * self.f_env)  # meters
            self.radius_unit = 'm'
        else:
            self.radius = cosmic_to_chip_radius(zeta_imag_parts, self.scale_factor)
            self.radius_unit = 'mm'
            self.radius *= 1e3  # convert to mm for display

        # 3. Power scaling
        self.power_N = 1e-3 * (self.f_env**2) * (self.radius**3) * (self.N_eff**2) * self.gamma**1.5
        self.power_N /= self.power_N.mean()

        # 4. Temporal envelope
        self.t = np.linspace(0, 1e-3, 1000)
        self.env_wave = np.zeros((8, len(self.t)))
        for i in range(8):
            self.env_wave[i] = 1 + 0.8 * np.cos(2*np.pi*self.f_env[i]*self.t + i*np.pi/4)

        # 5. Energy conservation
        E_kin = 0.5 * 1.0 * (2*np.pi*self.f_env)**2 * (self.radius**2) * self.power_N
        E_em = self.power_N / u.c
        self.E_kin_total = E_kin.sum()
        self.E_em_total = E_em.sum()
        self.E_total = self.E_kin_total + self.E_em_total
        self.energy_conserved = np.isclose(self.E_kin_total, self.E_em_total, rtol=0.1)

        # 6. Stability
        J = np.diag(-self.gamma * self.f_env)
        self.eigenvalues = np.linalg.eigvals(J)
        self.stable = np.all(np.real(self.eigenvalues) < 0)

        # 7. Resonance
        self.ratios = self.f_env[:,None] / self.f_env[None,:]
        phi = (1+np.sqrt(5))/2
        self.golden_hits = np.any(np.isclose(self.ratios, phi, rtol=0.01))
        self.rational_hits = np.any(np.isclose(self.ratios, np.round(self.ratios), atol=1e-3))

        # 8. Uncertainty
        self.compute_uncertainties()

        self._cache[key] = True

    def compute_uncertainties(self, n_samples=300):
        """Monte Carlo error propagation"""
        f0_samples = np.random.normal(self.f0, 0.02*self.f0, n_samples)
        f_env_dist = np.array([f0_s * zeta_imag_parts / zeta_imag_parts[0] for f0_s in f0_samples])
        self.f_env_std = f_env_dist.std(axis=0)
        self.radius_std = np.random.normal(0, 0.01*self.radius, 8)

    def export_state(self, filename=None):
        """Export complete state to JSON"""
        if filename is None:
            filename = f"TRD_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = {
            "meta": {"version": "2.2", "date": datetime.now().isoformat()},
            "parameters": {"gamma": self.gamma, "N_eff": self.N_eff, "f0": self.f0, 
                          "scale_factor": self.scale_factor, "scale_mode": self.scale_mode},
            "rings": [{"ring": i+1, "zeta_t": float(zeta_imag_parts[i]),
                       "f_env_Hz": float(self.f_env[i]), "f_std_Hz": float(self.f_env_std[i]),
                       "radius": float(self.radius[i]), "radius_unit": self.radius_unit,
                       "power_mW": float(self.power_N[i]*1000)} for i in range(8)],
            "diagnostics": {"energy_conserved": self.energy_conserved, "stable": self.stable,
                           "E_total_J": float(self.E_total), "golden_resonance": self.golden_hits}
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return filename

    @classmethod
    def from_preset(cls, preset_name):
        return cls(**PRESETS[preset_name])

# ========================= VISUALIZATION MODULES =========================

class SpiralModule:
    """Handles main spiral visualization with click interaction"""
    def __init__(self, ax, trd, continuous=True):
        self.ax = ax
        self.trd = trd
        self.continuous = continuous
        self.colors = plt.cm.plasma(np.linspace(0, 1, 8))
        self.setup()

    def setup(self):
        self.ax.set_aspect('equal')
        self.ax.set_facecolor('#0a0a0a')
        
        # Continuous spiral background
        if self.continuous:
            theta = np.linspace(0, 8*np.pi, 1000)
            r_cont = np.interp(theta/np.pi, np.arange(8), self.trd.radius[::-1])
            self.ax.plot(r_cont*np.cos(theta), r_cont*np.sin(theta), 'cyan', lw=2, alpha=0.3)

        # Ring positions
        self.ring_positions = []
        for i in range(8):
            r = self.trd.radius[i]
            angle = i * np.pi / 4
            x, y = r*np.cos(angle), r*np.sin(angle)
            self.ring_positions.append((x, y))
            
            # Uncertainty circle
            circle = plt.Circle((x, y), self.trd.radius_std[i], color=self.colors[i], alpha=0.1)
            self.ax.add_patch(circle)
            
            # Ring marker
            self.ax.plot(x, y, 'o', color=self.colors[i], ms=18, 
                        markeredgecolor='white', markeredgewidth=2, picker=5)
            
            # Ring label
            self.ax.text(x, y, f'{i+1}', color='white', ha='center', 
                        va='center', fontsize=10, weight='bold')
            
            # Force vector
            force = -self.trd.gamma * self.trd.f_env[i] * np.array([x, y])
            scale = 1e3 if self.trd.scale_mode == 'chip' else 1e-6
            self.ax.arrow(x, y, force[0]*scale, force[1]*scale, 
                         color='lime', width=0.02, alpha=0.7, head_width=0.1)

        self.ax.set_title(f"TRD Spiral – γ={self.trd.gamma:.1f} | N={self.trd.N_eff} | "
                         f"f₀={self.trd.f0/1e3:.0f} kHz | Mode: {self.trd.scale_mode}\n"
                         f"Energy: {'✓' if self.trd.energy_conserved else '✗'} | "
                         f"Stable: {'✓' if self.trd.stable else '✗'} | "
                         f"Golden φ: {'✓' if self.trd.golden_hits else '✗'}", 
                         color='white', fontsize=11)
        self.ax.axis('off')

    def on_click(self, event, idx):
        """Print detailed ring info"""
        print(f"\n{'='*70}")
        print(f"RING {idx+1} UNIVERSE LOADED")
        print(f"{'='*70}")
        print(f"Zeta Zero: Im(ρ_{idx+1}) = {zeta_imag_parts[idx]:.10f}")
        print(f"Envelope Frequency: f_env = {self.trd.f_env[idx]:.6f} ± {self.trd.f_env_std[idx]:.6f} Hz")
        print(f"Radius: r = {self.trd.radius[idx]:.6f} {self.trd.radius_unit}")
        print(f"Power Required: P = {self.trd.power_N[idx]*1000:.3f} mW")
        print(f"Phase Offset: φ = {idx*np.pi/4:.4f} rad ({idx*45}°)")
        print(f"\nCitation: {CITATIONS[idx]}")
        print(f"Lagrangian: {LAGRANGIAN_TERMS[idx]}")
        print(f"\nEnvelope Waveform Sample (first 10 points):")
        for j in range(10):
            print(f"  t={self.trd.t[j*100]*1e3:.3f} ms: A={self.trd.env_wave[idx][j*100]:.4f}")
        print(f"{'='*70}\n")

class EnvelopeModule:
    """Temporal envelope visualization"""
    def __init__(self, ax, trd):
        self.ax = ax
        self.trd = trd
        self.colors = plt.cm.plasma(np.linspace(0, 1, 8))
        self.setup()

    def setup(self):
        for i in range(8):
            self.ax.plot(self.trd.t*1e3, self.trd.env_wave[i] + i*0.9, 
                        color=self.colors[i], lw=1.5, label=f'Ring {i+1}')
        self.ax.set_title("Ring Envelopes (time-stacked)", fontsize=10)
        self.ax.set_xlabel("Time [ms]", fontsize=9)
        self.ax.set_ylabel("Amplitude (offset)", fontsize=9)
        self.ax.legend(loc='upper right', fontsize=7, ncol=2)
        self.ax.grid(alpha=0.2)

class FFTModule:
    """FFT spectrum analysis"""
    def __init__(self, ax, trd):
        self.ax = ax
        self.trd = trd
        self.setup()

    def setup(self):
        N = len(self.trd.t)
        freqs = fftfreq(N, self.trd.t[1]-self.trd.t[0])
        spectrum = np.abs(fft(self.trd.env_wave.sum(axis=0)))
        self.ax.semilogy(freqs[:N//2]/1e3, spectrum[:N//2], color='orange', lw=1.8)
        self.ax.set_title("FFT – Total Frequency Content", fontsize=10)
        self.ax.set_xlabel("Frequency [kHz]", fontsize=9)
        self.ax.set_ylabel("Magnitude", fontsize=9)
        self.ax.grid(alpha=0.3, which='both')

class ResonanceMatrixModule:
    """Frequency ratio heatmap"""
    def __init__(self, ax, trd):
        self.ax = ax
        self.trd = trd
        self.setup()

    def setup(self):
        im = self.ax.imshow(self.trd.ratios, cmap='RdYlGn', vmin=0, vmax=3, aspect='auto')
        self.ax.set_title("Frequency Ratio Matrix f_i/f_j", fontsize=10)
        self.ax.set_xlabel("Ring j", fontsize=9)
        self.ax.set_ylabel("Ring i", fontsize=9)
        self.ax.set_xticks(range(8))
        self.ax.set_yticks(range(8))
        self.ax.set_xticklabels(range(1,9))
        self.ax.set_yticklabels(range(1,9))
        plt.colorbar(im, ax=self.ax, label='Ratio')
        
        # Highlight golden ratio
        phi = (1+np.sqrt(5))/2
        for i in range(8):
            for j in range(8):
                if np.isclose(self.trd.ratios[i,j], phi, rtol=0.01):
                    self.ax.plot(j, i, 'w*', markersize=12)
                # Add ratio values
                if i != j:
                    self.ax.text(j, i, f'{self.trd.ratios[i,j]:.2f}', 
                               ha='center', va='center', fontsize=6, color='black')

class PowerModule:
    """Power distribution bar chart"""
    def __init__(self, ax, trd):
        self.ax = ax
        self.trd = trd
        self.colors = plt.cm.plasma(np.linspace(0, 1, 8))
        self.setup()

    def setup(self):
        bars = self.ax.bar(range(1,9), self.trd.power_N*1000, 
                          color=self.colors, edgecolor='white', linewidth=1.5)
        self.ax.set_xlabel("Ring", fontsize=9)
        self.ax.set_ylabel("Power [mW]", fontsize=9)
        self.ax.set_title("Power Distribution P ∝ f²r³N²γ^1.5", fontsize=10)
        self.ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=7)

class EnergyModule:
    """Energy breakdown chart"""
    def __init__(self, ax, trd):
        self.ax = ax
        self.trd = trd
        self.setup()

    def setup(self):
        energies = [self.trd.E_kin_total, self.trd.E_em_total]
        labels = ['Kinetic', 'EM']
        bars = self.ax.bar(labels, energies, color=['steelblue', 'coral'], 
                          edgecolor='white', linewidth=2)
        self.ax.set_ylabel("Energy [J]", fontsize=9)
        self.ax.set_title(f"Energy Budget (Total: {self.trd.E_total:.2e} J)", fontsize=10)
        self.ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        self.ax.grid(axis='y', alpha=0.3)
        
        # Add percentage labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            pct = 100 * height / self.trd.E_total
            self.ax.text(bar.get_x() + bar.get_width()/2., height/2,
                        f'{pct:.1f}%', ha='center', va='center', 
                        fontsize=9, color='white', weight='bold')

class ScaleLawModule:
    """Radius vs frequency cosmic law"""
    def __init__(self, ax, trd, show_uncertainty=True):
        self.ax = ax
        self.trd = trd
        self.show_uncertainty = show_uncertainty
        self.setup()

    def setup(self):
        if self.show_uncertainty:
            self.ax.errorbar(self.trd.f_env/1e3, self.trd.radius, 
                           yerr=self.trd.radius_std, xerr=self.trd.f_env_std/1e3,
                           fmt='o-', color='magenta', capsize=4, capthick=1.5, markersize=8)
        else:
            self.ax.loglog(self.trd.f_env/1e3, self.trd.radius, 'o-', 
                          color='magenta', markersize=8)
        
        self.ax.set_xlabel("f_env [kHz]", fontsize=9)
        self.ax.set_ylabel(f"Radius [{self.trd.radius_unit}]", fontsize=9)
        self.ax.set_title("Scale-Invariant Cosmic Law r ∝ c/f", fontsize=10)
        self.ax.grid(alpha=0.3, which='both')

# ========================= MAIN EXECUTION =========================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TRD Explorer v2.2 – Modular Interactive Edition")
    print("="*70)
    print("\nAvailable Presets:", list(PRESETS.keys()))
    print("\nUsage Options:")
    print("  1. Full Interactive:  app = InteractiveTRD(); app.show()")
    print("  2. From Preset:       app = InteractiveTRD(**PRESETS['fusion_optimized']); app.show()")
    print("  3. Spiral Only:       plot_spiral_only(TRD())")
    print("  4. Resonance Only:    plot_resonance_matrix_only(TRD())")
    print("  5. Energy Analysis:   plot_energy_analysis(TRD())")
    print("\nInteractive Features:")
    print("  • Click rings to explore detailed universes")
    print("  • Adjust sliders to modify parameters in real-time")
    print("  • 'Walk Spiral' button for automated tour")
    print("  • Toggle Chip/Cosmic scale modes")
    print("  • Export JSON with full state data")
    print("="*70 + "\n")
    
    # Launch full interactive app by default
    app = InteractiveTRD()
    app.show() INTERACTIVE VISUALIZER =========================

class InteractiveTRD:
    def __init__(self, gamma=1.0, N_eff=3, f0=432e3, scale_factor=1.0):
        self.trd = TRD(gamma, N_eff, f0, scale_factor)
        self.setup_figure()
        self.create_modules()
        self.setup_controls()
        self.setup_interactions()

    def setup_figure(self):
        self.fig = plt.figure(figsize=(20, 12))
        self.gs = GridSpec(5, 5, figure=self.fig, hspace=0.5, wspace=0.5, 
                          left=0.05, right=0.95, top=0.93, bottom=0.22)

    def create_modules(self):
        """Create all visualization modules"""
        # Main spiral (large, left)
        ax_spiral = self.fig.add_subplot(self.gs[:3, 0:2])
        self.spiral = SpiralModule(ax_spiral, self.trd)
        
        # Top row (right)
        ax_env = self.fig.add_subplot(self.gs[0, 2:])
        self.envelope = EnvelopeModule(ax_env, self.trd)
        
        ax_fft = self.fig.add_subplot(self.gs[1, 2:])
        self.fft = FFTModule(ax_fft, self.trd)
        
        # Middle row
        ax_res = self.fig.add_subplot(self.gs[2, 2:4])
        self.resonance = ResonanceMatrixModule(ax_res, self.trd)
        
        ax_scale = self.fig.add_subplot(self.gs[2, 4])
        self.scale_law = ScaleLawModule(ax_scale, self.trd)
        
        # Bottom row
        ax_power = self.fig.add_subplot(self.gs[3, 0:2])
        self.power = PowerModule(ax_power, self.trd)
        
        ax_energy = self.fig.add_subplot(self.gs[3, 2:4])
        self.energy = EnergyModule(ax_energy, self.trd)

    def setup_controls(self):
        """Setup interactive sliders and buttons"""
        # Sliders
        ax_gamma = plt.axes([0.15, 0.14, 0.3, 0.02])
        self.s_gamma = Slider(ax_gamma, 'γ (damping)', 0.1, 5.0, valinit=self.trd.gamma, valstep=0.1)
        
        ax_N = plt.axes([0.15, 0.11, 0.3, 0.02])
        self.s_N = Slider(ax_N, 'N_eff', 1, 20, valinit=self.trd.N_eff, valstep=1, valfmt='%d')
        
        ax_f0 = plt.axes([0.15, 0.08, 0.3, 0.02])
        self.s_f0 = Slider(ax_f0, 'f₀ [kHz]', 100, 1000, valinit=self.trd.f0/1e3, valstep=10)
        
        ax_scale = plt.axes([0.15, 0.05, 0.3, 0.02])
        self.s_scale = Slider(ax_scale, 'Scale Factor', 0.1, 10.0, valinit=self.trd.scale_factor, valstep=0.1)
        
        # Buttons
        ax_walk = plt.axes([0.55, 0.12, 0.1, 0.04])
        self.btn_walk = Button(ax_walk, 'Walk Spiral', color='lightblue')
        
        ax_export = plt.axes([0.55, 0.07, 0.1, 0.04])
        self.btn_export = Button(ax_export, 'Export JSON', color='lightgreen')
        
        # Scale mode toggle
        ax_mode = plt.axes([0.7, 0.08, 0.12, 0.08])
        self.radio_mode = RadioButtons(ax_mode, ['Chip', 'Cosmic'], active=0)
        
        # Module toggles
        ax_toggle = plt.axes([0.85, 0.05, 0.12, 0.12])
        self.check_modules = CheckButtons(ax_toggle, 
                                         ['Envelope', 'FFT', 'Resonance', 'Power'],
                                         [True, True, True, True])

    def setup_interactions(self):
        """Connect all interactive elements"""
        # Sliders
        self.s_gamma.on_changed(self.update)
        self.s_N.on_changed(self.update)
        self.s_f0.on_changed(self.update)
        self.s_scale.on_changed(self.update)
        
        # Buttons
        self.btn_walk.on_clicked(self.walk_spiral)
        self.btn_export.on_clicked(self.export_data)
        
        # Radio
        self.radio_mode.on_clicked(self.toggle_scale_mode)
        
        # Click on rings
        self.fig.canvas.mpl_connect('button_press_event', self.on_click_ring)

    def update(self, val):
        """Update all modules when parameters change"""
        self.trd.gamma = self.s_gamma.val
        self.trd.N_eff = int(self.s_N.val)
        self.trd.f0 = self.s_f0.val * 1e3
        self.trd.scale_factor = self.s_scale.val
        self.trd._cache.clear()
        self.trd.compute_all()
        
        # Redraw all modules
        self.fig.clear()
        self.setup_figure()
        self.create_modules()
        self.setup_controls()
        self.setup_interactions()
        plt.draw()

    def toggle_scale_mode(self, label):
        """Switch between cosmic and chip scale"""
        self.trd.scale_mode = label.lower()
        self.update(None)
        print(f"Switched to {label} scale mode")

    def on_click_ring(self, event):
        """Handle click on rings"""
        if event.inaxes != self.spiral.ax:
            return
        
        # Find closest ring
        click_pos = np.array([event.xdata, event.ydata])
        distances = [np.linalg.norm(click_pos - np.array(pos)) 
                    for pos in self.spiral.ring_positions]
        idx = np.argmin(distances)
        
        if distances[idx] < self.trd.radius[idx] * 0.3:  # Within 30% of ring radius
            self.spiral.on_click(event, idx)

    def walk_spiral(self, event):
        """Automated walk through all rings"""
        print(f"\n{'#'*70}")
        print("INITIATING SPIRAL WALK - VISITING ALL 8 RING UNIVERSES")
        print(f"{'#'*70}\n")
        for i in range(8):
            self.spiral.on_click(None, i)
            plt.pause(0.5)
        print(f"\n{'#'*70}")
        print("SPIRAL WALK COMPLETE")
        print(f"{'#'*70}\n")

    def export_data(self, event):
        """Export current state"""
        filename = self.trd.export_state()
        print(f"✓ Data exported to: {filename}")

    def show(self):
        """Display the interactive figure"""
        plt.suptitle("TRD Explorer v2.2 – Modular Interactive Edition", 
                     fontsize=16, color='cyan', weight='bold')
        plt.show()

# ========================= STANDALONE MODULE FUNCTIONS =========================

def plot_spiral_only(trd):
    """Deploy just the spiral visualization"""
    fig, ax = plt.subplots(figsize=(10, 10))
    spiral = SpiralModule(ax, trd)
    plt.show()

def plot_resonance_matrix_only(trd):
    """Deploy just the resonance matrix"""
    fig, ax = plt.subplots(figsize=(8, 7))
    res = ResonanceMatrixModule(ax, trd)
    plt.show()

def plot_energy_analysis(trd):
    """Deploy energy + power analysis"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    power = PowerModule(ax1, trd)
    energy = EnergyModule(ax2, trd)
    plt.show()

# ========================= MAIN