"""
Barre de rappel des paramètres actifs de simulation.
Affichée en haut de chaque panneau graphique.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt

from core.simulation_config import SimulationConfig


class _Chip(QLabel):
    """Pastille colorée affichant une paire clé/valeur."""

    def __init__(self, icon: str, value: str, color: str, bg: str):
        super().__init__()
        self._icon = icon
        self._color = color
        self._bg = bg
        self.set_value(value)
        self.setAlignment(Qt.AlignCenter)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            f"QLabel {{ background: {self._bg}; color: {self._color}; "
            f"border-radius: 10px; padding: 3px 10px; "
            f"font-size: 11px; font-weight: 600; }}"
        )

    def set_value(self, value: str):
        self.setText(f"{self._icon}  {value}")

    def update_theme(self, dark: bool):
        if dark:
            # En mode sombre, assombrir les backgrounds
            self._bg = self._bg  # conservé tel quel via stylesheet globale
        self._apply_style()


class ParamBar(QWidget):
    """
    Barre horizontale affichant les paramètres clés de la simulation active.
    Utilisation : instancier, appeler update_config(cfg) à chaque changement.
    """

    # (icon, label, color_light_fg, color_light_bg)
    _CHIP_DEFS = [
        ("⚡", "ion",    "#1565C0", "#E3F2FD"),
        ("🎯", "cible",  "#2E7D32", "#E8F5E9"),
        ("⚡", "énergie","#6A1B9A", "#F3E5F5"),
        ("📐", "angle",  "#E65100", "#FFF3E0"),
        ("🔢", "ions",   "#00695C", "#E0F2F1"),
        ("⚛",  "potentiel", "#455A64", "#ECEFF1"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        title = QLabel("Simulation active :")
        title.setStyleSheet("color: #757575; font-size: 10px; font-weight: 500;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(sep)

        icons   = ["⚡", "🎯", "⚡", "📐", "🔢", "⚛"]
        colors  = ["#1565C0", "#2E7D32", "#6A1B9A", "#E65100", "#00695C", "#455A64"]
        bgs     = ["#E3F2FD", "#E8F5E9", "#F3E5F5", "#FFF3E0", "#E0F2F1", "#ECEFF1"]

        self._chips: list[_Chip] = []
        for icon, color, bg in zip(icons, colors, bgs):
            chip = _Chip(icon, "…", color, bg)
            self._chips.append(chip)
            layout.addWidget(chip)

        layout.addStretch()

        self.setStyleSheet(
            "ParamBar { background: #F8F9FA; border-bottom: 1px solid #E0E0E0; "
            "border-radius: 0px; }"
        )

    def update_config(self, cfg: SimulationConfig):
        ion    = cfg.ion
        target = cfg.target_layers[0].element if cfg.target_layers else "?"
        pot    = cfg.physics.potential

        values = [
            f"{ion.element}  (Z={ion.Z}, M={ion.mass_amu:.2f} u)",
            target,
            f"{ion.energy_eV:,.0f} eV",
            f"{ion.angle_deg:.1f}°",
            f"{ion.num_ions:,}",
            pot,
        ]
        for chip, val in zip(self._chips, values):
            chip.set_value(val)

    def apply_dark(self, dark: bool):
        """Adapte les couleurs au thème sombre/clair."""
        dark_bgs  = ["#1A237E22", "#1B5E2022", "#4A148C22", "#BF360C22", "#004D4022", "#37474F22"]
        light_bgs = ["#E3F2FD",   "#E8F5E9",   "#F3E5F5",   "#FFF3E0",   "#E0F2F1",   "#ECEFF1"]
        dark_fgs  = ["#90CAF9",   "#A5D6A7",   "#CE93D8",   "#FFCC80",   "#80CBC4",   "#B0BEC5"]
        light_fgs = ["#1565C0",   "#2E7D32",   "#6A1B9A",   "#E65100",   "#00695C",   "#455A64"]

        bgs = dark_bgs if dark else light_bgs
        fgs = dark_fgs if dark else light_fgs

        for chip, fg, bg in zip(self._chips, fgs, bgs):
            chip._color = fg
            chip._bg    = bg
            chip._apply_style()

        bar_bg = "#1E1E2E" if dark else "#F8F9FA"
        sep_c  = "#45475A" if dark else "#E0E0E0"
        self.setStyleSheet(
            f"ParamBar {{ background: {bar_bg}; border-bottom: 1px solid {sep_c}; }}"
        )
