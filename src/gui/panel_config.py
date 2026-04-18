"""
Panneau de configuration des paramètres de simulation CSiPI.
Onglet « Configuration ».
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QPushButton, QFileDialog, QScrollArea,
    QFormLayout, QSizePolicy, QFrame, QToolButton, QMessageBox,
    QSplitter, QTextEdit, QTabWidget, QApplication,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette

from core.simulation_config import (
    SimulationConfig, IonParameters, TargetLayer,
    PhysicsParameters, OutputOptions,
    ELEMENTS, INTERATOMIC_POTENTIALS, SURFACE_BINDING_MODELS,
)


class TargetLayerWidget(QFrame):
    removed = pyqtSignal(object)
    changed = pyqtSignal()

    def __init__(self, layer: TargetLayer, index: int, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self._idx_label = QLabel(f"<b>Couche {index + 1}</b>")
        self._idx_label.setFixedWidth(70)
        layout.addWidget(self._idx_label)

        layout.addWidget(QLabel("Élément:"))
        self.elem_combo = QComboBox()
        self.elem_combo.addItems(sorted(ELEMENTS.keys()))
        self.elem_combo.setCurrentText(layer.element)
        self.elem_combo.setFixedWidth(70)
        self.elem_combo.currentTextChanged.connect(self._update_layer)
        layout.addWidget(self.elem_combo)

        layout.addWidget(QLabel("Fraction:"))
        self.frac_spin = QDoubleSpinBox()
        self.frac_spin.setRange(0.01, 1.0)
        self.frac_spin.setSingleStep(0.05)
        self.frac_spin.setValue(layer.fraction)
        self.frac_spin.setFixedWidth(75)
        self.frac_spin.valueChanged.connect(self._update_layer)
        layout.addWidget(self.frac_spin)

        self.bulk_check = QCheckBox("Bulk ∞")
        self.bulk_check.setChecked(layer.bulk)
        self.bulk_check.toggled.connect(self._toggle_bulk)
        layout.addWidget(self.bulk_check)

        layout.addWidget(QLabel("Épaisseur:"))
        self.thick_spin = QDoubleSpinBox()
        self.thick_spin.setRange(0.1, 10000.0)
        self.thick_spin.setSuffix(" nm")
        self.thick_spin.setValue(layer.thickness_nm)
        self.thick_spin.setEnabled(not layer.bulk)
        self.thick_spin.setFixedWidth(100)
        self.thick_spin.valueChanged.connect(self._update_layer)
        layout.addWidget(self.thick_spin)

        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "color: #1565C0; font-size: 10px; background: #E3F2FD; "
            "border-radius: 6px; padding: 2px 6px;"
        )
        self._refresh_info()
        layout.addWidget(self.info_label)

        layout.addStretch()

        remove_btn = QToolButton()
        remove_btn.setText("✕")
        remove_btn.setToolTip("Supprimer cette couche")
        remove_btn.setStyleSheet(
            "QToolButton { color: #B71C1C; border: 1px solid #EF9A9A; "
            "border-radius: 6px; padding: 2px 6px; background: #FFEBEE; }"
            "QToolButton:hover { background: #FFCDD2; }"
        )
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        layout.addWidget(remove_btn)

    def set_index(self, i: int):
        self._idx_label.setText(f"<b>Couche {i + 1}</b>")

    def _toggle_bulk(self, checked: bool):
        self.thick_spin.setEnabled(not checked)
        self.layer.bulk = checked
        self.changed.emit()

    def _update_layer(self):
        self.layer.element = self.elem_combo.currentText()
        self.layer.fraction = self.frac_spin.value()
        self.layer.thickness_nm = self.thick_spin.value()
        self._refresh_info()
        self.changed.emit()

    def _refresh_info(self):
        el = self.elem_combo.currentText()
        info = ELEMENTS.get(el, {})
        self.info_label.setText(f"Z={info.get('Z','?')}  M={info.get('mass','?')} u")


class ConfigPanel(QWidget):
    config_changed = pyqtSignal(SimulationConfig)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = SimulationConfig()
        self._layer_widgets: list[TargetLayerWidget] = []
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(400)
        self._preview_timer.timeout.connect(self._refresh_preview)
        self._build_ui()
        self._load_config_to_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 4, 8)
        left_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        self._main_layout = QVBoxLayout(container)
        self._main_layout.setSpacing(10)
        self._main_layout.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(container)

        self._main_layout.addWidget(self._build_ion_group())
        self._main_layout.addWidget(self._build_target_group())
        self._main_layout.addWidget(self._build_physics_group())
        self._main_layout.addWidget(self._build_output_group())
        self._main_layout.addStretch()

        left_layout.addWidget(scroll)

        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(6)
        self._btn_load   = QPushButton("📂  Charger JSON")
        self._btn_save   = QPushButton("💾  Sauvegarder JSON")
        self._btn_export = QPushButton("📄  Exporter fichier .in")
        self._btn_apply  = QPushButton("✓  Appliquer")
        self._btn_apply.setStyleSheet(
            "QPushButton { background: #1565C0; color: white; font-weight: bold; "
            "border-radius: 8px; padding: 6px 14px; }"
            "QPushButton:hover { background: #1976D2; }"
        )
        self._btn_load.clicked.connect(self._load_config)
        self._btn_save.clicked.connect(self._save_config)
        self._btn_export.clicked.connect(self._export_csipI)
        self._btn_apply.clicked.connect(self._apply)
        btn_bar.addWidget(self._btn_load)
        btn_bar.addWidget(self._btn_save)
        btn_bar.addStretch()
        btn_bar.addWidget(self._btn_export)
        btn_bar.addWidget(self._btn_apply)
        left_layout.addLayout(btn_bar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 8, 8, 8)
        right_layout.setSpacing(4)

        preview_header = QHBoxLayout()
        preview_title = QLabel("Aperçu – fichier d'entrée CSiPI")
        preview_title.setStyleSheet("font-weight: bold; color: #1565C0; font-size: 12px;")
        preview_header.addWidget(preview_title)
        preview_header.addStretch()
        copy_btn = QPushButton("Copier")
        copy_btn.setFixedWidth(70)
        copy_btn.clicked.connect(self._copy_preview)
        preview_header.addWidget(copy_btn)
        right_layout.addLayout(preview_header)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFont(QFont("Monospace", 9))
        self._preview.setStyleSheet(
            "background: #1E1E1E; color: #9CDCFE; border-radius: 8px; padding: 8px;"
        )
        right_layout.addWidget(self._preview)

        self._validity_label = QLabel()
        self._validity_label.setAlignment(Qt.AlignCenter)
        self._validity_label.setStyleSheet("border-radius: 6px; padding: 4px 8px; font-size: 11px;")
        right_layout.addWidget(self._validity_label)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        root.addWidget(splitter)

    def _build_ion_group(self) -> QGroupBox:
        grp = QGroupBox("Ion incident")
        form = QFormLayout(grp)
        form.setSpacing(6)

        self._ion_elem = QComboBox()
        self._ion_elem.addItems(sorted(ELEMENTS.keys()))
        self._ion_elem.currentTextChanged.connect(self._on_ion_elem_changed)
        form.addRow("Élément :", self._ion_elem)

        info_row = QHBoxLayout()
        self._ion_Z    = QLabel()
        self._ion_mass = QLabel()
        for lbl in (self._ion_Z, self._ion_mass):
            lbl.setStyleSheet(
                "color: #1565C0; font-size: 10px; background: #E3F2FD; "
                "border-radius: 6px; padding: 2px 8px;"
            )
        info_row.addWidget(self._ion_Z)
        info_row.addWidget(self._ion_mass)
        info_row.addStretch()
        form.addRow("Propriétés :", info_row)

        self._ion_energy = QDoubleSpinBox()
        self._ion_energy.setRange(1.0, 1e6)
        self._ion_energy.setSuffix(" eV")
        self._ion_energy.setDecimals(1)
        self._ion_energy.setToolTip("Énergie cinétique de l'ion incident (1 eV – 1 MeV)")
        self._ion_energy.valueChanged.connect(self._on_param_changed)
        form.addRow("Énergie :", self._ion_energy)

        self._ion_angle = QDoubleSpinBox()
        self._ion_angle.setRange(0.0, 89.9)
        self._ion_angle.setSuffix(" °")
        self._ion_angle.setDecimals(1)
        self._ion_angle.setToolTip("Angle d'incidence par rapport à la normale (0° = normal)")
        self._ion_angle.valueChanged.connect(self._on_param_changed)
        form.addRow("Angle d'incidence :", self._ion_angle)

        self._num_ions = QSpinBox()
        self._num_ions.setRange(100, 10_000_000)
        self._num_ions.setSingleStep(1000)
        self._num_ions.setToolTip("Nombre d'ions simulés (statistique Monte-Carlo)")
        self._num_ions.valueChanged.connect(self._on_param_changed)
        form.addRow("Nombre d'ions :", self._num_ions)

        self._time_estimate = QLabel()
        self._time_estimate.setStyleSheet("color: #757575; font-size: 10px;")
        form.addRow("", self._time_estimate)
        self._num_ions.valueChanged.connect(self._update_time_estimate)

        return grp

    def _build_target_group(self) -> QGroupBox:
        grp = QGroupBox("Cible (structure multicouches)")
        layout = QVBoxLayout(grp)
        layout.setSpacing(6)

        self._frac_warning = QLabel()
        self._frac_warning.setStyleSheet(
            "color: #E65100; font-size: 10px; background: #FFF3E0; "
            "border-radius: 4px; padding: 3px 8px;"
        )
        self._frac_warning.setVisible(False)
        layout.addWidget(self._frac_warning)

        self._layers_layout = QVBoxLayout()
        self._layers_layout.setSpacing(4)
        layout.addLayout(self._layers_layout)

        add_btn = QPushButton("＋  Ajouter une couche")
        add_btn.clicked.connect(lambda: self._add_layer())
        add_btn.setStyleSheet(
            "QPushButton { background: #E8F5E9; border: 1px solid #A5D6A7; "
            "border-radius: 8px; color: #2E7D32; padding: 5px 12px; }"
            "QPushButton:hover { background: #C8E6C9; }"
        )
        layout.addWidget(add_btn)
        return grp

    def _build_physics_group(self) -> QGroupBox:
        grp = QGroupBox("Paramètres physiques (BCA)")
        form = QFormLayout(grp)
        form.setSpacing(6)

        self._potential = QComboBox()
        self._potential.addItems(INTERATOMIC_POTENTIALS)
        self._potential.setToolTip("Potentiel interatomique utilisé pour les collisions binaires")
        self._potential.currentTextChanged.connect(self._on_param_changed)
        form.addRow("Potentiel interatomique :", self._potential)

        self._binding_model = QComboBox()
        self._binding_model.addItems(SURFACE_BINDING_MODELS)
        self._binding_model.setToolTip("Modèle d'énergie de liaison de surface")
        self._binding_model.currentTextChanged.connect(self._on_param_changed)
        form.addRow("Modèle énergie de surface :", self._binding_model)

        self._disp_energy = QDoubleSpinBox()
        self._disp_energy.setRange(0.1, 1000.0)
        self._disp_energy.setSuffix(" eV")
        self._disp_energy.setToolTip("Énergie seuil de déplacement atomique (typiquement 25–40 eV)")
        self._disp_energy.valueChanged.connect(self._on_param_changed)
        form.addRow("Énergie de déplacement :", self._disp_energy)

        self._cutoff_energy = QDoubleSpinBox()
        self._cutoff_energy.setRange(0.01, 100.0)
        self._cutoff_energy.setSuffix(" eV")
        self._cutoff_energy.setDecimals(3)
        self._cutoff_energy.setToolTip("Énergie en dessous de laquelle la trajectoire est arrêtée")
        self._cutoff_energy.valueChanged.connect(self._on_param_changed)
        form.addRow("Énergie de coupure :", self._cutoff_energy)

        flags_row = QHBoxLayout()
        self._track_recoils = QCheckBox("Suivre les reculs")
        self._track_recoils.setToolTip("Active le suivi des atomes de recul (cascade de dommages)")
        self._calc_traj = QCheckBox("Calculer les trajectoires")
        self._calc_traj.setToolTip("Enregistre les trajectoires complètes (fichier volumineux)")
        self._track_recoils.toggled.connect(self._on_param_changed)
        self._calc_traj.toggled.connect(self._on_param_changed)
        flags_row.addWidget(self._track_recoils)
        flags_row.addWidget(self._calc_traj)
        flags_row.addStretch()
        form.addRow(flags_row)

        self._max_depth = QDoubleSpinBox()
        self._max_depth.setRange(1.0, 100000.0)
        self._max_depth.setSuffix(" nm")
        self._max_depth.setToolTip("Profondeur maximale de simulation")
        self._max_depth.valueChanged.connect(self._on_param_changed)
        form.addRow("Profondeur maximale :", self._max_depth)

        return grp

    def _build_output_group(self) -> QGroupBox:
        grp = QGroupBox("Options de sortie")
        form = QFormLayout(grp)
        form.setSpacing(6)

        dir_row = QHBoxLayout()
        self._out_dir_edit = QLineEdit()
        self._out_dir_edit.textChanged.connect(self._on_param_changed)
        dir_btn = QPushButton("…")
        dir_btn.setFixedWidth(32)
        dir_btn.clicked.connect(self._choose_output_dir)
        dir_row.addWidget(self._out_dir_edit)
        dir_row.addWidget(dir_btn)
        form.addRow("Dossier de sortie :", dir_row)

        self._out_prefix = QLineEdit()
        self._out_prefix.textChanged.connect(self._on_param_changed)
        form.addRow("Préfixe des fichiers :", self._out_prefix)

        checks_row = QHBoxLayout()
        self._save_yield   = QCheckBox("Rendement");       self._save_yield.setChecked(True)
        self._save_traj    = QCheckBox("Trajectoires")
        self._save_angular = QCheckBox("Dist. angulaire"); self._save_angular.setChecked(True)
        self._save_energy  = QCheckBox("Dist. énergie");  self._save_energy.setChecked(True)
        for cb in (self._save_yield, self._save_traj, self._save_angular, self._save_energy):
            cb.toggled.connect(self._on_param_changed)
            checks_row.addWidget(cb)
        checks_row.addStretch()
        form.addRow("Fichiers de sortie :", checks_row)

        bins_row = QHBoxLayout()
        bins_row.addWidget(QLabel("Bins angulaires:"))
        self._bins_angle = QSpinBox()
        self._bins_angle.setRange(10, 360)
        self._bins_angle.setFixedWidth(70)
        self._bins_angle.valueChanged.connect(self._on_param_changed)
        bins_row.addWidget(self._bins_angle)
        bins_row.addSpacing(16)
        bins_row.addWidget(QLabel("Bins énergie:"))
        self._bins_energy = QSpinBox()
        self._bins_energy.setRange(10, 1000)
        self._bins_energy.setFixedWidth(70)
        self._bins_energy.valueChanged.connect(self._on_param_changed)
        bins_row.addWidget(self._bins_energy)
        bins_row.addStretch()
        form.addRow(bins_row)

        return grp

    # ------------------------------------------------------------------
    # Gestion des couches
    # ------------------------------------------------------------------

    def _add_layer(self, layer: TargetLayer = None):
        if layer is None:
            layer = TargetLayer()
            self.config.target_layers.append(layer)
        idx = len(self._layer_widgets)
        w = TargetLayerWidget(layer, idx)
        w.removed.connect(self._remove_layer)
        w.changed.connect(self._on_param_changed)
        self._layer_widgets.append(w)
        self._layers_layout.addWidget(w)
        self._check_fractions()

    def _remove_layer(self, widget: TargetLayerWidget):
        if len(self._layer_widgets) <= 1:
            QMessageBox.warning(self, "Impossible", "La cible doit avoir au moins une couche.")
            return
        self._layer_widgets.remove(widget)
        if widget.layer in self.config.target_layers:
            self.config.target_layers.remove(widget.layer)
        self._layers_layout.removeWidget(widget)
        widget.deleteLater()
        for i, w in enumerate(self._layer_widgets):
            w.set_index(i)
        self._check_fractions()
        self._on_param_changed()

    def _check_fractions(self):
        total = sum(w.layer.fraction for w in self._layer_widgets)
        if abs(total - 1.0) > 0.01 and len(self._layer_widgets) > 1:
            self._frac_warning.setText(
                f"⚠  La somme des fractions atomiques est {total:.3f} (doit être 1.000)"
            )
            self._frac_warning.setVisible(True)
        else:
            self._frac_warning.setVisible(False)

    # ------------------------------------------------------------------
    # Synchronisation UI ↔ config
    # ------------------------------------------------------------------

    def _load_config_to_ui(self):
        cfg = self.config
        self._ion_elem.setCurrentText(cfg.ion.element)
        self._ion_energy.setValue(cfg.ion.energy_eV)
        self._ion_angle.setValue(cfg.ion.angle_deg)
        self._num_ions.setValue(cfg.ion.num_ions)
        for w in list(self._layer_widgets):
            self._layers_layout.removeWidget(w)
            w.deleteLater()
        self._layer_widgets.clear()
        for layer in cfg.target_layers:
            self._add_layer(layer)
        self._potential.setCurrentText(cfg.physics.potential)
        self._binding_model.setCurrentText(cfg.physics.surface_binding_model)
        self._disp_energy.setValue(cfg.physics.displacement_energy_eV)
        self._cutoff_energy.setValue(cfg.physics.cutoff_energy_eV)
        self._track_recoils.setChecked(cfg.physics.track_recoils)
        self._calc_traj.setChecked(cfg.physics.calculate_trajectories)
        self._max_depth.setValue(cfg.physics.max_depth_nm)
        self._out_dir_edit.setText(cfg.output.output_directory)
        self._out_prefix.setText(cfg.output.output_prefix)
        self._save_yield.setChecked(cfg.output.save_yield)
        self._save_traj.setChecked(cfg.output.save_trajectories)
        self._save_angular.setChecked(cfg.output.save_angular_distribution)
        self._save_energy.setChecked(cfg.output.save_energy_distribution)
        self._bins_angle.setValue(cfg.output.num_bins_angle)
        self._bins_energy.setValue(cfg.output.num_bins_energy)
        self._refresh_preview()

    def collect_config(self) -> SimulationConfig:
        cfg = self.config
        cfg.ion.element = self._ion_elem.currentText()
        cfg.ion.energy_eV = self._ion_energy.value()
        cfg.ion.angle_deg = self._ion_angle.value()
        cfg.ion.num_ions = self._num_ions.value()
        cfg.physics.potential = self._potential.currentText()
        cfg.physics.surface_binding_model = self._binding_model.currentText()
        cfg.physics.displacement_energy_eV = self._disp_energy.value()
        cfg.physics.cutoff_energy_eV = self._cutoff_energy.value()
        cfg.physics.track_recoils = self._track_recoils.isChecked()
        cfg.physics.calculate_trajectories = self._calc_traj.isChecked()
        cfg.physics.max_depth_nm = self._max_depth.value()
        cfg.output.output_directory = self._out_dir_edit.text()
        cfg.output.output_prefix = self._out_prefix.text()
        cfg.output.save_yield = self._save_yield.isChecked()
        cfg.output.save_trajectories = self._save_traj.isChecked()
        cfg.output.save_angular_distribution = self._save_angular.isChecked()
        cfg.output.save_energy_distribution = self._save_energy.isChecked()
        cfg.output.num_bins_angle = self._bins_angle.value()
        cfg.output.num_bins_energy = self._bins_energy.value()
        return cfg

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_ion_elem_changed(self, elem: str):
        info = ELEMENTS.get(elem, {})
        self._ion_Z.setText(f"Z = {info.get('Z', '?')}")
        self._ion_mass.setText(f"M = {info.get('mass', '?')} u")
        self._on_param_changed()

    def _on_param_changed(self):
        self._check_fractions()
        self._preview_timer.start()

    def _refresh_preview(self):
        cfg = self.collect_config()
        self._preview.setPlainText(cfg.to_csipI_input())

        errors = []
        if cfg.ion.energy_eV < cfg.physics.cutoff_energy_eV:
            errors.append("Énergie ion < énergie de coupure")
        if not cfg.target_layers:
            errors.append("Aucune couche de cible définie")
        if cfg.ion.energy_eV < 10:
            errors.append("Énergie très faible (< 10 eV) – résultats peu fiables")

        if errors:
            self._validity_label.setText("⚠  " + "  |  ".join(errors))
            self._validity_label.setStyleSheet(
                "background: #FFF3E0; color: #E65100; border-radius: 6px; padding: 4px 8px; font-size: 11px;"
            )
        else:
            ion = cfg.ion
            target = cfg.target_layers[0].element if cfg.target_layers else "?"
            self._validity_label.setText(
                f"✓  Configuration valide  —  {ion.element} → {target}  "
                f"|  E = {ion.energy_eV:.0f} eV  |  θ = {ion.angle_deg:.1f}°  "
                f"|  {ion.num_ions:,} ions"
            )
            self._validity_label.setStyleSheet(
                "background: #E8F5E9; color: #2E7D32; border-radius: 6px; padding: 4px 8px; font-size: 11px;"
            )

    def _update_time_estimate(self, n: int):
        sec = n / 50_000
        txt = f"~{sec:.0f} s" if sec < 60 else f"~{sec/60:.1f} min"
        self._time_estimate.setText(f"Estimation : {txt} de calcul")

    def _apply(self):
        self.config_changed.emit(self.collect_config())

    def _copy_preview(self):
        QApplication.clipboard().setText(self._preview.toPlainText())

    def _choose_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Choisir le dossier de sortie")
        if d:
            self._out_dir_edit.setText(d)

    def _save_config(self):
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer la configuration", "", "JSON (*.json)")
        if path:
            self.collect_config().to_json(path)
            QMessageBox.information(self, "Succès", f"Configuration sauvegardée :\n{path}")

    def _load_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "Charger une configuration", "", "JSON (*.json)")
        if path:
            try:
                self.config = SimulationConfig.from_json(path)
                self._load_config_to_ui()
                self.config_changed.emit(self.config)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de charger :\n{e}")

    def _export_csipI(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter le fichier d'entrée CSiPI", "", "Fichier d'entrée (*.in);;Tous (*.*)"
        )
        if path:
            with open(path, "w") as f:
                f.write(self.collect_config().to_csipI_input())
            QMessageBox.information(self, "Succès", f"Fichier .in exporté :\n{path}")
