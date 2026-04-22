"""
Modèle de données pour la configuration d'une simulation CSiPI.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json


# Tables de masses atomiques et numéros atomiques simplifiées (éléments courants)
ELEMENTS = {
    "H":  {"Z": 1,  "mass": 1.008},
    "He": {"Z": 2,  "mass": 4.003},
    "C":  {"Z": 6,  "mass": 12.011},
    "N":  {"Z": 7,  "mass": 14.007},
    "O":  {"Z": 8,  "mass": 15.999},
    "Ne": {"Z": 10, "mass": 20.180},
    "Al": {"Z": 13, "mass": 26.982},
    "Si": {"Z": 14, "mass": 28.086},
    "Ar": {"Z": 18, "mass": 39.948},
    "Ti": {"Z": 22, "mass": 47.867},
    "Cr": {"Z": 24, "mass": 51.996},
    "Fe": {"Z": 26, "mass": 55.845},
    "Co": {"Z": 27, "mass": 58.933},
    "Ni": {"Z": 28, "mass": 58.693},
    "Cu": {"Z": 29, "mass": 63.546},
    "Mo": {"Z": 42, "mass": 95.96},
    "Ag": {"Z": 47, "mass": 107.868},
    "W":  {"Z": 74, "mass": 183.84},
    "Au": {"Z": 79, "mass": 196.967},
    "Xe": {"Z": 54, "mass": 131.293},
    "Kr": {"Z": 36, "mass": 83.798},
}

INTERATOMIC_POTENTIALS = [
    "ZBL",
    "Moliere",
    "Lenz-Jensen",
    "Kr-C",
    "Nakagawa-Yamamura",
]

SURFACE_BINDING_MODELS = [
    "Planar",
    "Element-specific",
    "None",
]


@dataclass
class IonParameters:
    element: str = "Xe"
    energy_eV: float = 800.0
    angle_deg: float = 0.0       # angle d'incidence par rapport à la normale
    num_ions: int = 10000

    @property
    def Z(self) -> int:
        return ELEMENTS.get(self.element, {}).get("Z", 1)

    @property
    def mass_amu(self) -> float:
        return ELEMENTS.get(self.element, {}).get("mass", 1.0)


@dataclass
class TargetLayer:
    element: str = "Mo"
    fraction: float = 1.0        # fraction atomique (0–1)
    thickness_nm: float = 100.0  # épaisseur en nm (inf = bulk)
    bulk: bool = True

    @property
    def Z(self) -> int:
        return ELEMENTS.get(self.element, {}).get("Z", 1)

    @property
    def mass_amu(self) -> float:
        return ELEMENTS.get(self.element, {}).get("mass", 1.0)


@dataclass
class PhysicsParameters:
    potential: str = "ZBL"
    surface_binding_model: str = "Planar"
    displacement_energy_eV: float = 25.0
    cutoff_energy_eV: float = 1.0
    track_recoils: bool = True
    calculate_trajectories: bool = False
    max_depth_nm: float = 500.0


@dataclass
class OutputOptions:
    save_yield: bool = True
    save_trajectories: bool = False
    save_angular_distribution: bool = True
    save_energy_distribution: bool = True
    output_directory: str = "./output"
    output_prefix: str = "csipI_result"
    num_bins_angle: int = 90
    num_bins_energy: int = 100


@dataclass
class SimulationConfig:
    ion: IonParameters = field(default_factory=IonParameters)
    target_layers: list = field(default_factory=lambda: [TargetLayer()])
    physics: PhysicsParameters = field(default_factory=PhysicsParameters)
    output: OutputOptions = field(default_factory=OutputOptions)

    def to_dict(self) -> dict:
        return {
            "ion": asdict(self.ion),
            "target_layers": [asdict(l) for l in self.target_layers],
            "physics": asdict(self.physics),
            "output": asdict(self.output),
        }

    def to_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "SimulationConfig":
        cfg = cls()
        if "ion" in d:
            cfg.ion = IonParameters(**d["ion"])
        if "target_layers" in d:
            cfg.target_layers = [TargetLayer(**l) for l in d["target_layers"]]
        if "physics" in d:
            cfg.physics = PhysicsParameters(**d["physics"])
        if "output" in d:
            cfg.output = OutputOptions(**d["output"])
        return cfg

    @classmethod
    def from_json(cls, path: str) -> "SimulationConfig":
        with open(path) as f:
            return cls.from_dict(json.load(f))

    def to_csipI_input(self) -> str:
        """Génère le fichier d'entrée texte au format CSiPI."""
        lines = [
            "# CSiPI Input File – généré par la GUI",
            f"ION_ELEMENT    {self.ion.element}",
            f"ION_Z          {self.ion.Z}",
            f"ION_MASS       {self.ion.mass_amu:.4f}",
            f"ION_ENERGY     {self.ion.energy_eV:.2f}",
            f"ION_ANGLE      {self.ion.angle_deg:.2f}",
            f"NUM_IONS       {self.ion.num_ions}",
            "",
            "# Target",
        ]
        for i, layer in enumerate(self.target_layers):
            lines.append(f"LAYER_{i+1}_ELEMENT    {layer.element}")
            lines.append(f"LAYER_{i+1}_Z          {layer.Z}")
            lines.append(f"LAYER_{i+1}_MASS       {layer.mass_amu:.4f}")
            lines.append(f"LAYER_{i+1}_FRACTION   {layer.fraction:.4f}")
            if layer.bulk:
                lines.append(f"LAYER_{i+1}_THICKNESS  INF")
            else:
                lines.append(f"LAYER_{i+1}_THICKNESS  {layer.thickness_nm:.2f}")
        lines += [
            "",
            "# Physics",
            f"POTENTIAL             {self.physics.potential}",
            f"SURFACE_BINDING       {self.physics.surface_binding_model}",
            f"DISPLACEMENT_ENERGY   {self.physics.displacement_energy_eV:.2f}",
            f"CUTOFF_ENERGY         {self.physics.cutoff_energy_eV:.4f}",
            f"TRACK_RECOILS         {'yes' if self.physics.track_recoils else 'no'}",
            f"CALC_TRAJECTORIES     {'yes' if self.physics.calculate_trajectories else 'no'}",
            f"MAX_DEPTH             {self.physics.max_depth_nm:.2f}",
            "",
            "# Output",
            f"OUTPUT_DIR            {self.output.output_directory}",
            f"OUTPUT_PREFIX         {self.output.output_prefix}",
            f"SAVE_YIELD            {'yes' if self.output.save_yield else 'no'}",
            f"SAVE_TRAJECTORIES     {'yes' if self.output.save_trajectories else 'no'}",
            f"SAVE_ANGULAR_DIST     {'yes' if self.output.save_angular_distribution else 'no'}",
            f"SAVE_ENERGY_DIST      {'yes' if self.output.save_energy_distribution else 'no'}",
            f"BINS_ANGLE            {self.output.num_bins_angle}",
            f"BINS_ENERGY           {self.output.num_bins_energy}",
        ]
        return "\n".join(lines)
