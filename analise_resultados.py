import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
from collections import defaultdict

@dataclass
class ResultadoColaborador:
    nome: str
    data_referencia: str
    metricas: Dict[str, int]
    indicadores: Dict[str, float]

class AnalisadorResultados:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        
        # Mapeamento de colunas
        self.mapeamento_colunas = {
            'SITUAÇÃO': ['SITUAÇÃO', 'SITUACAO', 'STATUS'],
            'RESOLUÇÃO': ['RESOLUÇÃO', 'RESOLUCAO', 'DATA RESOLUCAO']
        }
        
        # Status válidos
        self.status_positivos = ['VERIFICADO', 'APROVADO', 'QUITADO']
        self.status_atencao = ['PRIORIDADE', 'PRIORIDADE TOTAL', 'ANÁLISE']
        self.status_negativos = ['PENDENTE', 'APREENDIDO', 'CANCELADO']

    def setup_logging(self):
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            filename=log_dir / f'analise_resultados_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        Path('reports').mkdir(exist_ok=True)

    def encontrar_coluna(self, colunas: List[str], opcoes: List[str]) -> str:
        """Encontra a coluna correta baseada em várias opções de nome"""
        for opcao in opcoes:
            if opcao in colunas:
                return opcao
        return None

    def converter_data_excel(self, valor) -> pd.Timestamp:
        """Converte valores de data do Excel para timestamp"""
        try:
            if isinstance(valor, (int, float)):
                # Converter número serial do Excel para datetime
                return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(valor))
            elif isinstance(valor, str):
                return pd.to_datetime(valor)
            elif isinstance(valor, pd.Timestamp):
                return valor
            return None
        except:
            return None

    def analisar_colaborador(self, dados: pd.DataFrame, nome: str) -> ResultadoColaborador:
        """Analisa resultados detalhados de um colaborador"""
        try:
            # Normalizar nomes das colunas
            dados.columns = [col.strip().upper() if isinstance(col, str) else col for col in dados.columns]
            
            # Encontrar coluna de situação
            coluna_situacao = self.encontrar_coluna(dados.columns, self.mapeamento_colunas['SITUAÇÃO'])
            coluna_resolucao = self.encontrar_coluna(dados.columns, self.mapeamento_colunas['RESOLUÇÃO'])
            
            if not coluna_situacao or not coluna_resolucao:
                raise ValueError(f"Colunas necessárias não encontradas. Disponíveis: {list(dados.columns)}")
            
            # Limpar e padronizar dados
            dados[coluna_situacao] = dados[coluna_situacao].astype(str).str.strip().str.upper()
            
            # Tratar datas
            dados[coluna_resolucao] = dados[coluna_resolucao].apply(self.converter_data_excel)
            
            # Obter contagem de status
            status_counts = dados[coluna_situacao].value_counts()
            
            # Métricas básicas
            metricas = defaultdict(int)
            for status in status_counts.index:
                metricas[status] = int(status_counts[status])
            
            total = sum(metricas.values())
            metricas['TOTAL'] = total
            
            # Calcular indicadores
            indicadores = {
                'taxa_resolucao': sum(metricas[status] for status in self.status_positivos) / total if total > 0 else 0,
                'taxa_pendencia': metricas['PENDENTE'] / total if total > 0 else 0,
                'taxa_prioridade': sum(metricas.get(status, 0) for status in self.status_atencao) / total if total > 0 else 0,
                'taxa_efetividade': (metricas.get('APROVADO', 0) + metricas.get('QUITADO', 0)) / total if total > 0 else 0
            }
            
            # Obter última data válida
            datas_validas = dados[coluna_resolucao].dropna()
            ultima_data = datas_validas.max() if not datas_validas.empty else pd.Timestamp.now()
            
            return ResultadoColaborador(
                nome=nome,
                data_referencia=ultima_data.strftime('%d/%m/%Y'),
                metricas=dict(metricas),  # Converter defaultdict para dict
                indicadores=indicadores
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar colaborador {nome}: {str(e)}")
            raise

    def gerar_relatorio_geral(self, resultados: List[ResultadoColaborador]) -> None:
        """Gera relatório detalhado dos resultados"""
        print("\n=== RELATÓRIO GERAL DE RESULTADOS ===")
        print(f"Data de referência: {resultados[0].data_referencia}\n")
        
        # Ordenar por taxa de efetividade
        resultados.sort(key=lambda x: x.indicadores['taxa_efetividade'], reverse=True)
        
        for resultado in resultados:
            print(f"\n{resultado.nome.upper()}")
            print("="*50)
            
            # Resultados positivos
            print("\nResultados Positivos:")
            for status in self.status_positivos:
                if status in resultado.metricas:
                    print(f"✓ {status}: {resultado.metricas[status]}")
            
            # Pendências e Prioridades
            print("\nPendências e Prioridades:")
            print(f"! Pendentes: {resultado.metricas.get('PENDENTE', 0)}")
            for status in self.status_atencao:
                if status in resultado.metricas:
                    print(f"! {status}: {resultado.metricas[status]}")
            
            # Indicadores
            print("\nIndicadores:")
            print(f"• Taxa de Resolução: {resultado.indicadores['taxa_resolucao']:.2%}")
            print(f"• Taxa de Efetividade: {resultado.indicadores['taxa_efetividade']:.2%}")
            print(f"• Taxa de Pendência: {resultado.indicadores['taxa_pendencia']:.2%}")
            
            # Total
            print(f"\nTotal de Contratos: {resultado.metricas['TOTAL']}")
            print("-"*50)

def main():
    try:
        analisador = AnalisadorResultados()
        arquivo = Path("data") / "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
        
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
            
        print(f"Analisando arquivo: {arquivo.name}")
        
        xls = pd.ExcelFile(arquivo)
        resultados = []
        
        for aba in xls.sheet_names:
            if aba in ['RELATÓRIO GERAL', 'TESTE', 'RESUMO']:
                continue
                
            try:
                dados = pd.read_excel(arquivo, sheet_name=aba)
                if not dados.empty:
                    resultado = analisador.analisar_colaborador(dados, aba)
                    resultados.append(resultado)
                    print(f"✓ Processado: {aba}")
            except Exception as e:
                print(f"Erro ao processar {aba}: {str(e)}")
        
        if resultados:
            analisador.gerar_relatorio_geral(resultados)
        
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    main() 