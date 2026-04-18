"""
Panneau d'aide – onglet « Aide / Documentation ».
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QListWidget, QListWidgetItem, QSplitter, QLabel,
    QPushButton, QFileDialog, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


HELP_SECTIONS = {
    "Vue d'ensemble": """\
CSiPI GUI – Interface graphique pour le Code de Simulation de la Pulvérisation Ionique
=======================================================================================

CSiPI GUI est une interface graphique développée à l'ONERA (DPHY/CSE, Toulouse)
pour configurer, lancer et analyser des simulations d'interaction ion–matière par
la méthode BCA (Binary Collision Approximation).

Elle est organisée en onglets et panneaux détachables :

  1. Configuration     – Paramétrage complet de la simulation
  2. Exécution         – Lancement du binaire CSiPI, logs en temps réel
  3. Aide              – Ce panneau de documentation

Panneaux flottants / détachables (via le menu Affichage) :
  • Rendements        – Courbes Y(E) et Y(θ) (formule de Yamamura)
  • Trajectoires      – Visualisation Monte-Carlo des trajectoires
  • Post-traitement   – Distributions angulaire et en énergie

Technologies : Python 3 · PyQt5 · Matplotlib · NumPy
Responsable stage : Luca Chiabò (luca.chiabo@onera.fr)
""",

    "Onglet Configuration": """\
Onglet Configuration
====================

Cet onglet est divisé en deux colonnes :

COLONNE GAUCHE – Formulaire de paramètres
-----------------------------------------

[Ion incident]
  - Élément          : choix de l'ion parmi le tableau périodique
  - Propriétés       : numéro atomique Z et masse M affichés dynamiquement
  - Énergie          : énergie cinétique de l'ion (1 eV à 1 MeV)
  - Angle d'incidence: angle par rapport à la normale à la surface
  - Nombre d'ions    : nombre de trajectoires Monte-Carlo simulées
  - Estimation       : temps de calcul indicatif (~50 000 ions/s)

[Cible (structure multicouches)]
  Chaque couche possède :
  - Élément, fraction atomique, épaisseur, option Bulk ∞

[Paramètres physiques BCA]
  - Potentiel interatomique, modèle de surface, énergies seuils

[Options de sortie]
  - Dossier, préfixe, fichiers à générer, résolution des histogrammes

BOUTONS
-------
  - Charger JSON / Sauvegarder JSON / Exporter .in / Appliquer

COLONNE DROITE – Aperçu du fichier .in
---------------------------------------
  Affiche en temps réel le contenu du fichier d'entrée CSiPI généré.
""",

    "Panneaux détachables": """\
Panneaux détachables (QDockWidget)
===================================

Les trois panneaux de visualisation sont des fenêtres détachables :
  • Rendements (📈)
  • Trajectoires (🔀)
  • Post-traitement (📊)

INTERACTIONS POSSIBLES
----------------------
  - Glisser la barre de titre pour déplacer le panneau
  - Double-cliquer sur la barre de titre pour détacher / réancrer
  - Cliquer sur ✕ pour fermer (récupérable via menu Affichage)
  - Imbriquer deux panneaux pour créer des onglets côte à côte

MENU AFFICHAGE
--------------
  - Basculer thème clair/sombre  (Ctrl+T)
  - Panneau Rendements           : rouvrir si fermé
  - Panneau Trajectoires         : rouvrir si fermé
  - Panneau Post-traitement      : rouvrir si fermé
  - Réinitialiser la disposition : repositionner tous les docks
""",

    "Onglet Rendements": """\
Panneau Rendements
==================

Affiche les courbes de rendement de pulvérisation calculées analytiquement
par la formule de Yamamura.

  - Y(E) : rendement en fonction de l'énergie incidente
  - Y(θ) : rendement en fonction de l'angle d'incidence

FORMULE DE YAMAMURA
-------------------
  Y(E) = Q · Sn(E) · (1 − sqrt(Eth / E))²
""",

    "Onglet Trajectoires": """\
Panneau Trajectoires
====================

Visualise les trajectoires des ions et des atomes pulvérisés
par simulation Monte-Carlo BCA.

  - Bleu  : ion implanté
  - Rouge : ion rétro-diffusé
  - Orange: atome éjecté (pulvérisé)
""",

    "Onglet Post-traitement": """\
Panneau Post-traitement
=======================

Affiche les distributions statistiques issues de la simulation.

  - Distribution angulaire : polaire ou cartésienne
  - Distribution en énergie : loi de Thompson f(E) ∝ E / (E + Es)³
  - Vue combinée : les deux côte à côte
""",

    "Onglet Exécution": """\
Onglet Exécution
================

Permet de lancer le binaire CSiPI et de suivre son exécution.

  - Sélection du binaire CSiPI ou mode démonstration (mock)
  - Résumé de la configuration active
  - Bouton Lancer / Annuler
  - Barre de progression + console de logs temps réel
  - Export du log en .txt

MODE DÉMONSTRATION
------------------
  Si le binaire CSiPI n'est pas disponible, l'application fonctionne en
  mode démo avec des données synthétiques.
""",

    "Principes physiques BCA": """\
Principes physiques – Binary Collision Approximation (BCA)
==========================================================

CSiPI repose sur le modèle BCA, qui décompose l'interaction ion–matière
en une séquence de collisions binaires successives.

POTENTIELS INTERATOMIQUES
--------------------------
  ZBL, Moliere, Lenz-Jensen, Kr-C, Nakagawa-Yamamura

GRANDEURS CALCULÉES
-------------------
  - Rendement Y, distributions angulaire et en énergie, trajectoires

FORMULE DE YAMAMURA : Y(E) = Q · Sn · (1 − √(Eth/E))² × f(θ)
LOI DE THOMPSON     : f(E) ∝ E / (E + Es)³
""",

    "Fichier de configuration JSON": """\
Format du fichier de configuration JSON
========================================

{
  "ion": { "element": "Ar", "energy_eV": 1000.0, "angle_deg": 0.0, "num_ions": 10000 },
  "target_layers": [
    { "element": "Si", "fraction": 1.0, "thickness_nm": 100.0, "bulk": true }
  ],
  "physics": {
    "potential": "ZBL", "surface_binding_model": "Planar",
    "displacement_energy_eV": 25.0, "cutoff_energy_eV": 1.0,
    "track_recoils": true, "calculate_trajectories": false, "max_depth_nm": 500.0
  },
  "output": {
    "output_directory": "./results", "output_prefix": "sim",
    "save_yield": true, "save_trajectories": false,
    "save_angular_distribution": true, "save_energy_distribution": true,
    "num_bins_angle": 90, "num_bins_energy": 200
  }
}

RACCOURCIS CLAVIER
------------------
  Ctrl+O  : Charger JSON          Ctrl+S  : Sauvegarder JSON
  Ctrl+E  : Exporter .in          Ctrl+N  : Nouvelle configuration
  Ctrl+Q  : Quitter               Ctrl+T  : Toggle thème clair/sombre
  F5      : Lancer la simulation
""",
}


class HelpPanel(QWidget):
    """Panneau d'aide avec navigation par sections et affichage texte brut."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        header = QLabel("Documentation CSiPI GUI")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #1565C0; padding: 4px 0;")
        root.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        self._section_list = QListWidget()
        self._section_list.setFixedWidth(210)
        self._section_list.setStyleSheet(
            "QListWidget { border: 1px solid #BDBDBD; border-radius: 8px; "
            "background: #FAFAFA; padding: 4px; }"
            "QListWidget::item { padding: 6px 10px; border-radius: 5px; }"
            "QListWidget::item:selected { background: #1565C0; color: white; }"
            "QListWidget::item:hover:!selected { background: #E3F2FD; color: #1565C0; }"
        )
        for title in HELP_SECTIONS:
            self._section_list.addItem(QListWidgetItem(title))
        self._section_list.currentRowChanged.connect(self._on_section_changed)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Monospace", 10))
        self._text.setStyleSheet(
            "QTextEdit { background: #FAFAFA; border: 1px solid #BDBDBD; "
            "border-radius: 8px; padding: 10px; color: #212121; }"
        )
        right_layout.addWidget(self._text)

        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(6)
        copy_btn       = QPushButton("Copier le texte");              copy_btn.clicked.connect(self._copy_text)
        export_btn     = QPushButton("Exporter section en .txt");     export_btn.clicked.connect(self._export_txt)
        export_all_btn = QPushButton("Exporter toute la doc en .txt"); export_all_btn.clicked.connect(self._export_all_txt)
        btn_bar.addWidget(copy_btn)
        btn_bar.addWidget(export_btn)
        btn_bar.addStretch()
        btn_bar.addWidget(export_all_btn)
        right_layout.addLayout(btn_bar)

        splitter.addWidget(self._section_list)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)
        self._section_list.setCurrentRow(0)

    def _on_section_changed(self, row: int):
        if row < 0:
            return
        title = self._section_list.item(row).text()
        self._text.setPlainText(HELP_SECTIONS.get(title, ""))

    def _copy_text(self):
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(self._text.toPlainText())

    def _export_txt(self):
        row = self._section_list.currentRow()
        if row < 0:
            return
        title = self._section_list.item(row).text()
        safe_title = title.replace(" ", "_").replace("/", "-")
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la section", f"{safe_title}.txt", "Texte (*.txt);;Tous (*.*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(HELP_SECTIONS[title])
            QMessageBox.information(self, "Succès", f"Section exportée :\n{path}")

    def _export_all_txt(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter toute la documentation", "CSiPI_GUI_documentation.txt",
            "Texte (*.txt);;Tous (*.*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                for title, content in HELP_SECTIONS.items():
                    f.write("=" * 70 + "\n")
                    f.write(f"  {title}\n")
                    f.write("=" * 70 + "\n\n")
                    f.write(content)
                    f.write("\n\n")
            QMessageBox.information(self, "Succès", f"Documentation exportée :\n{path}")
