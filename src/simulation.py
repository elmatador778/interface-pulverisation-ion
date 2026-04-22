"""
Panneau d'exécution de la simulation et console de logs.
Onglet « Exécution ».
"""

import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QFileDialog, QProgressBar, QMessageBox, QFormLayout,
    QSplitter, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

from parametres_sim import SimulationConfig


# ---------------------------------------------------------------------------
# Thread de simulation réelle
# ---------------------------------------------------------------------------

class SimulationThread(QThread):
    log_line     = pyqtSignal(str)
    progress     = pyqtSignal(int)
    finished_ok  = pyqtSignal()
    finished_err = pyqtSignal(str)

    def __init__(self, cmd: list, cwd: str):
        super().__init__()
        self.cmd = cmd
        self.cwd = cwd
        self._abort = False

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd, cwd=self.cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                if self._abort:
                    proc.terminate()
                    self.finished_err.emit("Simulation annulée par l'utilisateur.")
                    return
                self.log_line.emit(line.rstrip())
                if "Progress:" in line:
                    try:
                        pct = int(line.split("Progress:")[1].strip().replace("%", ""))
                        self.progress.emit(pct)
                    except Exception:
                        pass
            proc.wait()
            if proc.returncode == 0:
                self.finished_ok.emit()
            else:
                self.finished_err.emit(f"Code de retour : {proc.returncode}.")
        except FileNotFoundError:
            self.finished_err.emit("Exécutable CSiPI introuvable. Vérifiez le chemin.")
        except Exception as e:
            self.finished_err.emit(str(e))

    def abort(self):
        self._abort = True


# ---------------------------------------------------------------------------
# Thread de démonstration (mock)
# ---------------------------------------------------------------------------

class DemoSimThread(QThread):
    log_line     = pyqtSignal(str)
    progress     = pyqtSignal(int)
    finished_ok  = pyqtSignal()
    finished_err = pyqtSignal(str)

    def __init__(self, cfg: SimulationConfig):
        super().__init__()
        self.cfg = cfg
        self._abort = False

    def run(self):
        import numpy as np
        cfg = self.cfg
        self.log_line.emit("=" * 62)
        self.log_line.emit("  CSiPI – Code de Simulation de la Pulvérisation Ionique")
        self.log_line.emit("  ONERA / DPHY-CSE  –  Mode démonstration (mock BCA)")
        self.log_line.emit("=" * 62)
        self.log_line.emit("")
        self.log_line.emit(f"  Ion        : {cfg.ion.element}  Z={cfg.ion.Z}  M={cfg.ion.mass_amu:.3f} amu")
        self.log_line.emit(f"  Énergie    : {cfg.ion.energy_eV:.1f} eV")
        self.log_line.emit(f"  Angle      : {cfg.ion.angle_deg:.1f}°")
        self.log_line.emit(f"  Nb ions    : {cfg.ion.num_ions:,}")
        self.log_line.emit(f"  Cible      : {', '.join(l.element for l in cfg.target_layers)}")
        self.log_line.emit(f"  Potentiel  : {cfg.physics.potential}")
        self.log_line.emit(f"  Reculs     : {'oui' if cfg.physics.track_recoils else 'non'}")
        self.log_line.emit(f"  Prof. max  : {cfg.physics.max_depth_nm:.0f} nm")
        self.log_line.emit("")
        self.log_line.emit("  Initialisation des tables de potentiel...")
        self.msleep(250)
        self.log_line.emit("  Initialisation du générateur Monte-Carlo (BCA)...")
        self.msleep(200)
        self.log_line.emit("  Démarrage de la simulation...")
        self.log_line.emit("")
        self.log_line.emit(f"{'Ion':>10}  {'Fait':>10}  {'%':>5}  {'Éjectés':>9}  {'Y (at/ion)':>12}")
        self.log_line.emit("─" * 55)

        n = cfg.ion.num_ions
        batch = max(1, n // 20)
        sputtered = 0

        for i in range(0, n, batch):
            if self._abort:
                self.finished_err.emit("Simulation annulée.")
                return
            done = min(i + batch, n)
            pct  = int(done / n * 100)
            ejected  = int(np.random.poisson(0.35 * batch / max(1, batch)))
            sputtered += ejected
            total_yield = sputtered / max(1, done)
            self.log_line.emit(
                f"  {cfg.ion.element:>6}  {done:>10,}  {pct:>4}%  {sputtered:>9,}  {total_yield:>12.5f}"
            )
            self.progress.emit(pct)
            self.msleep(110)

        self.log_line.emit("")
        self.log_line.emit("═" * 62)
        self.log_line.emit("  RÉSULTATS")
        self.log_line.emit("═" * 62)
        total_yield = sputtered / max(1, n)
        backscatter = np.random.uniform(0.02, 0.15)
        mean_depth  = np.random.uniform(5, 50)
        self.log_line.emit(f"  Rendement total              : {total_yield:.5f} at/ion")
        self.log_line.emit(f"  Atomes pulvérisés totaux     : {sputtered:,}")
        self.log_line.emit(f"  Taux de rétro-diffusion      : {backscatter:.4f}")
        self.log_line.emit(f"  Profondeur moyenne implant.  : {mean_depth:.2f} nm")
        self.log_line.emit("")
        self.log_line.emit("  Fichiers de sortie générés :")
        prefix = cfg.output.output_prefix
        if cfg.output.save_yield:                  self.log_line.emit(f"    → {prefix}_yield.dat")
        if cfg.output.save_angular_distribution:   self.log_line.emit(f"    → {prefix}_angular.dat")
        if cfg.output.save_energy_distribution:    self.log_line.emit(f"    → {prefix}_energy.dat")
        if cfg.output.save_trajectories:           self.log_line.emit(f"    → {prefix}_trajectories.dat")
        self.log_line.emit("")
        self.log_line.emit("  Simulation terminée avec succès.")
        self.progress.emit(100)
        self.finished_ok.emit()

    def abort(self):
        self._abort = True


# ---------------------------------------------------------------------------
# Panneau d'exécution
# ---------------------------------------------------------------------------

class RunnerPanel(QWidget):
    simulation_done = pyqtSignal(SimulationConfig)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = SimulationConfig()
        self._thread = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── Ligne exécutable ────────────────────────────────────────
        exe_grp = QGroupBox("Exécutable CSiPI")
        exe_form = QFormLayout(exe_grp)
        exe_row = QHBoxLayout()
        self._exe_path = QLineEdit()
        self._exe_path.setPlaceholderText("Laisser vide pour utiliser le mode démonstration (mock)")
        exe_btn = QPushButton("…")
        exe_btn.setFixedWidth(32)
        exe_btn.clicked.connect(self._choose_exe)
        exe_row.addWidget(self._exe_path)
        exe_row.addWidget(exe_btn)
        exe_form.addRow("Chemin :", exe_row)

        export_in_btn = QPushButton("Exporter fichier .in")
        export_in_btn.setToolTip("Génère le fichier d'entrée CSiPI sans lancer la simulation")
        export_in_btn.clicked.connect(self._export_input_file)
        exe_form.addRow("", export_in_btn)

        layout.addWidget(exe_grp)

        # ── Résumé de configuration ─────────────────────────────────
        summary_grp = QGroupBox("Résumé de la simulation à lancer")
        summary_layout = QHBoxLayout(summary_grp)

        ion_frame = self._make_summary_frame("Ion")
        self._lbl_ion    = QLabel()
        self._lbl_energy = QLabel()
        self._lbl_angle  = QLabel()
        self._lbl_nions  = QLabel()
        for k, v in [("Élément", self._lbl_ion), ("Énergie", self._lbl_energy),
                     ("Angle", self._lbl_angle), ("Nb ions", self._lbl_nions)]:
            ion_frame.layout().addRow(f"{k} :", v)
        summary_layout.addWidget(ion_frame)

        tgt_frame = self._make_summary_frame("Cible")
        self._lbl_target  = QLabel()
        self._lbl_pot     = QLabel()
        self._lbl_binding = QLabel()
        self._lbl_depth   = QLabel()
        for k, v in [("Éléments", self._lbl_target), ("Potentiel", self._lbl_pot),
                     ("Énergie surf.", self._lbl_binding), ("Prof. max", self._lbl_depth)]:
            tgt_frame.layout().addRow(f"{k} :", v)
        summary_layout.addWidget(tgt_frame)

        out_frame = self._make_summary_frame("Sorties")
        self._lbl_outdir = QLabel(); self._lbl_outdir.setWordWrap(True)
        self._lbl_prefix = QLabel()
        self._lbl_files  = QLabel(); self._lbl_files.setWordWrap(True)
        for k, v in [("Dossier", self._lbl_outdir), ("Préfixe", self._lbl_prefix), ("Fichiers", self._lbl_files)]:
            out_frame.layout().addRow(f"{k} :", v)
        summary_layout.addWidget(out_frame)

        layout.addWidget(summary_grp)
        self._refresh_summary()

        # ── Boutons Run / Annuler ───────────────────────────────────
        btn_row = QHBoxLayout()
        self._run_btn = QPushButton("▶  Lancer la simulation")
        self._run_btn.setStyleSheet(
            "QPushButton { background: #1565C0; color: white; font-weight: bold; "
            "border-radius: 8px; padding: 8px 22px; font-size: 13px; }"
            "QPushButton:hover { background: #1976D2; }"
            "QPushButton:disabled { background: #90A4AE; color: #CFD8DC; }"
        )
        self._run_btn.clicked.connect(self._run)

        self._abort_btn = QPushButton("■  Annuler")
        self._abort_btn.setEnabled(False)
        self._abort_btn.setStyleSheet(
            "QPushButton { background: #B71C1C; color: white; font-weight: bold; "
            "border-radius: 8px; padding: 8px 22px; font-size: 13px; }"
            "QPushButton:hover { background: #C62828; }"
            "QPushButton:disabled { background: #90A4AE; color: #CFD8DC; }"
        )
        self._abort_btn.clicked.connect(self._abort)

        self._clear_btn    = QPushButton("Effacer");          self._clear_btn.clicked.connect(self._clear_console)
        self._save_log_btn = QPushButton("Sauvegarder log");  self._save_log_btn.clicked.connect(self._save_log)

        btn_row.addWidget(self._run_btn)
        btn_row.addWidget(self._abort_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._clear_btn)
        btn_row.addWidget(self._save_log_btn)
        layout.addLayout(btn_row)

        # ── Barre de progression ────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        # ── Console ─────────────────────────────────────────────────
        self._console = QTextEdit()
        self._console.setReadOnly(True)
        self._console.setFont(QFont("Monospace", 9))
        self._console.setStyleSheet(
            "background: #1E1E1E; color: #D4D4D4; border-radius: 8px; padding: 6px;"
        )
        layout.addWidget(self._console)

    def _make_summary_frame(self, title: str) -> QGroupBox:
        grp = QGroupBox(title)
        grp.setLayout(QFormLayout())
        grp.layout().setSpacing(3)
        return grp

    # ------------------------------------------------------------------
    # Slots publics
    # ------------------------------------------------------------------

    def update_config(self, cfg: SimulationConfig):
        self.config = cfg
        self._refresh_summary()

    def _refresh_summary(self):
        cfg = self.config
        self._lbl_ion.setText(f"<b>{cfg.ion.element}</b>  (Z={cfg.ion.Z}, M={cfg.ion.mass_amu:.3f} u)")
        self._lbl_energy.setText(f"{cfg.ion.energy_eV:.1f} eV")
        self._lbl_angle.setText(f"{cfg.ion.angle_deg:.1f}°")
        self._lbl_nions.setText(f"{cfg.ion.num_ions:,}")
        targets = ", ".join(f"{l.element} ({l.fraction:.0%})" for l in cfg.target_layers)
        self._lbl_target.setText(targets)
        self._lbl_pot.setText(cfg.physics.potential)
        self._lbl_binding.setText(cfg.physics.surface_binding_model)
        self._lbl_depth.setText(f"{cfg.physics.max_depth_nm:.0f} nm")
        self._lbl_outdir.setText(cfg.output.output_directory)
        self._lbl_prefix.setText(cfg.output.output_prefix)
        saved = []
        if cfg.output.save_yield:                  saved.append("rendement")
        if cfg.output.save_angular_distribution:   saved.append("angulaire")
        if cfg.output.save_energy_distribution:    saved.append("énergie")
        if cfg.output.save_trajectories:           saved.append("trajectoires")
        self._lbl_files.setText(", ".join(saved) if saved else "aucun")

    # ------------------------------------------------------------------
    # Slots internes
    # ------------------------------------------------------------------

    def _choose_exe(self):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner l'exécutable CSiPI")
        if path:
            self._exe_path.setText(path)

    def _export_input_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le fichier d'entrée CSiPI", "", "Fichier d'entrée (*.in);;Tous (*.*)"
        )
        if path:
            with open(path, "w") as f:
                f.write(self.config.to_csipI_input())
            QMessageBox.information(self, "Succès", f"Fichier .in exporté :\n{path}")

    def _run(self):
        self._console.clear()
        self._progress.setValue(0)
        self._run_btn.setEnabled(False)
        self._abort_btn.setEnabled(True)

        exe = self._exe_path.text().strip()
        if exe and os.path.isfile(exe):
            out_dir = self.config.output.output_directory
            os.makedirs(out_dir, exist_ok=True)
            input_path = os.path.join(out_dir, "csipI_input.in")
            with open(input_path, "w") as f:
                f.write(self.config.to_csipI_input())
            self._thread = SimulationThread([exe, input_path], out_dir)
        else:
            self._log_colored(
                "[MODE DÉMO]  Aucun exécutable CSiPI détecté – simulateur mock activé.\n", "#FFA726"
            )
            self._thread = DemoSimThread(self.config)

        self._thread.log_line.connect(self._append_log)
        self._thread.progress.connect(self._progress.setValue)
        self._thread.finished_ok.connect(self._on_success)
        self._thread.finished_err.connect(self._on_error)
        self._thread.start()

    def _abort(self):
        if self._thread:
            self._thread.abort()
        self._abort_btn.setEnabled(False)

    def _on_success(self):
        self._run_btn.setEnabled(True)
        self._abort_btn.setEnabled(False)
        self._log_colored("✓  Simulation terminée avec succès.", "#66BB6A")
        self.simulation_done.emit(self.config)

    def _on_error(self, msg: str):
        self._run_btn.setEnabled(True)
        self._abort_btn.setEnabled(False)
        self._log_colored(f"✗  Erreur : {msg}", "#EF5350")

    def _append_log(self, line: str):
        self._console.moveCursor(QTextCursor.End)
        self._console.insertPlainText(line + "\n")
        self._console.moveCursor(QTextCursor.End)

    def _log_colored(self, line: str, color: str):
        self._console.moveCursor(QTextCursor.End)
        self._console.insertHtml(
            f'<span style="color:{color}; font-family:monospace;">{line}</span><br/>'
        )
        self._console.moveCursor(QTextCursor.End)

    def _clear_console(self):
        self._console.clear()
        self._progress.setValue(0)

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le log", "", "Texte (*.txt);;Tous (*.*)")
        if path:
            with open(path, "w") as f:
                f.write(self._console.toPlainText())
