"""
Simulateur de test (mock) qui génère des données réalistes sans appeler le binaire CSiPI.
Utilisé pour la démonstration et les tests de l'interface.
"""

import numpy as np


def yamamura_yield(E0: float, E_th: float, S_n: float, Q: float = 1.0) -> float:
    """Formule de Yamamura pour le rendement de pulvérisation."""
    if E0 <= E_th:
        return 0.0
    return Q * S_n * (1.0 - np.sqrt(E_th / E0)) ** 2


def mock_yield_vs_energy(
    ion_Z: int,
    ion_mass: float,
    target_Z: int,
    target_mass: float,
    angle_deg: float = 0.0,
    energies: np.ndarray = None,
) -> np.ndarray:
    """Calcule un rendement Y(E) réaliste via la formule de Yamamura."""
    if energies is None:
        energies = np.logspace(1, 4, 200)

    # Paramètres empiriques approximatifs
    mu = ion_mass / target_mass
    E_th = 8.0 * target_Z * ion_Z / (target_Z + ion_Z)  # seuil approximatif en eV
    Q = 0.5 * (1.0 + 0.35 * mu) * target_Z ** 0.5

    # Correction angulaire (Yamamura)
    f_angle = 1.0 / np.cos(np.radians(angle_deg)) ** 1.5 if angle_deg < 88 else 0.0

    yields = np.array([
        yamamura_yield(E, E_th, S_n=0.042 * mu / (1 + mu), Q=Q) * f_angle
        for E in energies
    ])
    # Normalisation réaliste
    peak = yields.max() if yields.max() > 0 else 1.0
    target_peak = np.clip(0.3 + 0.015 * (target_Z - 10), 0.05, 3.0)
    yields = yields / peak * target_peak
    return yields


def mock_yield_vs_angle(
    ion_Z: int,
    ion_mass: float,
    target_Z: int,
    target_mass: float,
    energy_eV: float = 800.0,
    angles: np.ndarray = None,
) -> np.ndarray:
    """Rendement Y(θ) : forme en cosinus modifiée."""
    if angles is None:
        angles = np.linspace(0, 85, 86)
    theta_r = np.radians(angles)
    Y0 = mock_yield_vs_energy(
        ion_Z, ion_mass, target_Z, target_mass, 0.0,
        np.array([energy_eV])
    )[0]
    # Yamamura angulaire
    f = (1.0 / np.cos(theta_r + 1e-9)) ** 1.5 * np.exp(
        -0.5 * (1.0 / np.cos(theta_r + 1e-9) - 1.0)
    )
    f[angles > 88] = 0.0
    return Y0 * f


def mock_angular_distribution(
    num_bins: int = 90,
    ion_angle_deg: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Distribution angulaire des atomes pulvérisés (cosinus + offset)."""
    angles = np.linspace(0, 180, num_bins)
    theta_r = np.radians(angles - 90.0)
    # Lobe principal (cos) décalé par rapport à l'angle d'incidence
    shift = np.radians(ion_angle_deg * 0.5)
    dist = np.cos(theta_r + shift) ** 2
    dist = np.clip(dist, 0, None)
    dist /= dist.sum() + 1e-12
    return angles, dist


def mock_energy_distribution(
    num_bins: int = 100,
    surface_binding_energy_eV: float = 6.8,
    ion_energy_eV: float = 800.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Distribution en énergie des atomes pulvérisés (Thompson)."""
    E_s = surface_binding_energy_eV
    E_max = ion_energy_eV * 0.5
    energies = np.linspace(0.1, E_max, num_bins)
    # Formule de Thompson
    dist = energies / (energies + E_s) ** 3
    dist /= dist.sum() + 1e-12
    return energies, dist


def mock_trajectories(
    num_trajectories: int = 30,
    max_depth_nm: float = 50.0,
    ion_angle_deg: float = 0.0,
) -> list:
    """Génère des trajectoires d'ions simulées (BCA simplifiée)."""
    rng = np.random.default_rng(42)
    trajectories = []
    for _ in range(num_trajectories):
        n_steps = rng.integers(5, 30)
        x = np.zeros(n_steps + 1)
        z = np.zeros(n_steps + 1)
        # Direction initiale
        dx = np.sin(np.radians(ion_angle_deg))
        dz = np.cos(np.radians(ion_angle_deg))
        for i in range(1, n_steps + 1):
            step = rng.exponential(max_depth_nm / n_steps)
            deflect = rng.normal(0, 15)
            angle_r = np.radians(deflect)
            new_dx = dx * np.cos(angle_r) - dz * np.sin(angle_r)
            new_dz = dx * np.sin(angle_r) + dz * np.cos(angle_r)
            norm = np.hypot(new_dx, new_dz) + 1e-12
            dx, dz = new_dx / norm, new_dz / norm
            x[i] = x[i - 1] + dx * step
            z[i] = z[i - 1] + dz * step
            if z[i] < 0:  # particule rétro-diffusée
                break
        trajectories.append((x[:i + 1], z[:i + 1]))
    return trajectories


def mock_sputtered_trajectories(
    num_atoms: int = 20,
    ion_angle_deg: float = 0.0,
) -> list:
    """Trajectoires des atomes éjectés."""
    rng = np.random.default_rng(7)
    trajectories = []
    for _ in range(num_atoms):
        emission_angle = rng.uniform(5, 85)
        # côté aléatoire
        side = rng.choice([-1, 1])
        theta_r = np.radians(emission_angle)
        t = np.linspace(0, 20, 20)
        x = side * t * np.sin(theta_r)
        z = -t * np.cos(theta_r)  # vers l'extérieur (z négatif = vide)
        trajectories.append((x, z))
    return trajectories
