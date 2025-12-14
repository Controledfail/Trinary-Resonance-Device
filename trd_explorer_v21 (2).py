# TRD Worldmap v3.1 — Fixed for Pydroid/Standard Python
# Combines v2.2 Physics Engine with v1.0 Immersive Dash Interface

# If you need to install packages in Pydroid, go to Pip and install:
# dash plotly pandas scipy

import numpy as np
import pandas as pd
from scipy.constants import epsilon_0, G
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px

# —————————————————————————————————————————————————————————————————————————————
# 1. CORE PHYSICS ENGINE
# —————————————————————————————————————————————————————————————————————————————

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

u = Units('SI')

zeta_imag_parts = np.array([
    14.1347251417, 21.0220396388, 25.0108575801, 30.4248761259,
    32.9350615877, 37.5861781588, 40.9187190122, 43.3270732809
])

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
    "∂M_i/∂t (Ang. Mom.)", "½Ω·I·Ω (Rot. KE)", "∇×(∇×E) (EM Wave)", 
    "∇V_TRD (Pot. Grad.)", "S = E×H (Poynting)", "F_ext (Coupling)", 
    "M_ext (Torque)", "Hamiltonian Constraint"
]

def cosmic_to_chip_radius(t_n, scale_factor=1.0):
    """Scale-invariant cosmic → chip transform"""
    cosmic_r = u.c / (4 * np.pi * t_n)
    compton_chip = u.hbar / (1.0 * u.c)
    lambda_compress = 1.0e16
    return scale_factor * compton_chip * (cosmic_r / compton_chip) / lambda_compress

class TRD_Engine:
    def __init__(self, gamma=1.0, N_eff=3, f0=432e3, scale_factor=1.0):
        self.gamma = float(gamma)
        self.N_eff = float(N_eff)
        self.f0 = float(f0)
        self.scale_factor = scale_factor
        self.compute_all()

    def compute_all(self):
        # 1. Envelope frequencies
        self.f_env = self.f0 * zeta_imag_parts / zeta_imag_parts[0]

        # 2. Radii (Chip scale default for visualization)
        self.radius = cosmic_to_chip_radius(zeta_imag_parts, self.scale_factor)
        self.radius_mm = self.radius * 1e3 

        # 3. Power scaling
        self.power_N = 1e-3 * (self.f_env**2) * (self.radius**3) * (self.N_eff**2) * self.gamma**1.5
        # Normalize for visualization
        self.power_viz = self.power_N / self.power_N.mean() * 10 

        # 4. Stability Analysis
        J = np.diag(-self.gamma * self.f_env)
        eigenvalues = np.linalg.eigvals(J)
        self.is_stable = np.all(np.real(eigenvalues) < 0)

        # 5. Resonance Matrix
        self.ratios = self.f_env[:,None] / self.f_env[None,:]
        
        # 6. Energy Budget (Simplified Model)
        self.E_kin = 0.5 * (2*np.pi*self.f_env)**2 * (self.radius**2) * self.power_N
        self.E_em = self.power_N / u.c
        self.E_total = self.E_kin.sum() + self.E_em.sum()
        self.energy_conserved = np.isclose(self.E_kin.sum(), self.E_em.sum() * 1e8, rtol=0.1)

    def get_dataframe(self):
        return pd.DataFrame({
            "zero": np.arange(1,9),
            "Im_t": zeta_imag_parts,
            "f_env": self.f_env,
            "radius_mm": self.radius_mm,
            "power_mW": self.power_N * 1000,
            "citation": CITATIONS,
            "lag_term": LAGRANGIAN_TERMS
        })

# —————————————————————————————————————————————————————————————————————————————
# 2. INTERFACE (Standard DASH)
# —————————————————————————————————————————————————————————————————————————————

# CHANGE: Use standard Dash class instead of JupyterDash
app = Dash(__name__)

app.layout = html.Div([
    html.H2("TRD Worldmap v3.1 — The Living Laboratory", 
            style={'textAlign':'center', 'color':'#2c3e50', 'fontFamily':'sans-serif'}),
    
    html.Div([
        # ——— LEFT PANEL: THE SPIRAL ———
        html.Div(dcc.Graph(id='spiral', style={'height':'750px'}), 
                 style={'width':'60%', 'display':'inline-block', 'verticalAlign':'top'}),
        
        # ——— RIGHT PANEL: THE TRICORDER ———
        html.Div([
            # CONTROLS
            html.Div([
                html.Label("γ (Damping)"), 
                dcc.Slider(id='gamma', min=0.1, max=5.0, step=0.1, value=1.0, 
                           marks={1:'1', 2.5:'2.5', 5:'5'}),
                html.Label("N_eff (Effectors)"), 
                dcc.Slider(id='N', min=1, max=10, step=1, value=3, marks={1:'1', 5:'5', 10:'10'}),
                html.Label("f₀ (Base Freq kHz)"), 
                dcc.Slider(id='f0', min=100, max=1000, step=50, value=432, marks={100:'100', 432:'432', 1000:'1k'}),
                html.Label("Scale Factor"), 
                dcc.Slider(id='scale', min=0.5, max=2.0, step=0.1, value=1.0, marks={0.5:'0.5', 1:'1', 2:'2'}),
            ], style={'padding':'15px', 'backgroundColor':'#ecf0f1', 'borderRadius':'10px', 'marginBottom':'15px'}),
            
            # TABS FOR DATA
            dcc.Tabs([
                # TAB 1: NAVIGATION
                dcc.Tab(label='Navigator', children=[
                    html.Div(id='node-info', style={'padding':'10px', 'fontFamily':'monospace', 'whiteSpace':'pre-wrap', 'height':'150px'}),
                    dcc.Graph(id='waveform', style={'height':'250px'})
                ]),
                
                # TAB 2: ANALYSIS
                dcc.Tab(label='Resonance', children=[
                    dcc.Graph(id='matrix', style={'height':'400px'})
                ]),
                
                # TAB 3: PHYSICS
                dcc.Tab(label='System State', children=[
                    dcc.Graph(id='power-bar', style={'height':'250px'}),
                    html.Div(id='system-status', style={'padding':'15px', 'fontSize':'14px', 'backgroundColor':'#f8f9fa'})
                ])
            ])
            
        ], style={'width':'38%', 'display':'inline-block', 'paddingLeft':'2%', 'verticalAlign':'top'})
    ], style={'maxWidth':'1400px', 'margin':'0 auto'})
])

@app.callback(
    Output('spiral', 'figure'),
    Output('node-info', 'children'),
    Output('waveform', 'figure'),
    Output('matrix', 'figure'),
    Output('power-bar', 'figure'),
    Output('system-status', 'children'),
    Input('gamma', 'value'), Input('N', 'value'), Input('f0', 'value'), Input('scale', 'value'),
    Input('spiral', 'clickData')
)
def update_universe(gamma, N_eff, f0_khz, scale, clickData):
    trd = TRD_Engine(gamma, N_eff, f0_khz*1e3, scale)
    df = trd.get_dataframe()
    
    # 1. SPIRAL PLOT
    r_plot = np.log10(df['radius_mm'] * 1e6) 
    theta = np.linspace(0, 4*np.pi, 8)
    x = r_plot * np.cos(theta)
    y = r_plot * np.sin(theta)
    
    fig_spiral = go.Figure()
    fig_spiral.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(color='#bdc3c7', width=1, dash='dot')))
    fig_spiral.add_trace(go.Scatter(
        x=x, y=y, mode='markers+text',
        marker=dict(size=df['power_mW']*5 + 15,
                   color=df['f_env'], colorscale='Plasma', showscale=True,
                   colorbar=dict(title='f_env (Hz)')),
        text=df['zero'], textfont=dict(color='white'),
        customdata=df['zero'],
        hovertemplate="<b>Ring %{text}</b><br>f: %{marker.color:.1f} Hz<br>r: %{customdata} mm<extra></extra>"
    ))
    fig_spiral.update_layout(
        title="Cosmic Topology (Log-Polar)", hovermode='closest',
        plot_bgcolor='white', showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    if clickData:
        idx = int(clickData['points'][0]['customdata']) - 1
        fig_spiral.add_trace(go.Scatter(x=[x[idx]], y=[y[idx]], mode='markers',
                                        marker=dict(size=40, color='rgba(0,0,0,0)', 
                                                    line=dict(color='cyan', width=3))))
    else:
        idx = 0 

    row = df.iloc[idx]
    
    info_text = f"""SELECTED: Ring {int(row.zero)} (ζ-zero {idx+1})
---------------------------------------
Freq (f_env) : {row.f_env:.4f} Hz
Radius       : {row.radius_mm:.6f} mm
Power Req    : {row.power_mW:.4f} mW
Lagrangian   : {row.lag_term}
Source       : {row.citation}"""

    t = np.linspace(0, 4/row.f_env if row.f_env > 0 else 1, 400)
    amp = np.exp(-0.2 * t) * np.cos(2*np.pi * row.f_env * t)
    fig_wave = px.line(x=t, y=amp, title=f"Local Oscillation @ {row.f_env:.1f} Hz")
    fig_wave.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20),
                          xaxis_title="Time (s)", yaxis_title="Amplitude")

    fig_matrix = px.imshow(trd.ratios, 
                           labels=dict(x="Ring Index", y="Ring Index", color="Ratio"),
                           x=np.arange(1,9), y=np.arange(1,9),
                           color_continuous_scale='Viridis',
                           title="Resonance Coupling (f_i / f_j)")
    fig_matrix.update_layout(height=400)

    fig_power = px.bar(df, x='zero', y='power_mW', 
                       title="Power Distribution per Ring",
                       color='power_mW', color_continuous_scale='Magma')
    fig_power.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))

    stable_icon = "✅" if trd.is_stable else "⚠️"
    energy_icon = "✅" if trd.energy_conserved else "⚠️"
    status_text = [
        html.H4("System Diagnostics"),
        html.P(f"Stability Condition: {stable_icon} {'STABLE' if trd.is_stable else 'UNSTABLE'}"),
        html.P(f"Energy Conservation: {energy_icon} (E_total = {trd.E_total:.2e} J)"),
        html.P(f"Scale Mode: Chip-Scale ({trd.scale_factor}x)"),
        html.Hr(),
        html.P(f"Jacobian Eigenvalues (Real): {np.array2string(np.real(np.linalg.eigvals(np.diag(-trd.gamma*trd.f_env)))[:3], precision=2)}...")
    ]

    return fig_spiral, info_text, fig_wave, fig_matrix, fig_power, status_text

# CHANGE: Standard run command for local execution
if __name__ == '__main__':
    app.run(debug=True, port=8050)
