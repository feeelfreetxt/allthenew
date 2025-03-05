import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime
from pathlib import Path
import warnings
from typing import Dict, List, Any

class AnalisadorEficiencia:
    def __init__(self):
        # Configurar logging
        self.setup_logging()
        
        # Criar diretórios necessários
        self.setup_directories()
        
        # Inicializar modelo
        self.model = None
        self.scaler = StandardScaler()
        
        # Métricas para análise
        self.metricas_importantes = [
            'tempo_medio_resolucao',
            'taxa_sucesso',
            'taxa_pendencia',
            'total_contratos',
            'contratos_prioritarios',
            'tempo_medio_aprovacao'
        ]

    def setup_logging(self):
        """Configura o sistema de logging"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / f'analise_eficiencia_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Cria diretórios necessários"""
        Path('models').mkdir(exist_ok=True)
        Path('reports').mkdir(exist_ok=True)
        Path('data').mkdir(exist_ok=True)

    def calcular_metricas_colaborador(self, dados: pd.DataFrame) -> Dict[str, float]:
        """Calcula métricas de eficiência para um colaborador"""
        try:
            if dados.empty:
                raise ValueError("DataFrame está vazio")

            # Mapeamento de nomes alternativos para as colunas
            mapeamento_colunas = {
                'DATA': ['DATA', 'DT', 'DATA_', 'DATA CADASTRO'],
                'RESOLUCAO': ['RESOLUÇÃO', 'RESOLUCAO', 'RESOL', 'DT_RESOLUCAO'],
                'SITUACAO': ['SITUAÇÃO', 'SITUACAO', 'STATUS']
            }

            # Normalizar nomes das colunas
            dados.columns = [col.strip().upper() for col in dados.columns]
            
            # Encontrar e renomear colunas
            colunas_encontradas = {}
            for col_padrao, alternativas in mapeamento_colunas.items():
                for alt in alternativas:
                    if alt.upper() in dados.columns:
                        colunas_encontradas[col_padrao] = alt.upper()
                        dados = dados.rename(columns={alt.upper(): col_padrao})
                        break
            
            # Verificar colunas necessárias
            colunas_faltantes = [col for col in mapeamento_colunas.keys() 
                               if col not in colunas_encontradas]
            
            if colunas_faltantes:
                self.logger.error(f"Colunas não encontradas: {colunas_faltantes}")
                self.logger.info(f"Colunas disponíveis: {list(dados.columns)}")
                raise ValueError(f"Colunas faltantes: {', '.join(colunas_faltantes)}")

            metricas = {}
            
            # Tempo médio de resolução
            dados['DATA'] = pd.to_datetime(dados['DATA'], errors='coerce')
            dados['RESOLUCAO'] = pd.to_datetime(dados['RESOLUCAO'], errors='coerce')
            
            # Remover linhas com datas inválidas
            dados = dados.dropna(subset=['DATA', 'RESOLUCAO'])
            
            if dados.empty:
                raise ValueError("Não há dados válidos após limpeza de datas")

            tempo_resolucao = (dados['RESOLUCAO'] - dados['DATA']).dt.days
            metricas['tempo_medio_resolucao'] = tempo_resolucao.mean()
            
            # Taxa de sucesso
            status_sucesso = ['QUITADO', 'APROVADO']
            total = len(dados)
            sucesso = len(dados[dados['SITUACAO'].isin(status_sucesso)])
            metricas['taxa_sucesso'] = sucesso / total if total > 0 else 0
            
            # Taxa de pendência
            pendentes = len(dados[dados['SITUACAO'] == 'PENDENTE'])
            metricas['taxa_pendencia'] = pendentes / total if total > 0 else 0
            
            # Total de contratos
            metricas['total_contratos'] = total
            
            # Contratos prioritários
            prioritarios = len(dados[dados['SITUACAO'] == 'PRIORIDADE'])
            metricas['contratos_prioritarios'] = prioritarios
            
            # Tempo médio até aprovação
            dados_aprovados = dados[dados['SITUACAO'] == 'APROVADO']
            if not dados_aprovados.empty:
                tempo_aprovacao = (dados_aprovados['RESOLUCAO'] - dados_aprovados['DATA']).dt.days
                metricas['tempo_medio_aprovacao'] = tempo_aprovacao.mean()
            else:
                metricas['tempo_medio_aprovacao'] = 0
            
            return metricas
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular métricas: {str(e)}")
            raise ValueError(f"Erro ao calcular métricas: {str(e)}")

    def avaliar_eficiencia(self, dados: pd.DataFrame) -> Dict[str, Any]:
        """Avalia a eficiência de um colaborador"""
        try:
            # Calcular métricas
            metricas = self.calcular_metricas_colaborador(dados)
            if not metricas:
                return {'status': 'erro', 'mensagem': 'Erro ao calcular métricas'}
            
            # Gerar recomendações
            recomendacoes = self.gerar_recomendacoes(metricas)
            
            # Calcular score de eficiência
            score = self.calcular_score_eficiencia(metricas)
            
            return {
                'status': 'sucesso',
                'eficiencia': 'Alta' if score > 0.7 else 'Baixa',
                'score': score,
                'metricas': metricas,
                'recomendacoes': recomendacoes
            }
            
        except Exception as e:
            self.logger.error(f"Erro na avaliação de eficiência: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

    def calcular_score_eficiencia(self, metricas: Dict[str, float]) -> float:
        """Calcula um score de eficiência baseado nas métricas"""
        try:
            # Pesos para cada métrica
            pesos = {
                'taxa_sucesso': 0.4,
                'tempo_medio_resolucao': 0.3,
                'taxa_pendencia': 0.2,
                'contratos_prioritarios': 0.1
            }
            
            score = (
                metricas['taxa_sucesso'] * pesos['taxa_sucesso'] +
                (1 / (1 + metricas['tempo_medio_resolucao']/30)) * pesos['tempo_medio_resolucao'] +
                (1 - metricas['taxa_pendencia']) * pesos['taxa_pendencia'] +
                (metricas['contratos_prioritarios'] / metricas['total_contratos']) * pesos['contratos_prioritarios']
            )
            
            return min(max(score, 0), 1)  # Normalizar entre 0 e 1
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular score: {str(e)}")
            return 0.0

    def gerar_recomendacoes(self, metricas: Dict[str, float]) -> List[str]:
        """Gera recomendações baseadas nas métricas"""
        recomendacoes = []
        
        if metricas['tempo_medio_resolucao'] > 15:
            recomendacoes.append(
                "Reduzir tempo médio de resolução. Considerar priorização de casos."
            )
        
        if metricas['taxa_sucesso'] < 0.6:
            recomendacoes.append(
                "Melhorar taxa de sucesso. Revisar estratégias de negociação."
            )
        
        if metricas['taxa_pendencia'] > 0.3:
            recomendacoes.append(
                "Alto número de pendências. Focar em resolução de casos pendentes."
            )
        
        if metricas['contratos_prioritarios'] > metricas['total_contratos'] * 0.2:
            recomendacoes.append(
                "Muitos casos prioritários. Necessária atenção especial."
            )
        
        return recomendacoes

    def calcular_metricas_avancadas(self, dados: pd.DataFrame) -> Dict[str, Any]:
        """Calcula métricas avançadas com foco na última resolução"""
        try:
            metricas = {}
            
            # Converter datas corretamente
            dados['DATA'] = pd.to_datetime(dados['DATA'], errors='coerce')
            dados['RESOLUÇÃO'] = pd.to_datetime(dados['RESOLUÇÃO'], errors='coerce')
            
            # Última data de resolução (negociação efetiva)
            ultima_resolucao = dados['RESOLUÇÃO'].max()
            
            # Filtrar dados recentes (últimos 30 dias baseado na RESOLUÇÃO)
            dados_recentes = dados[dados['RESOLUÇÃO'] >= (ultima_resolucao - pd.Timedelta(days=30))]
            
            # Status importantes
            status_positivos = ['QUITADO', 'APROVADO', 'VERIFICADO']
            
            # Análise de status atual
            status_counts = dados['SITUAÇÃO'].value_counts()
            total_contratos = len(dados)
            
            metricas.update({
                'ultima_resolucao': ultima_resolucao.strftime('%d/%m/%Y'),
                'total_contratos': total_contratos,
                'contratos_recentes': len(dados_recentes),
                'status': {
                    'pendentes': int(status_counts.get('PENDENTE', 0)),
                    'aprovados': int(status_counts.get('APROVADO', 0)),
                    'quitados': int(status_counts.get('QUITADO', 0)),
                    'verificados': int(status_counts.get('VERIFICADO', 0))
                }
            })
            
            # Calcular eficiência
            total_resolvidos = sum(status_counts.get(status, 0) for status in status_positivos)
            metricas['eficiencia'] = {
                'taxa_resolucao': total_resolvidos / total_contratos if total_contratos > 0 else 0,
                'taxa_pendencia': metricas['status']['pendentes'] / total_contratos if total_contratos > 0 else 0
            }
            
            # Análise de velocidade
            if not dados_recentes.empty:
                tempo_medio_recente = (dados_recentes['RESOLUÇÃO'] - dados_recentes['DATA']).dt.days.mean()
                metricas['velocidade'] = {
                    'tempo_medio_recente': tempo_medio_recente,
                    'resolucoes_recentes': len(dados_recentes),
                    'taxa_sucesso_recente': len(dados_recentes[dados_recentes['SITUAÇÃO'].isin(status_positivos)]) / len(dados_recentes)
                }
            
            return metricas
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular métricas avançadas: {str(e)}")
            return None

    def gerar_relatorio_detalhado(self, resultados: Dict[str, Any]) -> None:
        """Gera relatório focado em eficiência recente"""
        print("\n=== ANÁLISE DE EFICIÊNCIA POR COLABORADOR ===\n")
        
        print("TOP 5 COLABORADORES MAIS EFICIENTES:\n")
        for i, colab in enumerate(resultados['melhores'], 1):
            metricas = colab['metricas_avancadas']
            print(f"{i}. {colab['nome'].upper()}")
            print(f"   Última resolução: {metricas['ultima_resolucao']}")
            print(f"   Contratos ativos: {metricas['total_contratos']}")
            print("\n   Status atual:")
            print(f"   - Resolvidos (Aprovados/Quitados/Verificados): {sum([metricas['status'][k] for k in ['aprovados', 'quitados', 'verificados']])}")
            print(f"   - Pendentes: {metricas['status']['pendentes']}")
            print(f"   Taxa de resolução: {metricas['eficiencia']['taxa_resolucao']:.2%}")
            
            if 'velocidade' in metricas:
                print("\n   Desempenho recente (30 dias):")
                print(f"   - Resoluções: {metricas['velocidade']['resolucoes_recentes']}")
                print(f"   - Tempo médio: {metricas['velocidade']['tempo_medio_recente']:.1f} dias")
                print(f"   - Taxa de sucesso: {metricas['velocidade']['taxa_sucesso_recente']:.2%}")
            print("\n   " + "="*50)

    def analisar_colaboradores(self, arquivo: Path) -> Dict[str, Any]:
        """Analisa colaboradores com foco em resolução"""
        try:
            print(f"\nAnalisando arquivo: {arquivo.name}")
            
            resultados = {
                'melhores': [],
                'status': 'sucesso'
            }
            
            xls = pd.ExcelFile(arquivo)
            colaboradores = []
            
            for aba in xls.sheet_names:
                if aba in ['RELATÓRIO GERAL', 'TESTE', 'RESUMO']:
                    continue
                    
                try:
                    dados = pd.read_excel(arquivo, sheet_name=aba)
                    
                    if not dados.empty:
                        metricas_avancadas = self.calcular_metricas_avancadas(dados)
                        
                        if metricas_avancadas:
                            colaborador = {
                                'nome': aba,
                                'metricas_avancadas': metricas_avancadas
                            }
                            colaboradores.append(colaborador)
                except Exception as e:
                    self.logger.error(f"Erro ao processar {aba}: {str(e)}")
            
            # Ordenar por eficiência e data recente
            colaboradores.sort(key=lambda x: (
                x['metricas_avancadas']['eficiencia']['taxa_resolucao'],
                x['metricas_avancadas']['ultima_resolucao'],
                -x['metricas_avancadas']['status']['pendentes']
            ), reverse=True)
            
            resultados['melhores'] = colaboradores[:5]
            return resultados
            
        except Exception as e:
            self.logger.error(f"Erro na análise: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}

def main():
    try:
        analisador = AnalisadorEficiencia()
        arquivo = Path("data") / "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
        
        if not arquivo.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        
        resultados = analisador.analisar_colaboradores(arquivo)
        if resultados['status'] == 'sucesso':
            analisador.gerar_relatorio_detalhado(resultados)
        else:
            print(f"Erro: {resultados['mensagem']}")
            
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    main() 