import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging
from dataclasses import dataclass
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
        
        # Definir categorias de status
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

    def analisar_colaborador(self, dados: pd.DataFrame, nome: str) -> ResultadoColaborador:
        """Analisa resultados detalhados de um colaborador"""
        try:
            # Obter contagem de status
            status_counts = dados['SITUAÇÃO'].value_counts()
            
            # Métricas básicas
            metricas = {
                'VERIFICADO': int(status_counts.get('VERIFICADO', 0)),
                'ANÁLISE': int(status_counts.get('ANÁLISE', 0)),
                'PENDENTE': int(status_counts.get('PENDENTE', 0)),
                'PRIORIDADE': int(status_counts.get('PRIORIDADE', 0)),
                'PRIORIDADE TOTAL': int(status_counts.get('PRIORIDADE TOTAL', 0)),
                'APROVADO': int(status_counts.get('APROVADO', 0)),
                'QUITADO': int(status_counts.get('QUITADO', 0)),
                'APREENDIDO': int(status_counts.get('APREENDIDO', 0)),
                'CANCELADO': int(status_counts.get('CANCELADO', 0))
            }
            
            total = sum(metricas.values())
            metricas['TOTAL'] = total
            
            # Calcular indicadores
            indicadores = {
                'taxa_resolucao': sum(metricas[status] for status in self.status_positivos) / total if total > 0 else 0,
                'taxa_pendencia': metricas['PENDENTE'] / total if total > 0 else 0,
                'taxa_prioridade': sum(metricas[status] for status in self.status_atencao) / total if total > 0 else 0,
                'taxa_efetividade': (metricas['APROVADO'] + metricas['QUITADO']) / total if total > 0 else 0
            }
            
            # Obter última data de resolução
            ultima_data = dados['RESOLUÇÃO'].max()
            
            return ResultadoColaborador(
                nome=nome,
                data_referencia=ultima_data.strftime('%d/%m/%Y'),
                metricas=metricas,
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
            print(f"✓ Verificados: {resultado.metricas['VERIFICADO']}")
            print(f"✓ Aprovados: {resultado.metricas['APROVADO']}")
            print(f"✓ Quitados: {resultado.metricas['QUITADO']}")
            
            # Pendências e Prioridades
            print("\nPendências e Prioridades:")
            print(f"! Pendentes: {resultado.metricas['PENDENTE']}")
            print(f"! Prioridade: {resultado.metricas['PRIORIDADE']}")
            print(f"! Análise: {resultado.metricas['ANÁLISE']}")
            
            # Outros status
            print("\nOutros Status:")
            print(f"- Apreendidos: {resultado.metricas['APREENDIDO']}")
            print(f"- Cancelados: {resultado.metricas['CANCELADO']}")
            
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