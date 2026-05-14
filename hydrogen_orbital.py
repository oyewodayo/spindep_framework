"""
Hydrogen Atom Orbital Visualization
Replicates the dashboard showing:
  1. Polar plot (angular probability distribution)
  2. Probability density dot cloud (blue)
  3. 3D sphere isosurface (yellow)
  4. Wavefunction formula
  5. Radial probability distribution graph
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D
from scipy.special import sph_harm, genlaguerre, factorial
import warnings

from datetime import datetime
print(f"Generating hydrogen orbital visualization... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
warnings.filterwarnings("ignore")

# ── Quantum numbers (1s orbital) ──────────────────────────────────────────────
n, l, m = 1, 0, 0
a0 = 1.0  # Bohr radius (atomic units)

# ── Hydrogen radial wavefunction R_{n,l}(r) ───────────────────────────────────
def radial_wavefunction(r, n, l, a0=1.0):
    rho = 2 * r / (n * a0)
    norm = np.sqrt(
        (2 / (n * a0))**3
        * factorial(n - l - 1)
        / (2 * n * factorial(n + l)**3)
    )
    L = genlaguerre(n - l - 1, 2 * l + 1)
    return norm * np.exp(-rho / 2) * rho**l * L(rho)

# ── Full probability density |ψ|² ─────────────────────────────────────────────
def psi_squared(r, theta, phi, n, l, m, a0=1.0):
    R = radial_wavefunction(r, n, l, a0)
    Y = sph_harm(m, l, phi, theta)  # (m, l, phi, theta)
    return np.abs(R * Y) ** 2

# ═══════════════════════════════════════════════════════════════════════════════
# Figure layout
# ═══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 9), facecolor="#0a0a0a")

gs = gridspec.GridSpec(
    3, 3,
    figure=fig,
    left=0.03, right=0.97,
    top=0.97, bottom=0.05,
    wspace=0.35, hspace=0.45,
)

ax_polar   = fig.add_subplot(gs[:, 0], projection="polar")
ax_cloud   = fig.add_subplot(gs[0, 1])
ax_sphere  = fig.add_subplot(gs[0, 2], projection="3d")
ax_formula = fig.add_subplot(gs[1, 1:])
ax_radial  = fig.add_subplot(gs[2, 1:])

for ax in [ax_cloud, ax_formula, ax_radial]:
    ax.set_facecolor("#0a0a0a")
ax_sphere.set_facecolor("#0a0a0a")
ax_polar.set_facecolor("#0a0a0a")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. POLAR PLOT
# ═══════════════════════════════════════════════════════════════════════════════
theta_1d = np.linspace(0, 2 * np.pi, 800)

# For 1s orbital → constant angular distribution
r_angular = np.ones_like(theta_1d)

# Radial glow
r_2d = np.linspace(0, 1, 400)
th_2d = np.linspace(0, 2 * np.pi, 400)
R2, T2 = np.meshgrid(r_2d, th_2d)
glow = np.exp(-5 * R2**2)

# // Create a "black" background with the glow pattern
black= np.zeros_like(glow)

ax_polar.pcolormesh(T2, R2, black, cmap="YlOrBr", shading="auto",
                    vmin=0, vmax=1, zorder=1)

ax_polar.plot(theta_1d, r_angular, color="#ffee88",
              lw=1.5, alpha=0.9, zorder=3)

# ── FIXED POLAR STYLING ───────────────────────────────────────────────────────
ax_polar.set_theta_zero_location("N")  # FIXED
ax_polar.set_theta_direction(-1)
ax_polar.set_rlim(0, 1.05)

ax_polar.tick_params(colors="white", labelsize=8)

if "polar" in ax_polar.spines:
    ax_polar.spines["polar"].set_color("#444")

angles = np.arange(0, 360, 15)
labels = [f"{a}°" for a in angles]

ax_polar.set_thetagrids(angles, labels=labels)

for lbl in ax_polar.get_xticklabels():
    lbl.set_color("white")
    lbl.set_fontsize(7)

# Clean annotations
ax_polar.text(0.5, 1.05, "θ = 0°",
              transform=ax_polar.transAxes,
              ha="center", va="bottom",
              color="white", fontsize=8)

ax_polar.text(0.02, 0.5, "φ = 180°",
              transform=ax_polar.transAxes,
              color="white", fontsize=8)

ax_polar.text(0.88, 0.5, "φ = 0°",
              transform=ax_polar.transAxes,
              color="white", fontsize=8)

# Radial rings
for r_tick in np.linspace(0.2, 1.0, 5):
    ax_polar.plot(np.linspace(0, 2*np.pi, 200),
                  [r_tick]*200, color="#333", lw=0.5, zorder=2)

# ═══════════════════════════════════════════════════════════════════════════════
# 2. PROBABILITY DENSITY CLOUD
# ═══════════════════════════════════════════════════════════════════════════════
np.random.seed(42)
N_dots = 4000

r_max = 5 * a0
samples_x, samples_y, samples_z = [], [], []

psi_max = psi_squared(0.01, np.pi/2, 0, n, l, m, a0) * 1.1

max_iter = 50
iters = 0

while len(samples_x) < N_dots and iters < max_iter:
    iters += 1

    rx = np.random.uniform(-r_max, r_max, 5000)
    ry = np.random.uniform(-r_max, r_max, 5000)
    rz = np.random.uniform(-r_max, r_max, 5000)

    r = np.sqrt(rx**2 + ry**2 + rz**2) + 1e-10
    th = np.arccos(np.clip(rz / r, -1, 1))
    ph = np.arctan2(ry, rx)

    prob = psi_squared(r, th, ph, n, l, m, a0)
    accept = np.random.uniform(0, psi_max, len(prob)) < prob

    samples_x.extend(rx[accept])
    samples_y.extend(ry[accept])
    samples_z.extend(rz[accept])

samples_x = np.array(samples_x[:N_dots])
samples_y = np.array(samples_y[:N_dots])

dist = np.sqrt(samples_x**2 + samples_y**2)
dist_norm = dist / dist.max()

ax_cloud.scatter(samples_x, samples_y, s=0.6,
                 c=dist_norm, cmap="Blues_r",
                 alpha=0.6, linewidths=0)

ax_cloud.set_xlim(-r_max, r_max)
ax_cloud.set_ylim(-r_max, r_max)
ax_cloud.set_aspect("equal")
ax_cloud.axis("off")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. 3D SPHERE
# ═══════════════════════════════════════════════════════════════════════════════
u = np.linspace(0, 2 * np.pi, 60)
v = np.linspace(0, np.pi, 60)

xs = np.outer(np.cos(u), np.sin(v))
ys = np.outer(np.sin(u), np.sin(v))
zs = np.outer(np.ones(np.size(u)), np.cos(v))

ax_sphere.plot_surface(xs, ys, zs,
                       color="#d4b800", alpha=0.92,
                       linewidth=0)

ax_sphere.set_box_aspect([1, 1, 1])
ax_sphere.axis("off")
ax_sphere.view_init(elev=20, azim=30)

# ═══════════════════════════════════════════════════════════════════════════════
# 4. FORMULA
# ═══════════════════════════════════════════════════════════════════════════════
ax_formula.axis("off")

ax_formula.text(
    0.5, 0.5,
    r"$\psi_{nlm} = R_{n,l} Y_l^m e^{-iE_n t/\hbar}$",
    fontsize=26, color="white",
    ha="center", va="center",
    transform=ax_formula.transAxes,
)

# ═══════════════════════════════════════════════════════════════════════════════
# 5. RADIAL DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════════
r_vals = np.linspace(0.001, 20 * a0, 1000)
R_vals = radial_wavefunction(r_vals, n, l, a0)
P_r = r_vals**2 * R_vals**2

ax_radial.fill_between(r_vals, P_r, color="#00bcd4", alpha=0.7)
ax_radial.plot(r_vals, P_r, color="#00e5ff", lw=1.2)

ax_radial.set_xlim(0, 20)
ax_radial.set_ylim(0, P_r.max() * 1.1)
ax_radial.set_facecolor("#0d1a1f")

ax_radial.tick_params(colors="#555", labelsize=7)
for spine in ax_radial.spines.values():
    spine.set_color("#222")

ax_radial.grid(True, color="#1a2a2a", linewidth=0.5)
ax_radial.set_xlabel("r / a₀", color="#888", fontsize=8)
ax_radial.set_ylabel("P(r)", color="#888", fontsize=8)

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE
# ═══════════════════════════════════════════════════════════════════════════════
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"hydrogen_orbital_{timestamp}.png"
plt.savefig(filename,
            dpi=180, bbox_inches="tight",
            facecolor="#0a0a0a")

print(f"Saved → {filename}")
plt.show()