"""
Panneau de visualisation des rendements de pulvérisation.
Onglet « Rendements ».
"""

import os
import tempfile
import numpy as np
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QCheckBox, QFileDialog,
    QDoubleSpinBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QSplitter, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.simulation_config import SimulationConfig, ELEMENTS
from core.mock_simulator import mock_yield_vs_energy, mock_yield_vs_angle
from gui.param_bar import ParamBar


def _make_swoosh_svg(color: str) -> str:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 22 22">'
        f'<rect width="22" height="22" rx="5" fill="{color}"/>'
        '<path d="M4 13 Q9 6 18 5 Q12 10 10 16 Q8 14 4 13Z" fill="white" stroke="none"/>'
        '</svg>'
    )
    tmp = tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w")
    tmp.write(svg)
    tmp.close()
    return tmp.name


_COLORS = ["#1565C0", "#2E7D32", "#B71C1C", "#E65100", "#6A1B9A", "#00695C"]
_COMMON_IONS = ["Ar", "Xe", "Kr", "Ne", "N", "O", "He"]


class YieldCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(7, 4.5), tight_layout=True,
                          facecolor=matplotlib.rcParams.get("figure.facecolor", "#FFFFFF"))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(matplotlib.rcParams.get("axes.facecolor", "#FAFAFA"))
        super().__init__(self.fig)


class YieldPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config: SimulationConfig = SimulationConfig()
        # curseur interactif
        self._cursor_annot = None
        self._cursor_lines: list = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Barre de rappel ─────────────────────────────────────────
        self._param_bar = ParamBar()
        root.addWidget(self._param_bar)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(6)
        inner_layout.setContentsMargins(8, 6, 8, 8)

        splitter = QSplitter(Qt.Vertical)

        ctrl_widget = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_widget)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(8)

        mode_grp = QGroupBox("Mode d'affichage")
        mode_form = QFormLayout(mode_grp)
        mode_form.setSpacing(4)
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Y(E) – Rendement vs Énergie", "Y(θ) – Rendement vs Angle"])
        self._mode_combo.currentIndexChanged.connect(self._plot)
        mode_form.addRow("Mode :", self._mode_combo)
        self._log_x = QCheckBox("Axe X log");   self._log_x.setChecked(True);  self._log_x.toggled.connect(self._plot)
        self._show_grid = QCheckBox("Grille");   self._show_grid.setChecked(True); self._show_grid.toggled.connect(self._plot)
        flags_row = QHBoxLayout()
        flags_row.addWidget(self._log_x); flags_row.addWidget(self._show_grid); flags_row.addStretch()
        mode_form.addRow(flags_row)
        ctrl_layout.addWidget(mode_grp)

        range_grp = QGroupBox("Gamme d'énergie")
        range_form = QFormLayout(range_grp)
        range_form.setSpacing(4)
        self._e_min = QDoubleSpinBox(); self._e_min.setRange(1, 1e5); self._e_min.setValue(10);   self._e_min.setSuffix(" eV")
        self._e_max = QDoubleSpinBox(); self._e_max.setRange(10, 1e6); self._e_max.setValue(10000); self._e_max.setSuffix(" eV")
        range_form.addRow("E min :", self._e_min)
        range_form.addRow("E max :", self._e_max)
        ctrl_layout.addWidget(range_grp)

        cmp_grp = QGroupBox("Comparaison multi-ions")
        cmp_form = QFormLayout(cmp_grp)
        cmp_form.setSpacing(4)
        self._compare_check = QCheckBox("Activer la comparaison")
        self._compare_check.toggled.connect(self._plot)
        cmp_form.addRow(self._compare_check)
        self._ion_checks = {}
        self._swoosh_svgs: list[str] = []
        ions_row = QHBoxLayout(); ions_row.setSpacing(6)
        for i, ion in enumerate(_COMMON_IONS):
            color = _COLORS[i % len(_COLORS)]
            svg_path = _make_swoosh_svg(color)
            self._swoosh_svgs.append(svg_path)
            svg_url = svg_path.replace("\\", "/")
            cb = QCheckBox(ion)
            cb.setChecked(ion in ("Ar", "Xe"))
            cb.toggled.connect(self._plot)
            cb.setStyleSheet(f"""
                QCheckBox {{ spacing: 5px; color: #212121; font-weight: 500; }}
                QCheckBox::indicator {{ width: 22px; height: 22px; border-radius: 5px; border: 2px solid {color}; background: transparent; }}
                QCheckBox::indicator:unchecked:hover {{ background: rgba(0,0,0,0.06); }}
                QCheckBox::indicator:checked {{ image: url("{svg_url}"); border: none; }}
            """)
            self._ion_checks[ion] = cb
            ions_row.addWidget(cb)
        ions_row.addStretch()
        cmp_form.addRow("Ions :", ions_row)
        ctrl_layout.addWidget(cmp_grp)

        btn_col = QVBoxLayout()
        plot_btn = QPushButton("Tracer");               plot_btn.clicked.connect(self._plot)
        save_btn = QPushButton("Exporter figure");      save_btn.clicked.connect(self._save_figure)
        csv_btn  = QPushButton("Exporter données (.csv)"); csv_btn.clicked.connect(self._export_data)
        btn_col.addWidget(plot_btn); btn_col.addWidget(save_btn); btn_col.addWidget(csv_btn); btn_col.addStretch()
        ctrl_layout.addLayout(btn_col)

        splitter.addWidget(ctrl_widget)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(6)
        self._canvas = YieldCanvas()
        self._toolbar = NavigationToolbar(self._canvas, self)
        bottom_layout.addWidget(self._toolbar)
        bottom_layout.addWidget(self._canvas)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Ion", "Cible", "E seuil (eV)", "Y à E₀ (at/ion)", "Y max (at/ion)"])
        self._table.setMaximumHeight(130)
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        bottom_layout.addWidget(self._table)

        splitter.addWidget(bottom)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        inner_layout.addWidget(splitter)

        root.addWidget(inner)

        # ── Curseur interactif ───────────────────────────────────────
        self._canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self._canvas.mpl_connect("axes_leave_event",    self._on_axes_leave)

    # ------------------------------------------------------------------
    # Curseur interactif
    # ------------------------------------------------------------------

    def _on_mouse_move(self, event):
        ax = self._canvas.ax
        if event.inaxes != ax:
            return

        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return

        # Trouver la ligne la plus proche verticalement au x du curseur
        best_line  = None
        best_ydist = float("inf")
        best_y     = None

        for line in ax.lines:
            xdata, ydata = line.get_xdata(), line.get_ydata()
            if len(xdata) < 2:
                continue
            # interpolation
            try:
                y_interp = float(np.interp(x, xdata, ydata))
            except Exception:
                continue
            dist = abs(y_interp - y)
            if dist < best_ydist:
                best_ydist = dist
                best_line  = line
                best_y     = y_interp

        # Ne montrer le curseur que si on est assez proche d'une courbe
        if best_line is None or best_ydist > (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.08:
            self._hide_cursor()
            return

        color = best_line.get_color()
        label = best_line.get_label()

        # Lignes croisées
        for ln in self._cursor_lines:
            ln.remove()
        self._cursor_lines.clear()
        self._cursor_lines.append(
            ax.axvline(x, color=color, linewidth=0.8, linestyle=":", alpha=0.7)
        )
        self._cursor_lines.append(
            ax.axhline(best_y, color=color, linewidth=0.8, linestyle=":", alpha=0.7)
        )

        # Annotation
        mode = self._mode_combo.currentIndex()
        x_unit = "eV" if mode == 0 else "°"
        x_fmt  = f"{x:,.1f}" if mode == 0 else f"{x:.1f}"
        tip = f"{label}\n{x_fmt} {x_unit}\nY = {best_y:.4f} at/ion"

        if self._cursor_annot is None:
            self._cursor_annot = ax.annotate(
                "", xy=(x, best_y),
                xytext=(12, 12), textcoords="offset points",
                bbox=dict(boxstyle="round,pad=0.4", fc="#FFFFCC", ec=color, lw=1.2, alpha=0.92),
                fontsize=9,
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8),
            )
        self._cursor_annot.set_text(tip)
        self._cursor_annot.xy = (x, best_y)
        self._cursor_annot.set_visible(True)

        self._canvas.draw_idle()

    def _on_axes_leave(self, event):
        self._hide_cursor()

    def _hide_cursor(self):
        if self._cursor_annot is not None:
            self._cursor_annot.set_visible(False)
        for ln in self._cursor_lines:
            ln.remove()
        self._cursor_lines.clear()
        self._canvas.draw_idle()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def update_config(self, cfg: SimulationConfig):
        self.config = cfg
        self._param_bar.update_config(cfg)
        self._plot()

    def _plot(self):
        cfg = self.config
        ion = cfg.ion
        if not cfg.target_layers:
            return
        target = cfg.target_layers[0]

        # Réinitialiser le curseur à chaque nouveau tracé
        self._cursor_annot = None
        self._cursor_lines.clear()

        bg    = matplotlib.rcParams.get("figure.facecolor", "#FFFFFF")
        ax_bg = matplotlib.rcParams.get("axes.facecolor",   "#FAFAFA")
        self._canvas.fig.set_facecolor(bg)
        self._canvas.ax.set_facecolor(ax_bg)

        ax = self._canvas.ax
        ax.clear()
        self._table.setRowCount(0)

        mode    = self._mode_combo.currentIndex()
        compare = self._compare_check.isChecked()
        ions_to_plot = (
            [(n, ELEMENTS[n]["Z"], ELEMENTS[n]["mass"]) for n, cb in self._ion_checks.items() if cb.isChecked() and n in ELEMENTS]
            if compare else [(ion.element, ion.Z, ion.mass_amu)]
        )

        for idx, (ion_name, ion_Z, ion_mass) in enumerate(ions_to_plot):
            color = _COLORS[idx % len(_COLORS)]
            if mode == 0:
                energies = np.logspace(np.log10(self._e_min.value()), np.log10(self._e_max.value()), 400)
                yields   = mock_yield_vs_energy(ion_Z, ion_mass, target.Z, target.mass_amu, ion.angle_deg, energies)
                ax.plot(energies, yields, color=color, linewidth=2, label=f"{ion_name} → {target.element}")
                if not compare or ion_name == ion.element:
                    y_e = mock_yield_vs_energy(ion_Z, ion_mass, target.Z, target.mass_amu, ion.angle_deg, np.array([ion.energy_eV]))[0]
                    ax.axvline(ion.energy_eV, color=color, linestyle="--", alpha=0.5)
                    ax.scatter([ion.energy_eV], [y_e], color=color, zorder=5, s=60)
                e_th = 8.0 * target.Z * ion_Z / (target.Z + ion_Z)
                y_e0 = mock_yield_vs_energy(ion_Z, ion_mass, target.Z, target.mass_amu, ion.angle_deg, np.array([ion.energy_eV]))[0]
                self._add_table_row(ion_name, target.element, e_th, y_e0, float(np.nanmax(yields)))
            else:
                angles = np.linspace(0, 85, 86)
                yields  = mock_yield_vs_angle(ion_Z, ion_mass, target.Z, target.mass_amu, ion.energy_eV, angles)
                ax.plot(angles, yields, color=color, linewidth=2, label=f"{ion_name} → {target.element}")
                if not compare or ion_name == ion.element:
                    ax.axvline(ion.angle_deg, color=color, linestyle="--", alpha=0.5)
                y_a = mock_yield_vs_angle(ion_Z, ion_mass, target.Z, target.mass_amu, ion.energy_eV, np.array([ion.angle_deg]))[0]
                e_th = 8.0 * target.Z * ion_Z / (target.Z + ion_Z)
                self._add_table_row(ion_name, target.element, e_th, y_a, float(np.nanmax(yields)))

        if mode == 0:
            if self._log_x.isChecked():
                ax.set_xscale("log")
            ax.set_xlabel("Énergie de l'ion (eV)", fontsize=11)
            ax.set_ylabel("Rendement de pulvérisation (atomes/ion)", fontsize=11)
            ax.set_title(f"Rendement Y(E) – {'multi-ions' if compare else ion.element} → {target.element}  (θ = {ion.angle_deg:.0f}°)", fontsize=12)
        else:
            ax.set_xlabel("Angle d'incidence (°)", fontsize=11)
            ax.set_ylabel("Rendement de pulvérisation (atomes/ion)", fontsize=11)
            ax.set_title(f"Rendement Y(θ) – {'multi-ions' if compare else ion.element} → {target.element}  (E = {ion.energy_eV:.0f} eV)", fontsize=12)

        ax.legend(fontsize=10)
        ax.set_ylim(bottom=0)
        if self._show_grid.isChecked():
            ax.grid(True, linestyle="--", alpha=0.5)
        self._canvas.draw()

    def _add_table_row(self, ion, target, e_th, y_e0, y_max):
        row = self._table.rowCount()
        self._table.insertRow(row)
        for col, val in enumerate([ion, target, f"{e_th:.1f}", f"{y_e0:.4f}", f"{y_max:.4f}"]):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, col, item)
        self._table.resizeColumnsToContents()

    def _save_figure(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter la figure", "", "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if path:
            self._canvas.fig.savefig(path, dpi=150, bbox_inches="tight")

    def _export_data(self):
        cfg = self.config; ion = cfg.ion
        if not cfg.target_layers: return
        target = cfg.target_layers[0]
        path, _ = QFileDialog.getSaveFileName(self, "Exporter les données", "", "CSV (*.csv)")
        if not path: return
        if self._mode_combo.currentIndex() == 0:
            energies = np.logspace(np.log10(self._e_min.value()), np.log10(self._e_max.value()), 400)
            yields   = mock_yield_vs_energy(ion.Z, ion.mass_amu, target.Z, target.mass_amu, ion.angle_deg, energies)
            header   = f"# Y(E)  ion={ion.element}  target={target.element}  angle={ion.angle_deg}deg\nenergy_eV,yield_at_per_ion"
            np.savetxt(path, np.column_stack([energies, yields]), delimiter=",", header=header, comments="")
        else:
            angles = np.linspace(0, 85, 86)
            yields  = mock_yield_vs_angle(ion.Z, ion.mass_amu, target.Z, target.mass_amu, ion.energy_eV, angles)
            header  = f"# Y(θ)  ion={ion.element}  target={target.element}  energy={ion.energy_eV}eV\nangle_deg,yield_at_per_ion"
            np.savetxt(path, np.column_stack([angles, yields]), delimiter=",", header=header, comments="")
