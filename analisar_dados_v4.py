import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
import joblib
import warnings
import matplotlib.pyplot as plt
import seaborn as sns

class AnalisadorInteligente:
    def __init__(self):
        self.diretorios = [
            Path('F:/okok/data'),
            Path('F:/okok'),
            Path('.'),
            Path('./data')
        ]
        
        self.arquivos = {
            'julio': '(JULIO) LISTAS INDIVIDUAIS.xlsx',
            'leandro': '(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx'
        }
        
        self.colunas_mapeamento = {
            'status': ['SITUACAO', 'STATUS', 'SITUAÇÃO', 'ESTADO'],
            'data': ['DATA', 'DATA_CONCLUSAO', 'DATA_INICIO', 'DT_CONCLUSAO'],
            'responsavel': ['RESPONSAVEL', 'COLABORADOR', 'NOME'],
            'prioridade': ['PRIORIDADE', 'URGENCIA', 'IMPORTANCIA'],
            'tipo': ['TIPO', 'CATEGORIA', 'CLASSIFICACAO']
        }
        
        # Status específicos solicitados
        self.status_especificos = [
            'VERIFICADO', 'ANÁLISE', 'PENDENTE', 'PRIORIDADE', 
            'APROVADO', 'QUITADO', 'CANCELADO'
        ]
        
        self.modelos = {}
        warnings.filterwarnings('ignore')
        
    def encontrar_diretorio(self):
        """Encontra o primeiro diretório válido"""
        for diretorio in self.diretorios:
            if diretorio.exists():
                return diretorio
        raise FileNotFoundError("Nenhum diretório válido encontrado")
    
    def carregar_dados(self):
        """Carrega dados de todos os arquivos Excel"""
        diretorio = self.encontrar_diretorio()
        print(f"Diretório de trabalho: {diretorio}")
        
        dados_grupos = {}
        
        for grupo, arquivo in self.arquivos.items():
            caminho = diretorio / arquivo
            if not caminho.exists():
                print(f"Arquivo não encontrado: {caminho}")
                continue
                
            print(f"\nCarregando dados do grupo {grupo}...")
            xls = pd.ExcelFile(caminho)
            abas = [aba for aba in xls.sheet_names if aba not in ["TESTE", "RELATÓRIO GERAL"]]
            
            dados_colaboradores = {}
            metricas_colaboradores = {}
            
            for aba in abas:
                try:
                    df = pd.read_excel(caminho, sheet_name=aba)
                    if df.empty:
                        continue
                    
                    df = self.normalizar_dataframe(df)
                    if df is not None:
                        dados_colaboradores[aba] = df
                        metricas = self.calcular_metricas(df, aba)
                        metricas_colaboradores[aba] = metricas
                        
                        # Mostrar contagem de status específicos
                        status_counts = self.contar_status_especificos(df)
                        status_str = ", ".join([f"{k}: {v}" for k, v in status_counts.items() if v > 0])
                        print(f"✓ {aba}: {len(df)} registros | {status_str}")
                except Exception as e:
                    print(f"✗ Erro ao processar {aba}: {str(e)}")
            
            dados_grupos[grupo] = {
                'colaboradores': dados_colaboradores,
                'metricas': metricas_colaboradores
            }
        
        return dados_grupos
    
    def normalizar_dataframe(self, df):
        """Normaliza e limpa o DataFrame"""
        # Normalizar nomes de colunas
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        # Encontrar coluna de status
        coluna_status = None
        for col in self.colunas_mapeamento['status']:
            if col in df.columns:
                coluna_status = col
                break
        
        if not coluna_status:
            return None
        
        # Padronizar coluna de status
        df = df.rename(columns={coluna_status: 'STATUS'})
        df['STATUS'] = df['STATUS'].fillna('NÃO INFORMADO')
        df['STATUS'] = df['STATUS'].astype(str).str.upper().str.strip()
        
        # Encontrar e normalizar coluna de data
        coluna_data = None
        for col in self.colunas_mapeamento['data']:
            if col in df.columns:
                coluna_data = col
                break
        
        if coluna_data:
            df = df.rename(columns={coluna_data: 'DATA'})
            df['DATA'] = pd.to_datetime(df['DATA'], errors='coerce')
            df['DIA'] = df['DATA'].dt.date
        
        # Encontrar coluna de prioridade
        coluna_prioridade = None
        for col in self.colunas_mapeamento['prioridade']:
            if col in df.columns:
                coluna_prioridade = col
                break
        
        if coluna_prioridade:
            df = df.rename(columns={coluna_prioridade: 'PRIORIDADE'})
        
        return df
    
    def contar_status_especificos(self, df):
        """Conta ocorrências dos status específicos"""
        status_counts = {}
        
        for status in self.status_especificos:
            count = df[df['STATUS'].str.contains(status, case=False, na=False)].shape[0]
            status_counts[status] = count
        
        # Adicionar total
        status_counts['TOTAL'] = len(df)
        
        return status_counts
    
    def calcular_metricas(self, df, colaborador):
        """Calcula métricas de desempenho para um colaborador"""
        metricas = {
            'colaborador': colaborador,
            'total_registros': len(df),
            'status_counts': self.contar_status_especificos(df),
            'taxa_conclusao': 0,
            'pendencias': 0,
            'tempo_medio': 0,
            'eficiencia': 0
        }
        
        # Calcular taxa de conclusão
        status_concluidos = ['APROVADO', 'QUITADO', 'VERIFICADO']
        concluidos = df[df['STATUS'].isin(status_concluidos)].shape[0]
        if metricas['total_registros'] > 0:
            metricas['taxa_conclusao'] = (concluidos / metricas['total_registros']) * 100
        
        # Calcular pendências
        metricas['pendencias'] = df[df['STATUS'] == 'PENDENTE'].shape[0]
        
        # Calcular tempo médio (se houver coluna de data)
        if 'DATA' in df.columns and 'DIA' in df.columns:
            # Verificar se há mais de um dia nos dados
            dias_unicos = df['DIA'].dropna().unique()
            if len(dias_unicos) > 1:
                primeiro_dia = min(dias_unicos)
                ultimo_dia = max(dias_unicos)
                dias_total = (ultimo_dia - primeiro_dia).days
                if dias_total > 0:
                    metricas['tempo_medio'] = concluidos / dias_total
        
        # Calcular eficiência (concluídos por dia)
        if 'DIA' in df.columns:
            dias_com_atividade = df.groupby('DIA')['STATUS'].count()
            if len(dias_com_atividade) > 0:
                metricas['eficiencia'] = concluidos / len(dias_com_atividade)
        
        return metricas
    
    def gerar_relatorio_diario(self, dados_grupos):
        """Gera relatório diário com contagem de status por dia"""
        print("\n=== Gerando Relatório Diário ===")
        
        relatorio_diario = {}
        
        for grupo, dados in dados_grupos.items():
            for colaborador, df in dados['colaboradores'].items():
                if 'DIA' not in df.columns:
                    continue
                
                # Agrupar por dia e contar status
                dias = df['DIA'].dropna().unique()
                
                for dia in dias:
                    df_dia = df[df['DIA'] == dia]
                    status_counts = self.contar_status_especificos(df_dia)
                    
                    dia_str = dia.strftime('%Y-%m-%d') if hasattr(dia, 'strftime') else str(dia)
                    chave = f"{grupo}_{colaborador}_{dia_str}"
                    
                    relatorio_diario[chave] = {
                        'grupo': grupo,
                        'colaborador': colaborador,
                        'dia': dia_str,
                        **status_counts
                    }
        
        # Converter para DataFrame
        if relatorio_diario:
            df_diario = pd.DataFrame(relatorio_diario).T
            
            # Salvar relatório
            diretorio = self.encontrar_diretorio()
            caminho_relatorio = diretorio / 'relatorio_diario.xlsx'
            df_diario.to_excel(caminho_relatorio)
            print(f"Relatório diário salvo em: {caminho_relatorio}")
            
            return df_diario
        else:
            print("Não foi possível gerar relatório diário (dados insuficientes)")
            return None
    
    def gerar_relatorio_geral(self, dados_grupos):
        """Gera relatório geral com totais por colaborador"""
        print("\n=== Gerando Relatório Geral ===")
        
        linhas = []
        
        for grupo, dados in dados_grupos.items():
            for colaborador, metricas in dados['metricas'].items():
                status_counts = metricas['status_counts']
                
                linha = {
                    'GRUPO': grupo,
                    'COLABORADOR': colaborador,
                    'VERIFICADO': status_counts.get('VERIFICADO', 0),
                    'ANÁLISE': status_counts.get('ANÁLISE', 0),
                    'PENDENTE': status_counts.get('PENDENTE', 0),
                    'PRIORIDADE': status_counts.get('PRIORIDADE', 0),
                    'APROVADO': status_counts.get('APROVADO', 0),
                    'QUITADO': status_counts.get('QUITADO', 0),
                    'CANCELADO': status_counts.get('CANCELADO', 0),
                    'TOTAL': status_counts.get('TOTAL', 0)
                }
                
                linhas.append(linha)
        
        # Criar DataFrame
        df_geral = pd.DataFrame(linhas)
        
        # Adicionar linha de totais
        totais = {
            'GRUPO': 'TOTAL',
            'COLABORADOR': 'GERAL'
        }
        
        for coluna in ['VERIFICADO', 'ANÁLISE', 'PENDENTE', 'PRIORIDADE', 
                       'APROVADO', 'QUITADO', 'CANCELADO', 'TOTAL']:
            totais[coluna] = df_geral[coluna].sum()
        
        df_geral = pd.concat([df_geral, pd.DataFrame([totais])], ignore_index=True)
        
        # Salvar relatório
        diretorio = self.encontrar_diretorio()
        caminho_relatorio = diretorio / 'relatorio_geral.xlsx'
        df_geral.to_excel(caminho_relatorio, index=False)
        print(f"Relatório geral salvo em: {caminho_relatorio}")
        
        # Exibir resumo
        print("\nResumo Geral:")
        for status in self.status_especificos + ['TOTAL']:
            print(f"{status}: {totais.get(status, 0)}")
        
        return df_geral
    
    def gerar_relatorio_produtividade_diaria(self, dados_grupos):
        """Gera relatório de produtividade diária por colaborador"""
        print("\n=== Gerando Relatório de Produtividade Diária ===")
        
        dados_produtividade = []
        
        for grupo, dados in dados_grupos.items():
            for colaborador, df in dados['colaboradores'].items():
                if 'DIA' not in df.columns:
                    continue
                
                # Agrupar por dia
                dias_produtividade = df.groupby('DIA').size().reset_index()
                dias_produtividade.columns = ['DIA', 'TOTAL']
                
                # Adicionar contagem por status
                for status in self.status_especificos:
                    dias_produtividade[status] = df[df['STATUS'].str.contains(status, case=False, na=False)].groupby('DIA').size().reindex(dias_produtividade['DIA']).fillna(0)
                
                # Adicionar informações do colaborador
                dias_produtividade['GRUPO'] = grupo
                dias_produtividade['COLABORADOR'] = colaborador
                
                dados_produtividade.append(dias_produtividade)
        
        if dados_produtividade:
            df_produtividade = pd.concat(dados_produtividade, ignore_index=True)
            
            # Ordenar por grupo, colaborador e dia
            df_produtividade = df_produtividade.sort_values(['GRUPO', 'COLABORADOR', 'DIA'])
            
            # Salvar relatório
            diretorio = self.encontrar_diretorio()
            caminho_relatorio = diretorio / 'produtividade_diaria.xlsx'
            df_produtividade.to_excel(caminho_relatorio, index=False)
            print(f"Relatório de produtividade diária salvo em: {caminho_relatorio}")
            
            return df_produtividade
        else:
            print("Não foi possível gerar relatório de produtividade (dados insuficientes)")
            return None
    
    def executar_analise_completa(self):
        """Executa o fluxo completo de análise"""
        print("=== Iniciando Análise Inteligente de Desempenho ===\n")
        
        # 1. Carregar dados
        dados_grupos = self.carregar_dados()
        
        # 2. Gerar relatório diário
        self.gerar_relatorio_diario(dados_grupos)
        
        # 3. Gerar relatório geral
        self.gerar_relatorio_geral(dados_grupos)
        
        # 4. Gerar relatório de produtividade diária
        self.gerar_relatorio_produtividade_diaria(dados_grupos)
        
        # 5. Gerar visualizações
        self.gerar_visualizacoes(dados_grupos)
        
        print("\n=== Análise Concluída com Sucesso ===")

    def gerar_visualizacoes(self, dados_grupos):
        """Gera visualizações para análise de desempenho"""
        try:
            # Preparar dados para visualização
            dados_viz = []
            
            for grupo, dados in dados_grupos.items():
                for colaborador, metricas in dados['metricas'].items():
                    status_counts = metricas['status_counts']
                    
                    for status in self.status_especificos:
                        dados_viz.append({
                            'GRUPO': grupo,
                            'COLABORADOR': colaborador,
                            'STATUS': status,
                            'QUANTIDADE': status_counts.get(status, 0)
                        })
            
            df_viz = pd.DataFrame(dados_viz)
            
            # Criar visualizações
            plt.figure(figsize=(15, 10))
            
            # Gráfico 1: Quantidade por status e colaborador
            plt.subplot(2, 1, 1)
            pivot = df_viz.pivot_table(
                index='COLABORADOR', 
                columns='STATUS', 
                values='QUANTIDADE',
                aggfunc='sum'
            ).fillna(0)
            
            ax = pivot.plot(kind='bar', stacked=True, ax=plt.gca())
            plt.title('Quantidade por Status e Colaborador')
            plt.ylabel('Quantidade')
            plt.xticks(rotation=45)
            plt.legend(title='Status')
            
            # Gráfico 2: Distribuição de status por grupo
            plt.subplot(2, 1, 2)
            grupo_status = df_viz.groupby(['GRUPO', 'STATUS'])['QUANTIDADE'].sum().reset_index()
            sns.barplot(x='STATUS', y='QUANTIDADE', hue='GRUPO', data=grupo_status)
            plt.title('Distribuição de Status por Grupo')
            plt.ylabel('Quantidade')
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # Salvar visualização
            diretorio = self.encontrar_diretorio()
            caminho_viz = diretorio / 'analise_status.png'
            plt.savefig(caminho_viz)
            print(f"\nVisualizações salvas em: {caminho_viz}")
            
        except Exception as e:
            print(f"Erro ao gerar visualizações: {str(e)}")

if __name__ == "__main__":
    try:
        analisador = AnalisadorInteligente()
        analisador.executar_analise_completa()
    except Exception as e:
        print(f"\nErro crítico: {str(e)}") 