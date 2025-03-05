from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Criar diretório para o banco de dados
os.makedirs('data', exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/colaboradores.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Nova sintaxe do SQLAlchemy 2.0
Base = declarative_base()

# Modelos do banco de dados
class Colaborador(Base):
    __tablename__ = "colaboradores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    grupo = Column(String)  # JULIO ou LEANDRO
    score = Column(Float)
    taxa_preenchimento = Column(Float)
    taxa_padronizacao = Column(Float)
    consistencia = Column(Float)
    data_analise = Column(DateTime)
    metricas_detalhadas = Column(JSON)  # Armazena métricas adicionais em JSON

class RelatorioSemanal(Base):
    __tablename__ = "relatorios_semanais"

    id = Column(Integer, primary_key=True, index=True)
    semana = Column(Integer)
    ano = Column(Integer)
    data_geracao = Column(DateTime)
    dados_relatorio = Column(JSON)
    metricas_gerais = Column(JSON)

# Criar tabelas
Base.metadata.create_all(bind=engine) 