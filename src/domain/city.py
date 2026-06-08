from dataclasses import dataclass
from typing import Tuple
from enum import IntEnum

class Priority(IntEnum):
    REGULAR = 1
    URGENT = 2
    CRITICAL = 3

@dataclass(frozen=True)
class City:
    """
    Representa um hospital ou unidade de saúde no problema de roteamento.
    Contém coordenadas geográficas, demanda de insumos e nível de prioridade.
    """
    id: int
    name: str
    x: float
    y: float
    demand: float = 1.0  # Demanda de carga (padrão 1.0)
    priority: Priority = Priority.REGULAR

    @property
    def coordinates(self) -> Tuple[float, float]:
        return (self.x, self.y)
