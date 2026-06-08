from dataclasses import dataclass

@dataclass(frozen=True)
class Vehicle:
    """
    Representa um veículo de entrega na frota hospitalar.
    """
    id: int
    name: str
    capacity: float  # Capacidade máxima de carga (ex: kg ou unidades)
    autonomy: float  # Distância máxima que o veículo pode percorrer
