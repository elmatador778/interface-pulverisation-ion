"""
Panneau de visualisation des trajectoires de particules.
Onglet « Trajectoires ».
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QPushButton, QCheckBox,
    QFileDialog, QFormLayout, QFrame,
)
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from parametres_sim import SimulationConfig
from simulateur import mock_trajectories, mock_sputtered_trajectories


class TrajCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(8, 5.5), tight_layout=True,
                          facecolor=matplotlib.rcParams.get("figure.facecolor", "#FFFFFF"))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(matplotlib.rcParams.get("axes.facecolor", "#FAFAFA"))
        super().__init__(self.fig)


class TrajectoriesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = SimulationConfig()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        ctrl_grp = QGroupBox("Contrôles de visualisation")
        ctrl_main = QHBoxLayout(ctrl_grp)
        ctrl_main.setSpacing(12)

        col1 = QFormLayout(); col1.setSpacing(4)
        self._n_ions_spin  = QSpinBox(); self._n_ions_spin.setRange(1, 200);  self._n_ions_spin.setValue(30)
        self._n_atoms_spin = QSpinBox(); self._n_atoms_spin.setRange(0, 100); self._n_atoms_spin.setValue(20)
        col1.addRow("Trajectoires ions :", self._n_ions_spin)
        col1.addRow("Atomes éjectés :",    self._n_atoms_spin)
        ctrl_main.addLayout(col1)

        sep = QFrame(); sep.setFrameShape(QFrame.VLine); sep.setStyleSheet("color: #E0E0E0;")
        ctrl_main.addWidget(sep)

        col2 = QVBoxLayout(); col2.setSpacing(4)
        self._show_surface   = QCheckBox("Surface de la cible");   self._show_surface.setChecked(True)
        self._show_ion_traj  = QCheckBox("Trajectoires des ions");  self._show_ion_traj.setChecked(True)
        self._show_sputtered = QCheckBox("Atomes éjectés");         self._show_sputtered.setChecked(True)
        self._show_arrow     = QCheckBox("Flèche d'incidence");     self._show_arrow.setChecked(True)
        for cb in (self._show_surface, self._show_ion_traj, self._show_sputtered, self._show_arrow):
            col2.addWidget(cb)
        ctrl_main.addLayout(col2)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.VLine); sep2.setStyleSheet("color: #E0E0E0;")
        ctrl_main.addWidget(sep2)

        col3 = QVBoxLayout(); col3.setSpacing(2)
        stats_title = QLabel("Statistiques (mock)")
        stats_title.setStyleSheet("font-weight: bold; color: #1565C0; font-size: 11px;")
        col3.addWidget(stats_title)
        self._stat_implanted     = QLabel("Implantés : –")
        self._stat_backscattered = QLabel("Rétro-diffusés : –")
        self._stat_sputtered     = QLabel("Éjectés : –")
        self._stat_mean_depth    = QLabel("Prof. moy. implant. : –")
        for lbl in (self._stat_implanted, self._stat_backscattered, self._stat_sputtered, self._stat_mean_depth):
            lbl.setStyleSheet("font-size: 11px; color: #424242;")
            col3.addWidget(lbl)
        ctrl_main.addLayout(col3)
        ctrl_main.addStretch()

        btn_col = QVBoxLayout()
        plot_btn = QPushButton("Tracer");          plot_btn.clicked.connect(self._plot)
        save_btn = QPushButton("Exporter figure"); save_btn.clicked.connect(self._save_figure)
        btn_col.addWidget(plot_btn); btn_col.addWidget(save_btn); btn_col.addStretch()
        ctrl_main.addLayout(btn_col)

        layout.addWidget(ctrl_grp)

        self._canvas  = TrajCanvas()
        self._toolbar = NavigationToolbar(self._canvas, self)
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)

        note = QLabel(
            "Les trajectoires sont générées par simulation Monte-Carlo BCA (approximation). "
            "Bleu = ion implanté  |  Rouge = rétro-diffusé  |  Orange = atome éjecté"
        )
        note.setStyleSheet("color: #757575; font-size: 10px; background: #F5F5F5; border-radius: 4px; padding: 4px 8px;")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

    def update_config(self, cfg: SimulationConfig):
        self.config = cfg
        self._plot()

    def _plot(self):
        cfg = self.config; ion = cfg.ion

        bg    = matplotlib.rcParams.get("figure.facecolor", "#FFFFFF")
        ax_bg = matplotlib.rcParams.get("axes.facecolor",   "#FAFAFA")
        self._canvas.fig.set_facecolor(bg)
        self._canvas.ax.set_facecolor(ax_bg)

        ax = self._canvas.ax; ax.clear()
        max_depth = cfg.physics.max_depth_nm
        n_ions = self._n_ions_spin.value(); n_atoms = self._n_atoms_spin.value()

        if self._show_surface.isChecked():
            ax.axhspan(0, max_depth, alpha=0.06, color="#78909C")
            ax.axhline(0, color="#455A64", linewidth=2.5, label="Surface")

        n_implanted = 0; n_backscattered = 0; depths_implanted = []

        if self._show_ion_traj.isChecked():
            trajs = mock_trajectories(num_trajectories=n_ions, max_depth_nm=max_depth, ion_angle_deg=ion.angle_deg)
            for i, (x, z) in enumerate(trajs):
                implanted = z[-1] >= 0
                color = "#1565C0" if implanted else "#E53935"
                ax.plot(x, z, color=color, linewidth=0.9, alpha=max(0.15, 1.0 - i / len(trajs) * 0.75))
                if implanted: n_implanted += 1; depths_implanted.append(z[-1])
                else: n_backscattered += 1
            ax.plot([], [], color="#1565C0", linewidth=1.5, label=f"Ion {ion.element} – implanté ({n_implanted})")
            ax.plot([], [], color="#E53935", linewidth=1.5, label=f"Ion {ion.element} – rétro-diffusé ({n_backscattered})")

        if self._show_sputtered.isChecked() and cfg.target_layers:
            s_trajs = mock_sputtered_trajectories(num_atoms=n_atoms, ion_angle_deg=ion.angle_deg)
            for i, (x, z) in enumerate(s_trajs):
                ax.plot(x, z, color="#FF6F00", linewidth=0.9, alpha=max(0.25, 1.0 - i / len(s_trajs) * 0.65), linestyle="--")
            ax.plot([], [], color="#FF6F00", linewidth=1.5, linestyle="--",
                    label=f"Atome {cfg.target_layers[0].element} éjecté ({n_atoms})")

        if self._show_arrow.isChecked():
            arrow_len = max_depth * 0.28
            dx = arrow_len * np.sin(np.radians(ion.angle_deg))
            dz = arrow_len * np.cos(np.radians(ion.angle_deg))
            ax.annotate("", xy=(dx * 0.85, arrow_len * 0.85 - dz * 0.85),
                        xytext=(-dx * 0.15, arrow_len - dz * 0.15),
                        arrowprops=dict(arrowstyle="-|>", color="#43A047", lw=2.0, mutation_scale=14))
            ax.text(-dx * 0.15 - 4, arrow_len * 1.05,
                    f"{ion.element}\n{ion.energy_eV:.0f} eV\nθ={ion.angle_deg:.0f}°",
                    color="#43A047", fontsize=9, va="bottom")

        ax.set_xlabel("Position latérale x (nm)", fontsize=11)
        ax.set_ylabel("Profondeur z (nm)", fontsize=11)
        target_name = cfg.target_layers[0].element if cfg.target_layers else "?"
        ax.set_title(f"Trajectoires BCA – {ion.element} ({ion.energy_eV:.0f} eV, {ion.angle_deg:.0f}°) → {target_name}", fontsize=12)
        ax.invert_yaxis(); ax.legend(fontsize=9, loc="lower right"); ax.grid(True, linestyle=":", alpha=0.4)
        self._canvas.draw()

        total     = n_implanted + n_backscattered if self._show_ion_traj.isChecked() else n_ions
        pct_back  = n_backscattered / total * 100 if total > 0 else 0
        pct_impl  = n_implanted    / total * 100 if total > 0 else 0
        mean_depth = float(np.mean(depths_implanted)) if depths_implanted else 0.0
        self._stat_implanted.setText(f"Implantés : {n_implanted} ({pct_impl:.0f}%)")
        self._stat_backscattered.setText(f"Rétro-diffusés : {n_backscattered} ({pct_back:.0f}%)")
        self._stat_sputtered.setText(f"Éjectés affichés : {n_atoms}")
        self._stat_mean_depth.setText(f"Prof. moy. implant. : {mean_depth:.1f} nm")

    def _save_figure(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter la figure", "", "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if path:
            self._canvas.fig.savefig(path, dpi=150, bbox_inches="tight")
