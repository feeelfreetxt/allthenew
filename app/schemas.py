from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Dict, Any

class ColaboradorBase(BaseModel):
    nome: str
    grupo: str
    score: float
    taxa_preenchimento: float
    taxa_padronizacao: float
    consistencia: float

class ColaboradorCreate(ColaboradorBase):
    id: int
    data_analise: datetime
    metricas_detalhadas: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class RelatorioBase(BaseModel):
    semana: int
    ano: int
    data_geracao: datetime

class RelatorioCreate(RelatorioBase):
    id: int
    dados_relatorio: Dict[str, Any]
    metricas_gerais: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True) 