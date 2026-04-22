"""
CSiPI GUI  Interface graphique pour le Code de Simulation de la Pulvérisation Ionique.

Point d'entrée principal de l'application.
"""

import sys
import os

# Ajouter src/ au chemin Python afin que les imports relatifs fonctionnent
sys.path.insert(0, os.path.dirname(__file__))

import matplotlib
matplotlib.use("Qt5Agg")

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QStatusBar,
    QAction, QMenuBar, QMessageBox, QSizePolicy,
    QPushButton, QStyleFactory,
)
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

from gui.panel_config import ConfigPanel
from gui.panel_yield import YieldPanel
from gui.panel_trajectories import TrajectoriesPanel
from gui.panel_postprocess import PostProcessPanel
from gui.panel_runner import RunnerPanel
from gui.panel_help import HelpPanel
from core.simulation_config import SimulationConfig



# Feuilles de style


STYLE_LIGHT = """
/*  Fenêtre & fond général  */
QMainWindow { background-color: #F5F5F5; }
QWidget { color: #212121; }

/*  Onglets  */
QTabWidget::pane { border: 1px solid #BDBDBD; border-radius: 10px; background: #FFFFFF; }
QTabBar::tab {
    background: #E0E0E0; color: #424242;
    padding: 8px 18px; border-top-left-radius: 8px; border-top-right-radius: 8px;
    min-width: 120px; font-weight: 500;
}
QTabBar::tab:selected { background: #1565C0; color: #FFFFFF; }
QTabBar::tab:hover:!selected { background: #BBDEFB; color: #1565C0; }

/*  GroupBox  */
QGroupBox {
    font-weight: bold; color: #1565C0;
    border: 1px solid #BDBDBD; border-radius: 10px;
    margin-top: 10px; padding-top: 8px; background: #FFFFFF;
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #1565C0; }

/*  Boutons  */
QPushButton {
    background: #E3F2FD; border: 1px solid #90CAF9;
    border-radius: 8px; padding: 6px 14px; color: #1565C0; min-height: 24px;
}
QPushButton:hover { background: #BBDEFB; color: #0D47A1; }
QPushButton:pressed { background: #90CAF9; color: #0D47A1; }
QPushButton:disabled { background: #EEEEEE; border-color: #BDBDBD; color: #9E9E9E; }

/*  Champs de saisie  */
QLineEdit, QSpinBox, QDoubleSpinBox {
    border: 1px solid #BDBDBD; border-radius: 8px; padding: 4px 8px;
    background: #FFFFFF; color: #212121;
    selection-background-color: #1565C0; selection-color: #FFFFFF; min-height: 24px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1.5px solid #1565C0; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background: #EEEEEE; color: #9E9E9E; }

/*  Boutons +/- des SpinBox  */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right;
    width: 22px; height: 14px;
    border-left: 1px solid #BDBDBD; border-bottom: 1px solid #BDBDBD;
    border-top-right-radius: 8px; background: #E3F2FD;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover { background: #BBDEFB; }
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed { background: #90CAF9; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-bottom: 6px solid #1565C0;
}
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled { border-bottom-color: #9E9E9E; }
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 22px; height: 14px;
    border-left: 1px solid #BDBDBD; border-top: 1px solid #BDBDBD;
    border-bottom-right-radius: 8px; background: #E3F2FD;
}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #BBDEFB; }
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed { background: #90CAF9; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 6px solid #1565C0;
}
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled { border-top-color: #9E9E9E; }

/*  ComboBox  */
QComboBox {
    border: 1px solid #BDBDBD; border-radius: 8px; padding: 4px 8px;
    background: #FFFFFF; color: #212121;
    selection-background-color: #1565C0; selection-color: #FFFFFF; min-height: 24px;
}
QComboBox:focus { border: 1.5px solid #1565C0; }
QComboBox:disabled { background: #EEEEEE; color: #9E9E9E; }
QComboBox::drop-down { border: none; width: 24px; border-top-right-radius: 8px; border-bottom-right-radius: 8px; }
QComboBox QAbstractItemView {
    background: #FFFFFF; color: #212121; border: 1px solid #BDBDBD;
    border-radius: 6px; selection-background-color: #1565C0; selection-color: #FFFFFF;
    outline: none; padding: 4px;
}
QComboBox QAbstractItemView::item { padding: 4px 8px; color: #212121; background: #FFFFFF; }
QComboBox QAbstractItemView::item:hover { background: #E3F2FD; color: #1565C0; }
QComboBox QAbstractItemView::item:selected { background: #1565C0; color: #FFFFFF; }

/*  CheckBox  */
QCheckBox { color: #212121; spacing: 6px; }
QCheckBox:disabled { color: #9E9E9E; }
QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #BDBDBD; border-radius: 3px; background: #FFFFFF; }
QCheckBox::indicator:checked { background: #1565C0; border-color: #1565C0; }
QCheckBox::indicator:hover { border-color: #1565C0; }

/*  Labels  */
QLabel { color: #212121; background: transparent; }

/*  ScrollArea  */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #F5F5F5; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #BDBDBD; border-radius: 5px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #90CAF9; }

/*  Barre de statut  */
QStatusBar { background: #E3F2FD; color: #1565C0; font-size: 11px; }

/*  Barre d'outils matplotlib  */
QToolBar { background: #F5F5F5; border: none; spacing: 4px; }
QToolButton {
    background: transparent; border: 1px solid transparent;
    border-radius: 3px; padding: 2px 4px; color: #424242;
}
QToolButton:hover { background: #E3F2FD; border-color: #90CAF9; color: #1565C0; }

/*  Séparateur  */
QSplitter::handle { background: #E0E0E0; }

/*  Barre de progression  */
QProgressBar {
    border: 1px solid #BDBDBD; border-radius: 4px; background: #EEEEEE;
    color: #212121; text-align: center; height: 16px;
}
QProgressBar::chunk { background: #1565C0; border-radius: 3px; }

/*  Tableau  */
QTableWidget {
    background: #FFFFFF; color: #212121; gridline-color: #E0E0E0;
    border: 1px solid #BDBDBD;
    selection-background-color: #BBDEFB; selection-color: #212121;
}
QHeaderView::section {
    background: #E3F2FD; color: #1565C0; font-weight: bold;
    padding: 4px; border: none; border-bottom: 1px solid #BDBDBD;
}

/*  Frame  */
QFrame[frameShape="1"] { background: #FAFAFA; border: 1px solid #E0E0E0; border-radius: 4px; }

/*  DockWidget  */
QDockWidget { font-weight: bold; color: #1565C0; }
QDockWidget::title { background: #E3F2FD; padding: 6px 10px; border-bottom: 1px solid #BDBDBD; }
QDockWidget::close-button, QDockWidget::float-button { background: transparent; border: none; padding: 2px; }
QDockWidget::close-button:hover, QDockWidget::float-button:hover { background: #BBDEFB; border-radius: 3px; }
"""

STYLE_DARK = """
/*  Fenêtre & fond général  */
QMainWindow { background-color: #1E1E2E; }
QWidget { color: #CDD6F4; background-color: #1E1E2E; }

/*  Onglets  */
QTabWidget::pane { border: 1px solid #45475A; border-radius: 10px; background: #181825; }
QTabBar::tab {
    background: #313244; color: #BAC2DE;
    padding: 8px 18px; border-top-left-radius: 8px; border-top-right-radius: 8px;
    min-width: 120px; font-weight: 500;
}
QTabBar::tab:selected { background: #89B4FA; color: #1E1E2E; }
QTabBar::tab:hover:!selected { background: #45475A; color: #89B4FA; }

/*  GroupBox  */
QGroupBox {
    font-weight: bold; color: #89B4FA;
    border: 1px solid #45475A; border-radius: 10px;
    margin-top: 10px; padding-top: 8px; background: #181825;
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; color: #89B4FA; }

/*  Boutons  */
QPushButton {
    background: #313244; border: 1px solid #45475A;
    border-radius: 8px; padding: 6px 14px; color: #89B4FA; min-height: 24px;
}
QPushButton:hover { background: #45475A; color: #B4BEFE; }
QPushButton:pressed { background: #585B70; color: #CDD6F4; }
QPushButton:disabled { background: #313244; border-color: #45475A; color: #585B70; }

/*  Champs de saisie  */
QLineEdit, QSpinBox, QDoubleSpinBox {
    border: 1px solid #45475A; border-radius: 8px; padding: 4px 8px;
    background: #313244; color: #CDD6F4;
    selection-background-color: #89B4FA; selection-color: #1E1E2E; min-height: 24px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1.5px solid #89B4FA; }
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background: #181825; color: #585B70; }

/*  Boutons +/- des SpinBox  */
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right;
    width: 22px; height: 14px;
    border-left: 1px solid #45475A; border-bottom: 1px solid #45475A;
    border-top-right-radius: 8px; background: #45475A;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover { background: #585B70; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-bottom: 6px solid #89B4FA;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 22px; height: 14px;
    border-left: 1px solid #45475A; border-top: 1px solid #45475A;
    border-bottom-right-radius: 8px; background: #45475A;
}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #585B70; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 6px solid #89B4FA;
}

/*  ComboBox  */
QComboBox {
    border: 1px solid #45475A; border-radius: 8px; padding: 4px 8px;
    background: #313244; color: #CDD6F4;
    selection-background-color: #89B4FA; selection-color: #1E1E2E; min-height: 24px;
}
QComboBox:focus { border: 1.5px solid #89B4FA; }
QComboBox:disabled { background: #181825; color: #585B70; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #313244; color: #CDD6F4; border: 1px solid #45475A;
    border-radius: 6px; selection-background-color: #89B4FA; selection-color: #1E1E2E;
    outline: none; padding: 4px;
}
QComboBox QAbstractItemView::item { padding: 4px 8px; }
QComboBox QAbstractItemView::item:hover { background: #45475A; color: #89B4FA; }
QComboBox QAbstractItemView::item:selected { background: #89B4FA; color: #1E1E2E; }

/*  CheckBox  */
QCheckBox { color: #CDD6F4; spacing: 6px; }
QCheckBox:disabled { color: #585B70; }
QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #45475A; border-radius: 3px; background: #313244; }
QCheckBox::indicator:checked { background: #89B4FA; border-color: #89B4FA; }
QCheckBox::indicator:hover { border-color: #89B4FA; }

/*  Labels  */
QLabel { color: #CDD6F4; background: transparent; }

/*  ScrollArea  */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #181825; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #45475A; border-radius: 5px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: #89B4FA; }

/*  Barre de statut  */
QStatusBar { background: #181825; color: #89B4FA; font-size: 11px; }

/*  Barre d'outils matplotlib  */
QToolBar { background: #1E1E2E; border: none; spacing: 4px; }
QToolButton {
    background: transparent; border: 1px solid transparent;
    border-radius: 3px; padding: 2px 4px; color: #BAC2DE;
}
QToolButton:hover { background: #313244; border-color: #45475A; color: #89B4FA; }

/*  Séparateur  */
QSplitter::handle { background: #45475A; }

/*  Barre de progression  */
QProgressBar {
    border: 1px solid #45475A; border-radius: 4px; background: #313244;
    color: #CDD6F4; text-align: center; height: 16px;
}
QProgressBar::chunk { background: #89B4FA; border-radius: 3px; }

/*  Tableau  */
QTableWidget {
    background: #181825; color: #CDD6F4; gridline-color: #45475A;
    border: 1px solid #45475A;
    selection-background-color: #313244; selection-color: #CDD6F4;
}
QHeaderView::section {
    background: #313244; color: #89B4FA; font-weight: bold;
    padding: 4px; border: none; border-bottom: 1px solid #45475A;
}

/*  Frame  */
QFrame[frameShape="1"] { background: #181825; border: 1px solid #45475A; border-radius: 4px; }

/*  DockWidget  */
QDockWidget { font-weight: bold; color: #89B4FA; }
QDockWidget::title { background: #313244; padding: 6px 10px; border-bottom: 1px solid #45475A; }
QDockWidget::close-button, QDockWidget::float-button { background: transparent; border: none; padding: 2px; }
QDockWidget::close-button:hover, QDockWidget::float-button:hover { background: #45475A; border-radius: 3px; }
"""



# Fenêtre principale


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSiPI GUI – Simulation de la Pulvérisation Ionique")
        self.resize(1200, 820)
        self.setMinimumSize(QSize(900, 600))

        self._dark_mode = False

        self._build_panels()
        self._build_menu()
        self._build_docks()
        self._build_status_bar()

        self._config_panel.config_changed.connect(self._on_config_changed)
        self._runner_panel.simulation_done.connect(self._on_simulation_done)

    
    # Panneaux
    

    def _build_panels(self):
        self._config_panel = ConfigPanel()
        self._yield_panel  = YieldPanel()
        self._traj_panel   = TrajectoriesPanel()
        self._post_panel   = PostProcessPanel()
        self._runner_panel = RunnerPanel()
        self._help_panel   = HelpPanel()

        cfg = self._config_panel.config
        self._yield_panel.update_config(cfg)
        self._traj_panel.update_config(cfg)
        self._post_panel.update_config(cfg)
        self._runner_panel.update_config(cfg)

    
    # Dock widgets
    

    def _build_docks(self):
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.addTab(self._config_panel, "⚙  Configuration")
        self._tabs.addTab(self._runner_panel,  "▶  Exécution")
        self._tabs.addTab(self._yield_panel,   "📈  Rendements")
        self._tabs.addTab(self._traj_panel,    "🔀  Trajectoires")
        self._tabs.addTab(self._post_panel,    "📊  Post-traitement")
        self._tabs.addTab(self._help_panel,    "❓  Aide")
        self.setCentralWidget(self._tabs)

    
    # Menu
    

    def _build_menu(self):
        menu = self.menuBar()

        # ── Fichier ─────────────────────────────────────────────────
        file_menu = menu.addMenu("Fichier")

        act_new = QAction("Nouvelle configuration", self)
        act_new.setShortcut("Ctrl+N")
        act_new.setStatusTip("Réinitialiser tous les paramètres")
        act_new.triggered.connect(self._new_config)
        file_menu.addAction(act_new)

        file_menu.addSeparator()

        act_load = QAction("Charger une configuration JSON…", self)
        act_load.setShortcut("Ctrl+O")
        act_load.triggered.connect(lambda: self._config_panel._load_config())
        file_menu.addAction(act_load)

        act_save = QAction("Sauvegarder la configuration JSON…", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(lambda: self._config_panel._save_config())
        file_menu.addAction(act_save)

        act_export_in = QAction("Exporter le fichier d'entrée CSiPI (.in)…", self)
        act_export_in.setShortcut("Ctrl+E")
        act_export_in.triggered.connect(lambda: self._config_panel._export_csipI())
        file_menu.addAction(act_export_in)

        file_menu.addSeparator()

        act_quit = QAction("Quitter", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # ── Affichage ───────────────────────────────────────────────
        view_menu = menu.addMenu("Affichage")

        act_toggle_theme = QAction("Basculer thème clair/sombre", self)
        act_toggle_theme.setShortcut("Ctrl+T")
        act_toggle_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(act_toggle_theme)

        # ── Simulation ───────────────────────────────────────────────
        sim_menu = menu.addMenu("Simulation")

        act_run = QAction("Lancer la simulation", self)
        act_run.setShortcut("F5")
        act_run.triggered.connect(self._go_to_runner)
        sim_menu.addAction(act_run)

        sim_menu.addSeparator()

        act_cfg  = QAction("Aller à Configuration", self); act_cfg.setShortcut("Ctrl+1")
        act_exec = QAction("Aller à Exécution",     self); act_exec.setShortcut("Ctrl+2")
        act_cfg.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        act_exec.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        for act in (act_cfg, act_exec):
            sim_menu.addAction(act)

        # ── Aide ────────────────────────────────────────────────────
        help_menu = menu.addMenu("Aide")

        act_about = QAction("À propos de CSiPI GUI", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

        act_bca = QAction("Principe BCA (résumé)", self)
        act_bca.triggered.connect(self._show_bca_info)
        help_menu.addAction(act_bca)

    
    # Barre de statut
    

    def _build_status_bar(self):
        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._status_label = QLabel("CSiPI GUI  |  Prêt  |  Mode : démonstration")
        self._status.addWidget(self._status_label, stretch=1)

        self._mode_label = QLabel("MODE DÉMO")
        self._mode_label.setStyleSheet(
            "background: #FFF3E0; color: #E65100; border-radius: 4px; "
            "padding: 2px 8px; font-size: 10px; font-weight: bold;"
        )
        self._status.addPermanentWidget(self._mode_label)

        self._theme_btn = QPushButton("🌙  Sombre")
        self._theme_btn.setFixedHeight(22)
        self._theme_btn.setStyleSheet(
            "QPushButton { background: #E0E0E0; border: 1px solid #BDBDBD; "
            "border-radius: 4px; padding: 0px 8px; font-size: 10px; color: #424242; }"
            "QPushButton:hover { background: #BDBDBD; }"
        )
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._status.addPermanentWidget(self._theme_btn)

        ver_label = QLabel("CSiPI GUI  v1.0  –  ONERA DPHY/CSE")
        ver_label.setStyleSheet("color: #9E9E9E; font-size: 10px; padding-right: 4px;")
        self._status.addPermanentWidget(ver_label)

    
    # Thème clair / sombre
    

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        app = QApplication.instance()
        if self._dark_mode:
            app.setStyleSheet(STYLE_DARK)
            self._theme_btn.setText("☀  Clair")
            self._apply_dark_palette(app)
            self._apply_matplotlib_style(dark=True)
        else:
            app.setStyleSheet(STYLE_LIGHT)
            self._theme_btn.setText("🌙  Sombre")
            self._apply_light_palette(app)
            self._apply_matplotlib_style(dark=False)
        self._on_config_changed(self._config_panel.config)

    @staticmethod
    def _apply_light_palette(app):
        app.setStyle(QStyleFactory.create("Fusion"))
        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor("#F5F5F5"))
        palette.setColor(QPalette.WindowText,      QColor("#212121"))
        palette.setColor(QPalette.Base,            QColor("#FFFFFF"))
        palette.setColor(QPalette.AlternateBase,   QColor("#F5F5F5"))
        palette.setColor(QPalette.Text,            QColor("#212121"))
        palette.setColor(QPalette.Highlight,       QColor("#1565C0"))
        palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
        palette.setColor(QPalette.Button,          QColor("#E3F2FD"))
        palette.setColor(QPalette.ButtonText,      QColor("#1565C0"))
        palette.setColor(QPalette.ToolTipBase,     QColor("#FFFFFF"))
        palette.setColor(QPalette.ToolTipText,     QColor("#212121"))
        palette.setColor(QPalette.Disabled, QPalette.Text,       QColor("#9E9E9E"))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#9E9E9E"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#9E9E9E"))
        palette.setColor(QPalette.Disabled, QPalette.Base,       QColor("#EEEEEE"))
        app.setPalette(palette)

    @staticmethod
    def _apply_dark_palette(app):
        app.setStyle(QStyleFactory.create("Fusion"))
        palette = QPalette()
        palette.setColor(QPalette.Window,          QColor("#1E1E2E"))
        palette.setColor(QPalette.WindowText,      QColor("#CDD6F4"))
        palette.setColor(QPalette.Base,            QColor("#181825"))
        palette.setColor(QPalette.AlternateBase,   QColor("#313244"))
        palette.setColor(QPalette.Text,            QColor("#CDD6F4"))
        palette.setColor(QPalette.Highlight,       QColor("#89B4FA"))
        palette.setColor(QPalette.HighlightedText, QColor("#1E1E2E"))
        palette.setColor(QPalette.Button,          QColor("#313244"))
        palette.setColor(QPalette.ButtonText,      QColor("#89B4FA"))
        palette.setColor(QPalette.ToolTipBase,     QColor("#313244"))
        palette.setColor(QPalette.ToolTipText,     QColor("#CDD6F4"))
        palette.setColor(QPalette.Disabled, QPalette.Text,       QColor("#585B70"))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor("#585B70"))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#585B70"))
        palette.setColor(QPalette.Disabled, QPalette.Base,       QColor("#181825"))
        app.setPalette(palette)

    @staticmethod
    def _apply_matplotlib_style(dark: bool = False):
        if dark:
            matplotlib.rcParams.update({
                "figure.facecolor":  "#1E1E2E",
                "axes.facecolor":    "#181825",
                "axes.edgecolor":    "#45475A",
                "axes.labelcolor":   "#CDD6F4",
                "axes.titlecolor":   "#89B4FA",
                "axes.grid":         True,
                "grid.color":        "#313244",
                "grid.linestyle":    "--",
                "grid.linewidth":    0.7,
                "xtick.color":       "#BAC2DE",
                "ytick.color":       "#BAC2DE",
                "text.color":        "#CDD6F4",
                "legend.framealpha": 0.85,
                "legend.edgecolor":  "#45475A",
                "legend.facecolor":  "#313244",
                "font.size":         10,
                "figure.dpi":        100,
            })
        else:
            matplotlib.rcParams.update({
                "figure.facecolor":  "#FFFFFF",
                "axes.facecolor":    "#FAFAFA",
                "axes.edgecolor":    "#BDBDBD",
                "axes.labelcolor":   "#212121",
                "axes.titlecolor":   "#1565C0",
                "axes.grid":         True,
                "grid.color":        "#E0E0E0",
                "grid.linestyle":    "--",
                "grid.linewidth":    0.7,
                "xtick.color":       "#424242",
                "ytick.color":       "#424242",
                "text.color":        "#212121",
                "legend.framealpha": 0.9,
                "legend.edgecolor":  "#BDBDBD",
                "font.size":         10,
                "figure.dpi":        100,
            })

    
    # Disposition
    

    
    # Slots
    

    def _on_config_changed(self, cfg: SimulationConfig):
        self._yield_panel.update_config(cfg)
        self._traj_panel.update_config(cfg)
        self._post_panel.update_config(cfg)
        self._runner_panel.update_config(cfg)
        target = cfg.target_layers[0].element if cfg.target_layers else "?"
        self._status_label.setText(
            f"Config mise à jour  |  "
            f"Ion : {cfg.ion.element} (Z={cfg.ion.Z})  •  "
            f"E = {cfg.ion.energy_eV:.0f} eV  •  "
            f"θ = {cfg.ion.angle_deg:.0f}°  •  "
            f"Cible : {target}  •  "
            f"{cfg.ion.num_ions:,} ions  •  "
            f"Potentiel : {cfg.physics.potential}"
        )

    def _on_simulation_done(self, cfg: SimulationConfig):
        self._status_label.setText("✓  Simulation terminée  –  Visualisations mises à jour.")
        self._mode_label.setText("TERMINÉE")
        self._mode_label.setStyleSheet(
            "background: #E8F5E9; color: #2E7D32; border-radius: 4px; "
            "padding: 2px 8px; font-size: 10px; font-weight: bold;"
        )
        self._yield_panel.update_config(cfg)
        self._traj_panel.update_config(cfg)
        self._post_panel.update_config(cfg)

    def _new_config(self):
        reply = QMessageBox.question(
            self, "Nouvelle configuration",
            "Réinitialiser tous les paramètres de simulation ?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._config_panel.config = SimulationConfig()
            self._config_panel._load_config_to_ui()
            self._status_label.setText("Nouvelle configuration  |  Paramètres réinitialisés.")

    def _go_to_runner(self):
        cfg = self._config_panel.collect_config()
        self._runner_panel.update_config(cfg)
        self._tabs.setCurrentWidget(self._runner_panel)

    def _show_about(self):
        QMessageBox.about(
            self, "À propos de CSiPI GUI",
            "<h2>CSiPI GUI &nbsp;<span style='font-size:14px; color:#9E9E9E;'>v1.0</span></h2>"
            "<p>Interface graphique pour le <b>Code de Simulation de la Pulvérisation Ionique</b> (CSiPI).</p>"
            "<p>Développée dans le cadre d'un stage à l'<b>ONERA</b> – DPHY/CSE, Toulouse.</p>"
            "<hr/><p><b>Technologies :</b> Python 3 · PyQt5 · Matplotlib · NumPy</p>"
            "<p><i>Responsable stage : Luca Chiabò (luca.chiabo@onera.fr)</i></p>",
        )

    def _show_bca_info(self):
        QMessageBox.information(
            self, "Principe BCA – Binary Collision Approximation",
            "<h3>Approximation des Collisions Binaires (BCA)</h3>"
            "<p>CSiPI repose sur le modèle BCA.</p>"
            "<p><b>Formule de Yamamura</b> : Y(E) = Q · S_n · (1 − √(E_th/E))² × f(θ)</p>"
            "<p><b>Loi de Thompson</b> : f(E) ∝ E / (E + E_s)³</p>",
        )



# Point d'entrée


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CSiPI GUI")
    app.setOrganizationName("ONERA")

    MainWindow._apply_light_palette(app)
    MainWindow._apply_matplotlib_style(dark=False)
    app.setStyleSheet(STYLE_LIGHT)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
