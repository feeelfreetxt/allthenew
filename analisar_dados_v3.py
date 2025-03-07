import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import warnings
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='analise.log'
)

@dataclass
class MetricasColaborador:
    """Classe para armazenar métricas de um colaborador"""
    total_registros: int = 0
    concluidos: int = 0
    pendentes: int = 0
    em_andamento: int = 0
    eficiencia: float = 0.0
    tempo_medio_conclusao: float = 0.0
    
class AnalisadorModerno:
    def __init__(self):
        self.diretorio = self._encontrar_diretorio()
        self.config = self._carregar_config()
        
    def _encontrar_diretorio(self) -> Path:
        """Localiza o diretório com os arquivos"""
        diretorios = [
            Path('F:/okok/data'),
            Path('F:/okok'),
            Path('.')
        ]
        
        for dir in diretorios:
            if dir.exists() and any(dir.glob("*.xlsx")):
                logging.info(f"Diretório de trabalho: {dir}")
                return dir
        raise FileNotFoundError("Nenhum diretório válido encontrado")

    def _carregar_config(self) -> dict:
        """Carrega ou cria configurações"""
        return {
            'arquivos': {
                'julio': '(JULIO) LISTAS INDIVIDUAIS.xlsx',
                'leandro': '(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx'
            },
            'colunas_mapeamento': {
                'status': ['SITUACAO', 'STATUS', 'SITUAÇÃO', 'ESTADO'],
                'data': ['DATA', 'DATA_CONCLUSAO', 'DT_CONCLUSAO'],
                'responsavel': ['RESPONSAVEL', 'COLABORADOR', 'NOME']
            },
            'valores_mapeamento': {
                'CONCLUÍDO': 'CONCLUIDO',
                'CONCLUIDA': 'CONCLUIDO',
                'FINALIZADO': 'CONCLUIDO',
                'EM ANDAMENTO': 'EM_ANDAMENTO',
                'ANDAMENTO': 'EM_ANDAMENTO',
                'PENDENTE': 'PENDENTE',
                'AGUARDANDO': 'PENDENTE'
            }
        }

    def _processar_aba(self, arquivo: Path, aba: str) -> Optional[Tuple[str, MetricasColaborador]]:
        """Processa uma aba do Excel"""
        try:
            df = pd.read_excel(arquivo, sheet_name=aba)
            if df.empty:
                return None

            # Normalizar colunas
            df.columns = [str(col).strip().upper() for col in df.columns]
            
            # Encontrar coluna de status
            coluna_status = next((col for col in df.columns 
                                if col in self.config['colunas_mapeamento']['status']), None)
            
            if not coluna_status:
                return None

            # Processar dados
            df['STATUS'] = (df[coluna_status]
                          .fillna('PENDENTE')
                          .str.upper()
                          .str.strip()
                          .replace(self.config['valores_mapeamento']))

            # Calcular métricas
            metricas = MetricasColaborador()
            metricas.total_registros = len(df)
            metricas.concluidos = (df['STATUS'] == 'CONCLUIDO').sum()
            metricas.pendentes = (df['STATUS'] == 'PENDENTE').sum()
            metricas.em_andamento = (df['STATUS'] == 'EM_ANDAMENTO').sum()
            
            if metricas.total_registros > 0:
                metricas.eficiencia = (metricas.concluidos / metricas.total_registros) * 100

            return aba, metricas

        except Exception as e:
            logging.error(f"Erro ao processar aba {aba}: {str(e)}")
            return None

    def analisar_arquivo(self, nome: str, arquivo: Path) -> dict:
        """Analisa um arquivo Excel completo"""
        try:
            logging.info(f"Analisando {nome}...")
            
            # Listar abas válidas
            xls = pd.ExcelFile(arquivo)
            abas = [aba for aba in xls.sheet_names 
                   if aba not in ["TESTE", "RELATÓRIO GERAL"]]

            resultados = {}
            
            # Processar abas em paralelo
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self._processar_aba, arquivo, aba)
                    for aba in abas
                ]
                
                for future in futures:
                    resultado = future.result()
                    if resultado:
                        aba, metricas = resultado
                        resultados[aba] = asdict(metricas)
                        
                        # Log formatado
                        print(f"\n{aba}:")
                        print(f"├─ Registros: {metricas.total_registros}")
                        print(f"├─ Concluídos: {metricas.concluidos}")
                        print(f"├─ Pendentes: {metricas.pendentes}")
                        print(f"└─ Eficiência: {metricas.eficiencia:.1f}%")

            return resultados

        except Exception as e:
            logging.error(f"Erro ao analisar arquivo {nome}: {str(e)}")
            return {}

    def gerar_relatorio(self):
        """Gera relatório de análise"""
        print("\n=== Iniciando Análise de Dados ===\n")
        
        relatorio = {
            'data_analise': datetime.now().isoformat(),
            'diretorio': str(self.diretorio),
            'grupos': {}
        }

        # Analisar cada arquivo
        for nome, arquivo in self.config['arquivos'].items():
            caminho = self.diretorio / arquivo
            if not caminho.exists():
                print(f"Arquivo não encontrado: {arquivo}")
                continue

            resultados = self.analisar_arquivo(nome, caminho)
            if resultados:
                relatorio['grupos'][nome] = resultados
                
                # Calcular métricas do grupo
                total_registros = sum(r['total_registros'] for r in resultados.values())
                total_concluidos = sum(r['concluidos'] for r in resultados.values())
                eficiencia_media = np.mean([r['eficiencia'] for r in resultados.values()])
                
                print(f"\n=== Resumo do Grupo {nome.title()} ===")
                print(f"Total de Colaboradores: {len(resultados)}")
                print(f"Total de Registros: {total_registros}")
                print(f"Total Concluídos: {total_concluidos}")
                print(f"Eficiência Média: {eficiencia_media:.1f}%")

        # Salvar relatório
        arquivo_saida = self.diretorio / 'analise_detalhada.json'
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
            print(f"\nRelatório detalhado salvo em: {arquivo_saida}")

if __name__ == "__main__":
    try:
        analisador = AnalisadorModerno()
        analisador.gerar_relatorio()
        print("\n=== Análise Concluída com Sucesso ===")
    except Exception as e:
        logging.error(f"Erro crítico: {str(e)}")
        print(f"\nErro crítico: {str(e)}")
        print("Consulte analise.log para mais detalhes") 