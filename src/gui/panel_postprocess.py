"""
Panneau de post-traitement : distributions angulaire et énergétique.
Onglet « Post-traitement ».
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton,
    QCheckBox, QFileDialog, QFormLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from core.simulation_config import SimulationConfig
from core.mock_simulator import mock_angular_distribution, mock_energy_distribution


class PostCanvas(FigureCanvas):
    def __init__(self, polar=False):
        self.fig = Figure(figsize=(7, 4.5), tight_layout=True,
                          facecolor=matplotlib.rcParams.get("figure.facecolor", "#FFFFFF"))
        self.ax = self.fig.add_subplot(111, projection="polar" if polar else None)
        self.ax.set_facecolor(matplotlib.rcParams.get("axes.facecolor", "#FAFAFA"))
        super().__init__(self.fig)


class PostProcessPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = SimulationConfig()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_angular_tab(), "Distribution angulaire")
        self._tabs.addTab(self._build_energy_tab(),  "Distribution en énergie")
        self._tabs.addTab(self._build_combined_tab(), "Vue combinée")
        layout.addWidget(self._tabs)

    # ------------------------------------------------------------------
    # Distribution angulaire
    # ------------------------------------------------------------------

    def _build_angular_tab(self) -> QWidget:
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(6,6,6,6); layout.setSpacing(6)

        ctrl = QGroupBox("Paramètres – Distribution angulaire")
        form = QFormLayout(ctrl); form.setSpacing(4)
        self._ang_bins = QSpinBox(); self._ang_bins.setRange(18, 360); self._ang_bins.setValue(90)
        form.addRow("Nombre de bins :", self._ang_bins)
        flags_row = QHBoxLayout()
        self._ang_polar     = QCheckBox("Vue polaire");            self._ang_polar.setChecked(True)
        self._ang_normalize = QCheckBox("Normaliser (max = 1)");   self._ang_normalize.setChecked(True)
        self._ang_polar.toggled.connect(self._rebuild_angular_canvas)
        flags_row.addWidget(self._ang_polar); flags_row.addWidget(self._ang_normalize); flags_row.addStretch()
        form.addRow(flags_row)
        btn_row = QHBoxLayout()
        btn_plot = QPushButton("Tracer");          btn_plot.clicked.connect(self._plot_angular)
        btn_save = QPushButton("Exporter figure"); btn_save.clicked.connect(lambda: self._save_fig(self._ang_canvas))
        btn_csv  = QPushButton("Exporter CSV");    btn_csv.clicked.connect(self._export_angular_data)
        btn_row.addWidget(btn_plot); btn_row.addWidget(btn_csv); btn_row.addStretch(); btn_row.addWidget(btn_save)
        form.addRow(btn_row)
        layout.addWidget(ctrl)

        self._ang_canvas_container = QVBoxLayout()
        self._ang_canvas  = PostCanvas(polar=True)
        self._ang_toolbar = NavigationToolbar(self._ang_canvas, w)
        self._ang_canvas_container.addWidget(self._ang_toolbar)
        self._ang_canvas_container.addWidget(self._ang_canvas)
        layout.addLayout(self._ang_canvas_container)

        self._ang_table = QTableWidget(3, 2)
        self._ang_table.setHorizontalHeaderLabels(["Grandeur", "Valeur"])
        self._ang_table.setMaximumHeight(110)
        self._ang_table.horizontalHeader().setStretchLastSection(True)
        self._ang_table.verticalHeader().setVisible(False)
        layout.addWidget(self._ang_table)
        return w

    def _rebuild_angular_canvas(self):
        polar = self._ang_polar.isChecked()
        old = self._ang_canvas
        self._ang_canvas = PostCanvas(polar=polar)
        self._ang_toolbar.setParent(None)
        pw = old.parentWidget(); old.setParent(None)
        self._ang_toolbar = NavigationToolbar(self._ang_canvas, pw)
        self._ang_canvas_container.addWidget(self._ang_toolbar)
        self._ang_canvas_container.addWidget(self._ang_canvas)
        self._plot_angular()

    def _plot_angular(self):
        cfg = self.config
        angles, dist = mock_angular_distribution(self._ang_bins.value(), cfg.ion.angle_deg)
        if self._ang_normalize.isChecked():
            dist = dist / (dist.max() + 1e-12)

        bg    = matplotlib.rcParams.get("figure.facecolor", "#FFFFFF")
        ax_bg = matplotlib.rcParams.get("axes.facecolor",   "#FAFAFA")
        self._ang_canvas.fig.set_facecolor(bg)

        ax = self._ang_canvas.ax; ax.clear()
        if self._ang_polar.isChecked():
            theta = np.radians(angles)
            ax.plot(theta, dist, color="#1565C0", linewidth=2)
            ax.fill(theta, dist, alpha=0.15, color="#1565C0")
            ax.set_title("Distribution angulaire polaire des atomes pulvérisés", pad=18, fontsize=12)
            ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
        else:
            self._ang_canvas.ax.set_facecolor(ax_bg)
            w = (angles[1] - angles[0]) * 0.9 if len(angles) > 1 else 2.0
            ax.bar(angles, dist, width=w, color="#1565C0", alpha=0.75, label="Distribution angulaire")
            ax.set_xlabel("Angle d'émission (°)", fontsize=11)
            ax.set_ylabel("Intensité" + (" normalisée" if self._ang_normalize.isChecked() else ""), fontsize=11)
            target = cfg.target_layers[0].element if cfg.target_layers else "?"
            ax.set_title(f"Distribution angulaire – {cfg.ion.element} → {target}", fontsize=12)
            ax.set_xlim(0, 180); ax.legend(fontsize=10); ax.grid(True, linestyle="--", alpha=0.5)

        self._ang_canvas.draw()
        peak_angle = float(angles[np.argmax(dist)])
        mean_angle = float(np.average(angles, weights=dist + 1e-12))
        std_angle  = float(np.sqrt(np.average((angles - mean_angle) ** 2, weights=dist + 1e-12)))
        self._fill_table(self._ang_table, [
            ("Angle du pic (°)", f"{peak_angle:.1f}"),
            ("Angle moyen (°)",  f"{mean_angle:.1f}"),
            ("Écart-type angulaire (°)", f"{std_angle:.1f}"),
        ])

    def _export_angular_data(self):
        cfg = self.config
        angles, dist = mock_angular_distribution(self._ang_bins.value(), cfg.ion.angle_deg)
        path, _ = QFileDialog.getSaveFileName(self, "Exporter distribution angulaire", "", "CSV (*.csv)")
        if path:
            header = (f"# Distribution angulaire\n# ion={cfg.ion.element}  E={cfg.ion.energy_eV}eV  "
                      f"theta_inc={cfg.ion.angle_deg}deg\nangle_deg,intensity")
            np.savetxt(path, np.column_stack([angles, dist]), delimiter=",", header=header, comments="")

    # ------------------------------------------------------------------
    # Distribution en énergie
    # ------------------------------------------------------------------

    def _build_energy_tab(self) -> QWidget:
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(6,6,6,6); layout.setSpacing(6)

        ctrl = QGroupBox("Paramètres – Distribution en énergie (Thompson)")
        form = QFormLayout(ctrl); form.setSpacing(4)
        self._en_bins = QSpinBox(); self._en_bins.setRange(10, 1000); self._en_bins.setValue(100)
        form.addRow("Nombre de bins :", self._en_bins)
        self._surface_binding = QDoubleSpinBox()
        self._surface_binding.setRange(0.1, 50.0); self._surface_binding.setValue(6.83); self._surface_binding.setSuffix(" eV")
        self._surface_binding.setToolTip("Énergie de liaison de surface Es (Mo ≈ 6.83 eV, W ≈ 8.68 eV, Cu ≈ 3.49 eV)")
        form.addRow("Énergie de liaison Es :", self._surface_binding)
        flags_row = QHBoxLayout()
        self._en_log_x         = QCheckBox("Axe X log")
        self._en_normalize     = QCheckBox("Normaliser (max = 1)");          self._en_normalize.setChecked(True)
        self._en_show_thompson = QCheckBox("Courbe Thompson analytique");    self._en_show_thompson.setChecked(True)
        flags_row.addWidget(self._en_log_x); flags_row.addWidget(self._en_normalize); flags_row.addWidget(self._en_show_thompson); flags_row.addStretch()
        form.addRow(flags_row)
        btn_row = QHBoxLayout()
        btn_plot = QPushButton("Tracer");          btn_plot.clicked.connect(self._plot_energy)
        btn_save = QPushButton("Exporter figure"); btn_save.clicked.connect(lambda: self._save_fig(self._en_canvas))
        btn_csv  = QPushButton("Exporter CSV");    btn_csv.clicked.connect(self._export_energy_data)
        btn_row.addWidget(btn_plot); btn_row.addWidget(btn_csv); btn_row.addStretch(); btn_row.addWidget(btn_save)
        form.addRow(btn_row)
        layout.addWidget(ctrl)

        self._en_canvas  = PostCanvas()
        self._en_toolbar = NavigationToolbar(self._en_canvas, w)
        layout.addWidget(self._en_toolbar); layout.addWidget(self._en_canvas)

        self._en_table = QTableWidget(5, 2)
        self._en_table.setHorizontalHeaderLabels(["Grandeur", "Valeur"])
        self._en_table.setMaximumHeight(155)
        self._en_table.horizontalHeader().setStretchLastSection(True)
        self._en_table.verticalHeader().setVisible(False)
        layout.addWidget(self._en_table)
        return w

    def _plot_energy(self):
        cfg = self.config; Es = self._surface_binding.value()
        energies, dist = mock_energy_distribution(self._en_bins.value(), Es, cfg.ion.energy_eV)
        if self._en_normalize.isChecked():
            dist = dist / (dist.max() + 1e-12)

        bg    = matplotlib.rcParams.get("figure.facecolor", "#FFFFFF")
        ax_bg = matplotlib.rcParams.get("axes.facecolor",   "#FAFAFA")
        self._en_canvas.fig.set_facecolor(bg); self._en_canvas.ax.set_facecolor(ax_bg)

        ax = self._en_canvas.ax; ax.clear()
        ax.plot(energies, dist, color="#2E7D32", linewidth=2, label="Distribution (BCA mock)")
        ax.fill_between(energies, dist, alpha=0.12, color="#2E7D32")
        peak_idx = np.argmax(dist)
        ax.axvline(energies[peak_idx], color="#E53935", linestyle="--", alpha=0.8, label=f"Pic : {energies[peak_idx]:.2f} eV")
        ax.axvline(Es / 2, color="#FF6F00", linestyle=":", alpha=0.8, label=f"Es/2 = {Es/2:.2f} eV  (Thompson)")
        if self._en_show_thompson.isChecked():
            E_th = np.linspace(energies[0], energies[-1], 500)
            f_th = E_th / (E_th + Es) ** 3
            if self._en_normalize.isChecked():
                f_th = f_th / (f_th.max() + 1e-12)
            ax.plot(E_th, f_th, color="#7B1FA2", linewidth=1.5, linestyle="--", alpha=0.8, label="Thompson analytique")
        if self._en_log_x.isChecked():
            ax.set_xscale("log")
        ax.set_xlabel("Énergie des atomes pulvérisés (eV)", fontsize=11)
        ax.set_ylabel("Intensité" + (" normalisée" if self._en_normalize.isChecked() else ""), fontsize=11)
        target = cfg.target_layers[0].element if cfg.target_layers else "?"
        ax.set_title(f"Distribution en énergie (Thompson) – {cfg.ion.element} → {target}  Es = {Es:.2f} eV", fontsize=12)
        ax.legend(fontsize=10); ax.grid(True, linestyle="--", alpha=0.5)
        self._en_canvas.draw()

        mean_E = float(np.average(energies, weights=dist + 1e-12))
        std_E  = float(np.sqrt(np.average((energies - mean_E) ** 2, weights=dist + 1e-12)))
        E_half_max = energies[np.argmin(np.abs(dist - 0.5))] if dist.max() > 0.5 else float("nan")
        self._fill_table(self._en_table, [
            ("Énergie du pic (eV)",  f"{energies[peak_idx]:.3f}"),
            ("Énergie moyenne (eV)", f"{mean_E:.3f}"),
            ("Écart-type (eV)",      f"{std_E:.3f}"),
            ("Es/2 – Thompson (eV)", f"{Es/2:.3f}"),
            ("E à mi-hauteur (eV)",  f"{E_half_max:.3f}" if not np.isnan(E_half_max) else "–"),
        ])

    def _export_energy_data(self):
        cfg = self.config; Es = self._surface_binding.value()
        energies, dist = mock_energy_distribution(self._en_bins.value(), Es, cfg.ion.energy_eV)
        path, _ = QFileDialog.getSaveFileName(self, "Exporter distribution en énergie", "", "CSV (*.csv)")
        if path:
            header = (f"# Distribution en énergie (Thompson)\n# ion={cfg.ion.element}  "
                      f"E_ion={cfg.ion.energy_eV}eV  Es={Es}eV  target={cfg.target_layers[0].element if cfg.target_layers else '?'}\n"
                      "energy_eV,intensity")
            np.savetxt(path, np.column_stack([energies, dist]), delimiter=",", header=header, comments="")

    # ------------------------------------------------------------------
    # Vue combinée
    # ------------------------------------------------------------------

    def _build_combined_tab(self) -> QWidget:
        w = QWidget(); layout = QVBoxLayout(w); layout.setContentsMargins(6,6,6,6); layout.setSpacing(6)
        ctrl_row = QHBoxLayout()
        btn = QPushButton("Mettre à jour"); btn.clicked.connect(self._plot_combined)
        btn_save = QPushButton("Exporter figure"); btn_save.clicked.connect(lambda: self._save_fig(self._comb_canvas))
        ctrl_row.addWidget(btn); ctrl_row.addStretch(); ctrl_row.addWidget(btn_save)
        layout.addLayout(ctrl_row)

        comb_fig = Figure(figsize=(10, 4.5), tight_layout=True,
                          facecolor=matplotlib.rcParams.get("figure.facecolor", "#FFFFFF"))
        self._comb_axes = comb_fig.subplots(1, 2)
        for ax in self._comb_axes:
            ax.set_facecolor(matplotlib.rcParams.get("axes.facecolor", "#FAFAFA"))
        self._comb_canvas  = FigureCanvas(comb_fig)
        self._comb_toolbar = NavigationToolbar(self._comb_canvas, w)
        layout.addWidget(self._comb_toolbar); layout.addWidget(self._comb_canvas)

        note = QLabel("Gauche : distribution angulaire des atomes éjectés  |  Droite : distribution en énergie (loi de Thompson)")
        note.setStyleSheet("color: #757575; font-size: 10px; background: #F5F5F5; border-radius: 4px; padding: 4px 8px;")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)
        return w

    def _plot_combined(self):
        cfg = self.config
        Es = self._surface_binding.value() if hasattr(self, "_surface_binding") else 6.83
        angles, ang_dist = mock_angular_distribution(90, cfg.ion.angle_deg)
        energies, en_dist = mock_energy_distribution(100, Es, cfg.ion.energy_eV)
        ang_dist = ang_dist / (ang_dist.max() + 1e-12)
        en_dist  = en_dist  / (en_dist.max()  + 1e-12)

        bg    = matplotlib.rcParams.get("figure.facecolor", "#FFFFFF")
        ax_bg = matplotlib.rcParams.get("axes.facecolor",   "#FAFAFA")
        self._comb_canvas.figure.set_facecolor(bg)
        ax1, ax2 = self._comb_axes
        ax1.clear(); ax2.clear()
        ax1.set_facecolor(ax_bg); ax2.set_facecolor(ax_bg)

        w = (angles[1] - angles[0]) * 0.9 if len(angles) > 1 else 2.0
        ax1.bar(angles, ang_dist, width=w, color="#1565C0", alpha=0.75)
        ax1.set_xlabel("Angle d'émission (°)", fontsize=10)
        ax1.set_ylabel("Intensité normalisée", fontsize=10)
        ax1.set_title("Distribution angulaire", fontsize=11)
        ax1.set_xlim(0, 180); ax1.grid(True, linestyle="--", alpha=0.5)

        ax2.plot(energies, en_dist, color="#2E7D32", linewidth=2)
        ax2.fill_between(energies, en_dist, alpha=0.12, color="#2E7D32")
        peak_idx = np.argmax(en_dist)
        ax2.axvline(energies[peak_idx], color="#E53935", linestyle="--", alpha=0.7, label=f"Pic : {energies[peak_idx]:.2f} eV")
        ax2.set_xlabel("Énergie (eV)", fontsize=10)
        ax2.set_ylabel("Intensité normalisée", fontsize=10)
        ax2.set_title("Distribution en énergie (Thompson)", fontsize=11)
        ax2.legend(fontsize=9); ax2.grid(True, linestyle="--", alpha=0.5)

        target = cfg.target_layers[0].element if cfg.target_layers else "?"
        self._comb_canvas.figure.suptitle(
            f"{cfg.ion.element} ({cfg.ion.energy_eV:.0f} eV, {cfg.ion.angle_deg:.0f}°) → {target}   |   Es = {Es:.2f} eV",
            fontsize=12, y=1.02
        )
        self._comb_canvas.draw()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def update_config(self, cfg: SimulationConfig):
        self.config = cfg
        self._plot_angular(); self._plot_energy(); self._plot_combined()

    def _fill_table(self, table: QTableWidget, rows: list):
        for i, (k, v) in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(k))
            vi = QTableWidgetItem(v); vi.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, vi)
        table.resizeColumnsToContents()

    def _save_fig(self, canvas: FigureCanvas):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter la figure", "", "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if path:
            canvas.figure.savefig(path, dpi=150, bbox_inches="tight")
