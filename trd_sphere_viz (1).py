import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap

# ============================================================================
# TRD UNIFIED BIDIRECTIONAL SPHERE
# Complete analytical continuation with positive/negative index encoding
# Implements circular geometric series: Σ ar^n for n ∈ ℤ (all integers)
# ============================================================================

def gamma_to_sphere(g):
    """
    Stereographic projection: complex Γ → unit sphere (x,y,z)
    North pole (0,0,1) maps to Γ=0, south pole (0,0,-1) to Γ=∞
    """
    g = np.array(g, dtype=complex)
    denom = 1 + np.abs(g)**2
    x = 2 * np.real(g) / denom
    y = 2 * np.imag(g) / denom
    z = (1 - np.abs(g)**2) / denom
    return np.vstack((x, y, z)).T

def mu_to_gamma(mu):
    """
    Möbius transformation: normalized mass/impedance μ → reflection coefficient Γ
    Γ = (μ - 1)/(μ + 1)
    """
    return (mu - 1) / (mu + 1)

def gamma_to_mu(gamma):
    """
    Inverse Möbius: Γ → μ
    μ = (1 + Γ)/(1 - Γ)
    """
    return (1 + gamma) / (1 - gamma)

def slerp(p1, p2, n=200):
    """Spherical linear interpolation (geodesic)"""
    p1 = p1 / np.linalg.norm(p1)
    p2 = p2 / np.linalg.norm(p2)
    dot = np.clip(np.dot(p1, p2), -1.0, 1.0)
    omega = np.arccos(dot)
    if np.isclose(omega, 0):
        return np.tile(p1, (n, 1))
    t = np.linspace(0, 1, n)
    return (np.sin((1-t)*omega)[:,None]*p1 + np.sin(t*omega)[:,None]*p2) / np.sin(omega)

def plot_bidirectional_path(ax, R, direction='both', color_pos='#ff6666', 
                           color_neg='#6666ff', alpha=0.5, samples=800):
    """
    Plot constant-R paths on BOTH hemispheres
    direction: 'both', 'positive' (northern), or 'negative' (southern)
    """
    tX = np.linspace(-10, 10, samples)
    
    if direction in ['both', 'positive']:
        # Positive (northern hemisphere) - standard Smith chart
        z_pos = R + 1j * tX
        gam_pos = mu_to_gamma(z_pos)
        pts_pos = gamma_to_sphere(gam_pos)
        ax.plot(pts_pos[:,0], pts_pos[:,1], pts_pos[:,2], 
                color=color_pos, alpha=alpha, linewidth=1.5)
    
    if direction in ['both', 'negative']:
        # Negative (southern hemisphere) - inverted/conjugate
        z_neg = R - 1j * tX  # Conjugate for southern hemisphere
        gam_neg = -mu_to_gamma(z_neg)  # Inversion for negative indices
        pts_neg = gamma_to_sphere(gam_neg)
        ax.plot(pts_neg[:,0], pts_neg[:,1], pts_neg[:,2], 
                color=color_neg, alpha=alpha, linewidth=1.5)

def plot_reactance_arc_bidirectional(ax, X, color_pos='#66ff66', 
                                    color_neg='#ff66ff', alpha=0.5, samples=800):
    """Plot constant-X arcs on both hemispheres"""
    tR = np.linspace(0.01, 10, samples)
    
    # Positive hemisphere
    z_pos = tR + 1j * X
    gam_pos = mu_to_gamma(z_pos)
    pts_pos = gamma_to_sphere(gam_pos)
    ax.plot(pts_pos[:,0], pts_pos[:,1], pts_pos[:,2], 
            color=color_pos, alpha=alpha, linewidth=1.5)
    
    # Negative hemisphere (conjugate + inversion)
    z_neg = tR - 1j * X
    gam_neg = -mu_to_gamma(z_neg)
    pts_neg = gamma_to_sphere(gam_neg)
    ax.plot(pts_neg[:,0], pts_neg[:,1], pts_neg[:,2], 
            color=color_neg, alpha=alpha, linewidth=1.5)

def plot_geometric_series_modes(ax, n_modes=8, r=0.8):
    """
    Plot circular geometric series modes: ar^n * e^{inθ}
    Positive n → northern, negative n → southern
    """
    theta = np.linspace(0, 2*np.pi, 200)
    
    for n in range(-n_modes, n_modes+1):
        if n == 0:
            continue
        # Mode frequency
        radius = r**abs(n)
        phase_shift = n * theta
        
        # Map to Gamma space
        gamma_n = radius * np.exp(1j * phase_shift)
        pts_n = gamma_to_sphere(gamma_n)
        
        # Color based on hemisphere
        color = '#ff4444' if n > 0 else '#4444ff'
        alpha = 0.3 * (1 - abs(n)/(n_modes+1))  # Fade with mode number
        
        ax.plot(pts_n[:,0], pts_n[:,1], pts_n[:,2], 
                color=color, alpha=alpha, linewidth=1.0)

# ============================================================================
# BUILD COMPLETE BIDIRECTIONAL SPHERE
# ============================================================================

plt.style.use('dark_background')
fig = plt.figure(figsize=(16, 14), facecolor='#0a0a0a')
ax = fig.add_subplot(111, projection='3d', facecolor='#0a0a0a')

# Build sphere mesh
u = np.linspace(0, 2*np.pi, 180)
v = np.linspace(0, np.pi, 90)
xs = np.outer(np.cos(u), np.sin(v))
ys = np.outer(np.sin(u), np.sin(v))
zs = np.outer(np.ones_like(u), np.cos(v))

# Color sphere by hemisphere: warm (north) / cool (south)
colors = np.zeros((*zs.shape, 4))
northern = zs > 0
southern = zs <= 0
colors[northern] = [0.8, 0.3, 0.3, 0.08]  # Warm red
colors[southern] = [0.3, 0.3, 0.8, 0.08]  # Cool blue

ax.plot_surface(xs, ys, zs, facecolors=colors, 
                edgecolor='none', antialiased=True, shade=True)

# ============================================================================
# EQUATOR: THE CRITICAL |Γ|=1 BOUNDARY
# ============================================================================

theta_eq = np.linspace(0, 2*np.pi, 500)
unit_circle = np.exp(1j*theta_eq)
equator_pts = gamma_to_sphere(unit_circle)
# Thick glowing equator
ax.plot(equator_pts[:,0], equator_pts[:,1], equator_pts[:,2], 
        color='#ffaa00', linewidth=6, alpha=0.3, zorder=90)
ax.plot(equator_pts[:,0], equator_pts[:,1], equator_pts[:,2], 
        color='#ffaa00', linewidth=3, alpha=1.0, zorder=91,
        label='|Γ|=1 Equator (Lossless)')

# ============================================================================
# CANONICAL TRIANGLE: EXTENDED TO BOTH HEMISPHERES
# ============================================================================

# Primary triangle (northern)
mus_north = [0, 1, 1j]
labels_north = ['μ=0\n(n→-∞)', 'μ=1\n(n=0)', 'μ=i\n(reactive)']
colors_north = ['#ff3366', '#33ff66', '#3366ff']
gammas_north = [mu_to_gamma(m) for m in mus_north]
points_north = gamma_to_sphere(gammas_north)

# Conjugate triangle (southern) - negative indices
mus_south = [gamma_to_mu(-mu_to_gamma(m)) for m in mus_north]
gammas_south = [mu_to_gamma(m) for m in mus_south]
points_south = gamma_to_sphere(gammas_south)
labels_south = ['μ=0̄\n(n→+∞)', 'μ=1̄\n(antipode)', 'μ=-i\n(conjugate)']
colors_south = ['#ff6699', '#66ff99', '#6699ff']

# Plot both triangles
for points, labels, colors, z_order in [(points_north, labels_north, colors_north, 100),
                                         (points_south, labels_south, colors_south, 95)]:
    for label, p, color in zip(labels, points, colors):
        # Glow effect
        ax.scatter(p[0], p[1], p[2], s=600, c=color, alpha=0.2, edgecolors='none')
        ax.scatter(p[0], p[1], p[2], s=300, c=color, alpha=0.5, edgecolors='none')
        ax.scatter(p[0], p[1], p[2], s=150, c=color, alpha=1.0, 
                   edgecolors='white', linewidths=2, zorder=z_order)
        offset = 1.15 if p[2] > 0 else 1.18
        ax.text(p[0]*offset, p[1]*offset, p[2]*offset, label, 
                fontsize=11, weight='bold', color=color, 
                ha='center', va='center', zorder=z_order+1)

# Draw geodesic triangles
for points, colors in [(points_north, ['#ff9966', '#66ff99', '#6699ff']),
                       (points_south, ['#ff99aa', '#88ffaa', '#8899ff'])]:
    pairs = [(0,1), (1,2), (2,0)]
    for (a, b), edge_color in zip(pairs, colors):
        curve = slerp(points[a], points[b], n=400)
        ax.plot(curve[:,0], curve[:,1], curve[:,2], 
                color=edge_color, linewidth=6, alpha=0.12, zorder=50)
        ax.plot(curve[:,0], curve[:,1], curve[:,2], 
                color=edge_color, linewidth=2.5, alpha=0.7, zorder=51)

# Connect antipodal points with great circles
for i in range(3):
    antipodal_curve = slerp(points_north[i], points_south[i], n=400)
    ax.plot(antipodal_curve[:,0], antipodal_curve[:,1], antipodal_curve[:,2],
            color='#ffff00', linewidth=2, alpha=0.4, linestyle='--', zorder=45)

# ============================================================================
# BIDIRECTIONAL SMITH CHART PATHS
# ============================================================================

# Constant-R circles (both hemispheres)
R_values = [0.2, 0.5, 1.0, 2.0, 5.0]
for R in R_values:
    plot_bidirectional_path(ax, R, direction='both',
                           color_pos='#ff5555', color_neg='#5555ff',
                           alpha=0.4, samples=800)

# Constant-X arcs (both hemispheres)
X_values = [0.5, 1.0, 2.0, 5.0]
for X in X_values:
    plot_reactance_arc_bidirectional(ax, X, 
                                    color_pos='#55ff55', color_neg='#ff55ff',
                                    alpha=0.4, samples=800)

# ============================================================================
# GEOMETRIC SERIES MODE STRUCTURE
# ============================================================================

plot_geometric_series_modes(ax, n_modes=6, r=0.75)

# ============================================================================
# POLES AND ANNOTATIONS
# ============================================================================

# North pole (Γ=0, n→+∞ accumulation)
north_pole = np.array([0, 0, 1])
ax.scatter(*north_pole, s=800, c='#ff0000', alpha=0.3, edgecolors='none')
ax.scatter(*north_pole, s=400, c='#ff0000', alpha=0.7, edgecolors='white', linewidths=3)
ax.text(0, 0, 1.25, 'NORTH POLE\nΓ=0\n(n→+∞)', 
        fontsize=12, weight='bold', color='#ff4444', ha='center', va='bottom')

# South pole (Γ=∞, n→-∞ accumulation)
south_pole = np.array([0, 0, -1])
ax.scatter(*south_pole, s=800, c='#0000ff', alpha=0.3, edgecolors='none')
ax.scatter(*south_pole, s=400, c='#0000ff', alpha=0.7, edgecolors='white', linewidths=3)
ax.text(0, 0, -1.25, 'SOUTH POLE\nΓ=∞\n(n→-∞)', 
        fontsize=12, weight='bold', color='#4444ff', ha='center', va='top')

# Main title
title_text = (
    "TRD BIDIRECTIONAL SPHERE: Complete Analytical Continuation\n"
    "Circular Geometric Series Σ(ar^n) with n ∈ ℤ\n"
    "Northern Hemisphere (red): n ≥ 0 | Southern Hemisphere (blue): n < 0"
)
ax.text2D(0.5, 0.98, title_text, transform=ax.transAxes,
          fontsize=14, weight='bold', ha='center', va='top',
          color='#ffffff', bbox=dict(boxstyle='round,pad=0.6', 
                                     facecolor='#1a1a1a', 
                                     edgecolor='#888888', linewidth=2))

# Legend box
legend_text = (
    "╔══════ BIDIRECTIONAL ENCODING ═══════╗\n"
    "║ NORTHERN (n>0): Forward rotation   ║\n"
    "║   • Red circles: +R paths          ║\n"
    "║   • Green arcs: +X paths           ║\n"
    "║                                    ║\n"
    "║ SOUTHERN (n<0): Reverse rotation   ║\n"
    "║   • Blue circles: -R paths         ║\n"
    "║   • Magenta arcs: -X paths         ║\n"
    "║                                    ║\n"
    "║ EQUATOR: |Γ|=1 (Lossless boundary) ║\n"
    "║ Yellow dashes: Antipodal geodesics ║\n"
    "╚═════════════════════════════════════╝\n"
    "\n"
    "Absolute value |ar^n| = distance\n"
    "Phase arg(e^{inθ}) = direction"
)
ax.text2D(0.01, 0.97, legend_text, transform=ax.transAxes,
          fontsize=9, ha='left', va='top', color='#cccccc',
          family='monospace', alpha=0.85,
          bbox=dict(boxstyle='round,pad=0.5', 
                   facecolor='#0a0a0a', edgecolor='#666666', linewidth=1))

# ============================================================================
# VIEW CONFIGURATION
# ============================================================================

ax.set_box_aspect([1, 1, 1])
ax.set_xlim([-1.2, 1.2])
ax.set_ylim([-1.2, 1.2])
ax.set_zlim([-1.2, 1.2])

ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False
ax.xaxis.pane.set_edgecolor('#333333')
ax.yaxis.pane.set_edgecolor('#333333')
ax.zaxis.pane.set_edgecolor('#333333')
ax.xaxis.pane.set_alpha(0.1)
ax.yaxis.pane.set_alpha(0.1)
ax.zaxis.pane.set_alpha(0.1)

ax.view_init(elev=15, azim=30)

plt.tight_layout()
plt.subplots_adjust(left=0, right=1, top=0.97, bottom=0.02)
plt.show()

# ============================================================================
# MATHEMATICAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("TRD BIDIRECTIONAL SPHERE: COMPLETE ANALYTICAL CONTINUATION")
print("="*80)
print("\nGEOMETRIC SERIES ENCODING:")
print("  Σ ar^n for n ∈ ℤ (all integers)")
print("  • Positive indices n ≥ 0 → Northern hemisphere (red)")
print("  • Negative indices n < 0 → Southern hemisphere (blue)")
print("  • Absolute value |ar^n| → Real distance traveled")
print("  • Phase arg(e^{inθ}) → Directional encoding")
print("\nCRITICAL BOUNDARIES:")
print("  • EQUATOR: |Γ|=1 (lossless, purely reactive)")
print("  • NORTH POLE: Γ=0 (perfect match, n→+∞ accumulation)")
print("  • SOUTH POLE: Γ=∞ (total reflection, n→-∞ accumulation)")
print("\nCANONICAL TRIANGLES:")
print("  Northern: μ = {0, 1, i}")
print("  Southern: μ̄ = antipodal conjugates")
print("  Antipodal geodesics: Connect n ↔ -n modes")
print("\nFUNCTIONAL EQUATION STRUCTURE:")
print("  η(-1/τ) = √(-iτ) η(τ)  [Modular transformation]")
print("  ζ(s) ↔ ζ(1-s)         [Riemann functional equation]")
print("  Γ(z)Γ(1-z) = π/sin(πz) [Reflection formula]")
print("\nPHYSICAL INTERPRETATION:")
print("  • Bidirectional phase flow (time-reversal symmetry)")
print("  • Symmetric spectral decomposition")
print("  • Infinite-dimensional Hilbert space (L² on circle)")
print("  • Quantum harmonic oscillator ladder operators (a†, a)")
print("  • TRD phase-field stabilization via antipodal balance")
print("="*80 + "\n")