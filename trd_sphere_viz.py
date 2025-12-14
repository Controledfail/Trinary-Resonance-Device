import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap

# ============================================================================
# TRD UNIFIED SPHERE VISUALIZATION
# Maps complex impedance/mass space onto Riemann sphere via Smith chart
# Shows canonical triangle (μ = 0, 1, i) as fundamental geometric structure
# ============================================================================

def gamma_to_sphere(g):
    """
    Stereographic projection: complex Γ → unit sphere (x,y,z)
    North pole (0,0,1) maps to Γ=0, south pole to Γ=∞
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
    Maps: μ=0 → Γ=-1, μ=1 → Γ=0, μ=i → Γ=(i-1)/(i+1)
    """
    return (mu - 1) / (mu + 1)

def slerp(p1, p2, n=200):
    """
    Spherical linear interpolation (geodesic on sphere)
    Shortest great-circle path between two points
    """
    p1 = p1 / np.linalg.norm(p1)
    p2 = p2 / np.linalg.norm(p2)
    dot = np.clip(np.dot(p1, p2), -1.0, 1.0)
    omega = np.arccos(dot)
    if np.isclose(omega, 0):
        return np.tile(p1, (n, 1))
    t = np.linspace(0, 1, n)
    return (np.sin((1-t)*omega)[:,None]*p1 + np.sin(t*omega)[:,None]*p2) / np.sin(omega)

def plot_const_R_circle(ax, R, color, alpha=0.4, linewidth=1.5, samples=800):
    """Plot constant-resistance circle on sphere"""
    tX = np.linspace(-10, 10, samples)
    z = R + 1j * tX
    gam = mu_to_gamma(z)
    pts = gamma_to_sphere(gam)
    ax.plot(pts[:,0], pts[:,1], pts[:,2], color=color, alpha=alpha, linewidth=linewidth)

def plot_const_X_arc(ax, X, color, alpha=0.4, linewidth=1.5, samples=800):
    """Plot constant-reactance arc on sphere"""
    tR = np.linspace(0.01, 10, samples)
    z = tR + 1j * X
    gam = mu_to_gamma(z)
    pts = gamma_to_sphere(gam)
    ax.plot(pts[:,0], pts[:,1], pts[:,2], color=color, alpha=alpha, linewidth=linewidth)

# ============================================================================
# BUILD VISUALIZATION
# ============================================================================

# Create figure with dark background
plt.style.use('dark_background')
fig = plt.figure(figsize=(14, 14), facecolor='#0a0a0a')
ax = fig.add_subplot(111, projection='3d', facecolor='#0a0a0a')

# Build sphere mesh
u = np.linspace(0, 2*np.pi, 150)
v = np.linspace(0, np.pi, 75)
xs = np.outer(np.cos(u), np.sin(v))
ys = np.outer(np.sin(u), np.sin(v))
zs = np.outer(np.ones_like(u), np.cos(v))

# Plot translucent sphere with subtle gradient
colors = cm.viridis(zs/2 + 0.5)
ax.plot_surface(xs, ys, zs, facecolors=colors, alpha=0.12, 
                edgecolor='none', antialiased=True, shade=True)

# ============================================================================
# CANONICAL TRD TRIANGLE (μ = 0, 1, i)
# ============================================================================

mus = [0, 1, 1j]
labels = ['μ=0\n(short)', 'μ=1\n(matched)', 'μ=i\n(reactive)']
colors_tri = ['#ff3366', '#33ff66', '#3366ff']
gammas = [mu_to_gamma(m) for m in mus]
points = gamma_to_sphere(gammas)

# Plot triangle vertices with glow effect
for i, (label, p, color) in enumerate(zip(labels, points, colors_tri)):
    # Outer glow
    ax.scatter(p[0], p[1], p[2], s=600, c=color, alpha=0.2, edgecolors='none')
    # Middle glow
    ax.scatter(p[0], p[1], p[2], s=300, c=color, alpha=0.5, edgecolors='none')
    # Core point
    ax.scatter(p[0], p[1], p[2], s=150, c=color, alpha=1.0, 
               edgecolors='white', linewidths=2, zorder=100)
    # Label
    ax.text(p[0]*1.15, p[1]*1.15, p[2]*1.15, label, 
            fontsize=13, weight='bold', color=color, 
            ha='center', va='center', zorder=101)

# Draw geodesic triangle edges
pairs = [(0,1), (1,2), (2,0)]
edge_colors = ['#ff9966', '#66ff99', '#6699ff']
for (a, b), edge_color in zip(pairs, edge_colors):
    curve = slerp(points[a], points[b], n=400)
    # Outer glow
    ax.plot(curve[:,0], curve[:,1], curve[:,2], 
            color=edge_color, linewidth=8, alpha=0.15, zorder=50)
    # Inner line
    ax.plot(curve[:,0], curve[:,1], curve[:,2], 
            color=edge_color, linewidth=3, alpha=0.8, zorder=51)

# ============================================================================
# SMITH CHART STRUCTURE
# ============================================================================

# Unit circle (|Γ|=1, lossless boundary)
theta = np.linspace(0, 2*np.pi, 500)
unit_circle = np.exp(1j*theta)
unit_sphere = gamma_to_sphere(unit_circle)
ax.plot(unit_sphere[:,0], unit_sphere[:,1], unit_sphere[:,2], 
        color='#ffaa00', linewidth=3.5, alpha=0.9, 
        label='|Γ|=1 (lossless)', zorder=60)

# Constant-resistance circles (real axis slices)
R_values = [0.2, 0.5, 1.0, 2.0, 5.0]
R_colors = ['#ff6666', '#ff8866', '#ffaa66', '#ffcc66', '#ffee66']
for R, color in zip(R_values, R_colors):
    plot_const_R_circle(ax, R, color, alpha=0.5, linewidth=1.5)

# Constant-reactance arcs (imaginary axis slices)
X_values = [0.5, 1.0, 2.0, 5.0]
X_colors = ['#6666ff', '#6688ff', '#66aaff', '#66ccff']
for X, color in zip(X_values, X_colors):
    plot_const_X_arc(ax, X, color, alpha=0.5, linewidth=1.5)
    plot_const_X_arc(ax, -X, color, alpha=0.5, linewidth=1.5)  # Symmetric

# ============================================================================
# COORDINATE AXES & ANNOTATIONS
# ============================================================================

# Draw subtle coordinate axes
axis_length = 1.3
axes_data = [
    ([0, axis_length], [0, 0], [0, 0], '#ff4444', 'Re(Γ)'),
    ([0, 0], [0, axis_length], [0, 0], '#44ff44', 'Im(Γ)'),
    ([0, 0], [0, 0], [0, axis_length], '#4444ff', 'projection')
]
for x, y, z, color, label in axes_data:
    ax.plot(x, y, z, color=color, linewidth=2, alpha=0.3, linestyle='--')

# Add key annotations
title_text = (
    "TRD Unified Sphere: Riemann Sphere + Smith Chart\n"
    "Canonical Triangle (μ = 0, 1, i) Encodes Force Structure"
)
ax.text2D(0.5, 0.97, title_text, transform=ax.transAxes,
          fontsize=16, weight='bold', ha='center', va='top',
          color='#ffffff', bbox=dict(boxstyle='round,pad=0.5', 
                                     facecolor='#1a1a1a', 
                                     edgecolor='#666666', linewidth=2))

# Legend
legend_text = (
    "Resistance circles (red-yellow)\n"
    "Reactance arcs (blue)\n"
    "Geodesic triangle (glowing edges)\n"
    "Unit circle = lossless boundary"
)
ax.text2D(0.02, 0.98, legend_text, transform=ax.transAxes,
          fontsize=10, ha='left', va='top', color='#cccccc',
          family='monospace', alpha=0.8)

# ============================================================================
# VIEW CONFIGURATION
# ============================================================================

ax.set_box_aspect([1, 1, 1])
ax.set_xlim([-1.1, 1.1])
ax.set_ylim([-1.1, 1.1])
ax.set_zlim([-1.1, 1.1])

# Remove axis ticks but keep panes for depth
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

# Set optimal viewing angle
ax.view_init(elev=20, azim=45)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(left=0, right=1, top=0.97, bottom=0.03)

# Display
plt.show()

# ============================================================================
# MATHEMATICAL INTERPRETATION
# ============================================================================
print("\n" + "="*70)
print("TRD UNIFIED SPHERE: GEOMETRIC INTERPRETATION")
print("="*70)
print("\nCANONICAL TRIANGLE VERTICES:")
print(f"  μ=0 (short)    → Γ = {mu_to_gamma(0):.4f}")
print(f"  μ=1 (matched)  → Γ = {mu_to_gamma(1):.4f}")
print(f"  μ=i (reactive) → Γ = {mu_to_gamma(1j):.4f}")
print("\nGEOMETRIC PROPERTIES:")
print("  • Triangle edges are geodesics (shortest paths on sphere)")
print("  • Hypotenuse |μ=1 to μ=i| → 0 in limit (degenerate geometry)")
print("  • Smith chart = stereographic projection of complex impedance")
print("  • Unit circle |Γ|=1 = lossless/reactive boundary")
print("\nFORCE STRUCTURE ENCODING:")
print("  • Real leg (0→1):      Mass/Weak force")
print("  • Imaginary leg (0→i): Phase/EM force")
print("  • Null hypotenuse:     Confinement/Strong force")
print("="*70 + "\n")