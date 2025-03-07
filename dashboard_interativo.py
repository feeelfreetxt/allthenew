import streamlit as st
st.set_page_config(
    page_title="Dashboard Interativo de Colaboradores",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict, Counter
import logging
from pathlib import Path
import traceback
import warnings

# Suprimir avisos específicos
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Configurar logging
logging.basicConfig(
    filename='dashboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Funções de utilidade com cache
@st.cache_data(ttl=3600)
def carregar_excel(caminho: str) -> tuple:
    """Carrega dados do Excel com cache"""
    caminho = Path(caminho)
    if not caminho.exists():
        st.warning(f"Arquivo não encontrado: {caminho}")
        return {}, []

    try:
        xls = pd.ExcelFile(str(caminho))
        abas_validas = [aba for aba in xls.sheet_names 
                       if aba and aba not in ["TESTE", "RELATÓRIO GERAL"]]
        
        dados_colaboradores = {}
        for aba in abas_validas:
            try:
                df = pd.read_excel(
                    caminho, 
                    sheet_name=aba,
                    parse_dates=True,
                    na_values=['NA', 'N/A', '']
                )
                
                if not df.empty:
                    # Normalização e limpeza
                    df.columns = [col.strip().upper().replace(' ', '_') if isinstance(col, str) else str(col) for col in df.columns]
                    
                    # Limpar dados
                    df = df.dropna(how='all')
                    if 'SITUACAO' in df.columns:
                        df['SITUACAO'] = df['SITUACAO'].fillna('NÃO INFORMADO')
                        df['SITUACAO'] = df['SITUACAO'].str.upper().str.strip()
                        dados_colaboradores[aba] = df
                        
                logging.info(f"Aba {aba} carregada: {len(df)} registros")
            except Exception as e:
                logging.error(f"Erro na aba {aba}: {str(e)}")
                continue
        
        return dados_colaboradores, list(dados_colaboradores.keys())
            
    except Exception as e:
        st.error(f"Erro ao carregar {caminho}: {str(e)}")
        logging.error(f"Erro ao carregar {caminho}: {str(e)}")
        return {}, []

@st.cache_data(ttl=3600)
def analisar_dados_colaborador(df: pd.DataFrame, nome: str) -> dict:
    """Analisa dados do colaborador"""
    if df is None or df.empty:
        return None
        
    try:
        analise = {
            'nome': nome,
            'total_registros': len(df),
            'eficiencia': 0,
            'situacao_counts': {},
            'situacao_percentual': {},
            'registros_vazios': 0
        }
        
        # Análise de situações
        situacoes = df['SITUACAO'].value_counts()
        total = len(df)
        
        analise['situacao_counts'] = situacoes.to_dict()
        analise['situacao_percentual'] = (situacoes / total * 100).to_dict()
        
        # Cálculo de eficiência
        if 'CONCLUIDO' in situacoes:
            analise['eficiencia'] = (situacoes['CONCLUIDO'] / total * 100)
            
        analise['registros_vazios'] = df['SITUACAO'].isna().sum()
        
        return analise
    except Exception as e:
        logging.error(f"Erro na análise do colaborador {nome}: {str(e)}")
        return None

class DashboardManager:
    def __init__(self):
        self.possiveis_diretorios = [
            Path('F:/okok/data'),
            Path('F:/okok'),
            Path('.'),
            Path('./data')
        ]
        
        self.nomes_arquivos = {
            'julio': '(JULIO) LISTAS INDIVIDUAIS.xlsx',
            'leandro': '(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx'
        }
        
        # Possíveis nomes para a coluna de situação
        self.colunas_situacao = [
            'SITUACAO', 'STATUS', 'SITUAÇÃO', 'ESTADO',
            'Status', 'Situacao', 'Situação', 'Estado'
        ]
        
        self.arquivos = self.localizar_arquivos()

    def encontrar_coluna_situacao(self, colunas):
        """Identifica a coluna de situação nas colunas disponíveis"""
        colunas = [str(col).strip().upper() for col in colunas]
        for possivel_nome in self.colunas_situacao:
            if possivel_nome.upper() in colunas:
                return possivel_nome
        return None

    def normalizar_dados(self, df):
        """Normaliza os dados do DataFrame"""
        # Normalizar nomes das colunas
        df.columns = [str(col).strip().upper() for col in df.columns]
        
        # Encontrar coluna de situação
        coluna_situacao = self.encontrar_coluna_situacao(df.columns)
        if coluna_situacao:
            # Renomear para padrão
            df = df.rename(columns={coluna_situacao: 'SITUACAO'})
            
            # Normalizar valores da situação
            df['SITUACAO'] = df['SITUACAO'].fillna('NÃO INFORMADO')
            df['SITUACAO'] = df['SITUACAO'].astype(str).str.upper().str.strip()
            
            # Padronizar valores comuns
            mapeamento_situacao = {
                'CONCLUÍDO': 'CONCLUIDO',
                'CONCLUIDA': 'CONCLUIDO',
                'CONCLUÍDO': 'CONCLUIDO',
                'FINALIZADO': 'CONCLUIDO',
                'EM ANDAMENTO': 'EM_ANDAMENTO',
                'ANDAMENTO': 'EM_ANDAMENTO',
                'PENDENTE': 'PENDENTE',
                'AGUARDANDO': 'PENDENTE',
                'NÃO INICIADO': 'PENDENTE'
            }
            df['SITUACAO'] = df['SITUACAO'].replace(mapeamento_situacao)
            
        return df, bool(coluna_situacao)

    def verificar_estrutura_arquivo(self, caminho: str) -> bool:
        """Verifica e normaliza a estrutura do arquivo"""
        try:
            xls = pd.ExcelFile(caminho)
            abas_validas = [aba for aba in xls.sheet_names 
                           if aba not in ["TESTE", "RELATÓRIO GERAL"]]
            
            dados_validos = False
            for aba in abas_validas:
                try:
                    df = pd.read_excel(caminho, sheet_name=aba)
                    if df.empty:
                        continue
                        
                    df, tem_situacao = self.normalizar_dados(df)
                    if tem_situacao:
                        dados_validos = True
                    else:
                        st.warning(f"Aba {aba}: Coluna de situação não encontrada. Procurando por: {', '.join(self.colunas_situacao)}")
                        
                except Exception as e:
                    st.warning(f"Erro ao processar aba {aba}: {str(e)}")
                    continue
                    
            return dados_validos
            
        except Exception as e:
            st.error(f"Erro ao verificar arquivo {caminho}: {str(e)}")
            return False

    @st.cache_data(ttl=3600)
    def carregar_excel(self, caminho: str) -> tuple:
        """Carrega dados do Excel com normalização"""
        if not Path(caminho).exists():
            return {}, []
            
        try:
            xls = pd.ExcelFile(caminho)
            abas_validas = [aba for aba in xls.sheet_names 
                           if aba not in ["TESTE", "RELATÓRIO GERAL"]]
            
            dados_colaboradores = {}
            for aba in abas_validas:
                try:
                    df = pd.read_excel(caminho, sheet_name=aba)
                    if df.empty:
                        continue
                        
                    df, tem_situacao = self.normalizar_dados(df)
                    if tem_situacao:
                        dados_colaboradores[aba] = df
                        st.success(f"✓ Aba {aba}: {len(df)} registros carregados")
                        
                except Exception as e:
                    st.warning(f"Erro ao processar aba {aba}: {str(e)}")
                    continue
                    
            return dados_colaboradores, list(dados_colaboradores.keys())
            
        except Exception as e:
            st.error(f"Erro ao carregar {caminho}: {str(e)}")
            return {}, []

    def localizar_arquivos(self) -> dict:
        """Localiza os arquivos Excel em vários diretórios possíveis"""
        arquivos_encontrados = {}
        
        # Procurar em cada diretório possível
        for diretorio in self.possiveis_diretorios:
            st.sidebar.write(f"Procurando em: {diretorio}")
            
            if not diretorio.exists():
                continue
                
            for tipo, nome in self.nomes_arquivos.items():
                caminho = diretorio / nome
                if caminho.exists():
                    arquivos_encontrados[tipo] = str(caminho)
                    st.sidebar.success(f"✓ Arquivo {tipo} encontrado em: {caminho}")
                    
        if not arquivos_encontrados:
            st.error("Nenhum arquivo Excel encontrado!")
            st.info("""
            Arquivos necessários:
            1. (JULIO) LISTAS INDIVIDUAIS.xlsx
            2. (LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx
            
            Diretórios verificados:
            {}
            """.format('\n'.join(f"- {d}" for d in self.possiveis_diretorios)))
            
        return arquivos_encontrados

    def iniciar_dashboard(self):
        """Inicia o dashboard"""
        st.title("Dashboard Interativo de Colaboradores")
        st.write(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        # Carregar dados
        with st.spinner('Carregando dados...'):
            dados_julio, colaboradores_julio = self.carregar_excel(
                self.arquivos.get('julio', '')
            )
            dados_leandro, colaboradores_leandro = self.carregar_excel(
                self.arquivos.get('leandro', '')
            )

        # Verificar se há dados
        if not dados_julio and not dados_leandro:
            st.error("Nenhum dado válido encontrado.")
            st.info("""
            Verifique se:
            1. Os arquivos têm pelo menos uma das seguintes colunas:
               - SITUACAO, STATUS, SITUAÇÃO, ESTADO
            2. As abas contêm dados válidos
            3. Os valores de situação estão preenchidos
            """)
            return

        # Mostrar resumo dos dados
        with st.expander("Resumo dos Dados", expanded=True):
            total_registros = 0
            if dados_julio:
                st.write("### Grupo Julio")
                for colaborador, df in dados_julio.items():
                    registros = len(df)
                    total_registros += registros
                    st.write(f"- {colaborador}: {registros} registros")
                    
            if dados_leandro:
                st.write("### Grupo Leandro")
                for colaborador, df in dados_leandro.items():
                    registros = len(df)
                    total_registros += registros
                    st.write(f"- {colaborador}: {registros} registros")
                    
            st.info(f"Total de registros: {total_registros}")

        # Função para exibir dashboard de um colaborador
        def exibir_dashboard_colaborador(analise, grupo):
            if not analise:
                return
            
            # Criar card para o colaborador
            with st.container():
                st.subheader(f"{analise['nome']} ({grupo})")
                
                # Métricas principais
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Volume Total", analise['total_registros'])
                with col2:
                    st.metric("Taxa de Eficiência", f"{analise['eficiencia']:.1f}%")
                
                # Distribuição de Status
                if analise['situacao_counts']:
                    st.write("### Distribuição de Status")
                    
                    # Criar DataFrame para o gráfico
                    df_situacao = pd.DataFrame({
                        'Status': list(analise['situacao_counts'].keys()),
                        'Quantidade': list(analise['situacao_counts'].values()),
                        'Percentual': [f"{analise['situacao_percentual'].get(k, 0):.1f}%" for k in analise['situacao_counts'].keys()]
                    })
                    
                    # Exibir tabela
                    st.dataframe(df_situacao, hide_index=True)
                    
                    # Criar gráfico de pizza
                    fig = px.pie(
                        df_situacao, 
                        values='Quantidade', 
                        names='Status', 
                        title=f"Distribuição de Status - {analise['nome']}",
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Análise Temporal
                if analise['analise_temporal']:
                    st.write("### Análise Temporal")
                    
                    for col_data, dados in analise['analise_temporal'].items():
                        if 'erro' in dados:
                            st.warning(f"Erro na análise da coluna {col_data}: {dados['erro']}")
                            continue
                        
                        st.write(f"#### Coluna: {col_data}")
                        
                        if 'periodo' in dados:
                            periodo = dados['periodo']
                            st.write(f"Período: {periodo['min']} a {periodo['max']}")
                            st.write(f"Registros com data: {periodo['registros']} ({periodo['percentual']:.1f}%)")
                        
                        # Transições de Estado
                        if dados.get('transicoes'):
                            st.write("##### Transições de Estado mais comuns:")
                            
                            # Criar DataFrame para as transições
                            transicoes_list = [(f"{de} -> {para}", count) for (de, para), count in dados['transicoes'].items()]
                            transicoes_list.sort(key=lambda x: x[1], reverse=True)
                            
                            if transicoes_list:
                                df_transicoes = pd.DataFrame(transicoes_list[:5], columns=['Transição', 'Ocorrências'])
                                st.dataframe(df_transicoes, hide_index=True)
                        
                        # Tempo médio em cada situação
                        if dados.get('tempos_por_situacao'):
                            st.write("##### Tempo Médio em cada Situação (dias):")
                            
                            # Criar DataFrame para os tempos
                            tempos_list = [(situacao, tempo) for situacao, tempo in dados['tempos_por_situacao'].items()]
                            tempos_list.sort(key=lambda x: x[1], reverse=True)
                            
                            if tempos_list:
                                df_tempos = pd.DataFrame(tempos_list, columns=['Situação', 'Tempo Médio (dias)'])
                                st.dataframe(df_tempos, hide_index=True)
                                
                                # Criar gráfico de barras
                                fig = px.bar(
                                    df_tempos, 
                                    x='Situação', 
                                    y='Tempo Médio (dias)', 
                                    title=f"Tempo Médio em cada Situação - {analise['nome']}",
                                    color='Tempo Médio (dias)'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                
                # Valores não padronizados
                if analise['valores_nao_padronizados']:
                    st.warning(f"Valores não padronizados encontrados: {', '.join(analise['valores_nao_padronizados'])}")
                
                # Registros vazios
                if analise['registros_vazios'] > 0:
                    st.warning(f"Registros com SITUACAO vazia: {analise['registros_vazios']} ({analise['registros_vazios']/analise['total_registros']*100:.1f}%)")

        # Função para exibir comparação entre colaboradores
        def exibir_comparacao_colaboradores(todas_analises):
            if not todas_analises:
                return
            
            st.header("Comparação entre Colaboradores")
            
            # Preparar dados para comparação
            dados_comparacao = []
            for grupo, analises in todas_analises.items():
                for nome, analise in analises.items():
                    dados_comparacao.append({
                        'Grupo': grupo,
                        'Nome': nome,
                        'Volume Total': analise['total_registros'],
                        'Taxa de Eficiência (%)': analise['eficiencia']
                    })
            
            # Criar DataFrame para comparação
            df_comparacao = pd.DataFrame(dados_comparacao)
            
            # Exibir tabela de comparação
            st.dataframe(df_comparacao, hide_index=True)
            
            # Gráfico de barras para volume total
            fig_volume = px.bar(
                df_comparacao, 
                x='Nome', 
                y='Volume Total', 
                color='Grupo',
                title="Volume Total por Colaborador",
                barmode='group'
            )
            st.plotly_chart(fig_volume, use_container_width=True)
            
            # Gráfico de barras para taxa de eficiência
            fig_eficiencia = px.bar(
                df_comparacao, 
                x='Nome', 
                y='Taxa de Eficiência (%)', 
                color='Grupo',
                title="Taxa de Eficiência por Colaborador",
                barmode='group'
            )
            st.plotly_chart(fig_eficiencia, use_container_width=True)

        # Opções de visualização
        opcao_visualizacao = st.sidebar.radio(
            "Tipo de Visualização",
            ["Colaborador Específico", "Todos os Colaboradores", "Comparação entre Colaboradores"]
        )

        # Variáveis para armazenar análises
        todas_analises = {
            "Grupo Julio": {},
            "Grupo Leandro": {}
        }

        # Visualização de colaborador específico
        if opcao_visualizacao == "Colaborador Específico":
            grupo = st.sidebar.radio("Selecione o Grupo", ["Grupo Julio", "Grupo Leandro"])
            
            if grupo == "Grupo Julio":
                colaborador = st.sidebar.selectbox("Selecione o Colaborador", colaboradores_julio)
                if colaborador:
                    df = dados_julio.get(colaborador)
                    analise = analisar_dados_colaborador(df, colaborador)
                    exibir_dashboard_colaborador(analise, "Grupo Julio")
                    todas_analises["Grupo Julio"][colaborador] = analise
            else:
                colaborador = st.sidebar.selectbox("Selecione o Colaborador", colaboradores_leandro)
                if colaborador:
                    df = dados_leandro.get(colaborador)
                    analise = analisar_dados_colaborador(df, colaborador)
                    exibir_dashboard_colaborador(analise, "Grupo Leandro")
                    todas_analises["Grupo Leandro"][colaborador] = analise

        # Visualização de todos os colaboradores
        elif opcao_visualizacao == "Todos os Colaboradores":
            grupo = st.sidebar.radio("Selecione o Grupo", ["Grupo Julio", "Grupo Leandro", "Ambos os Grupos"])
            
            if grupo in ["Grupo Julio", "Ambos os Grupos"]:
                st.header("Grupo Julio")
                for colaborador in colaboradores_julio:
                    df = dados_julio.get(colaborador)
                    analise = analisar_dados_colaborador(df, colaborador)
                    exibir_dashboard_colaborador(analise, "Grupo Julio")
                    todas_analises["Grupo Julio"][colaborador] = analise
                    st.markdown("---")
            
            if grupo in ["Grupo Leandro", "Ambos os Grupos"]:
                st.header("Grupo Leandro")
                for colaborador in colaboradores_leandro:
                    df = dados_leandro.get(colaborador)
                    analise = analisar_dados_colaborador(df, colaborador)
                    exibir_dashboard_colaborador(analise, "Grupo Leandro")
                    todas_analises["Grupo Leandro"][colaborador] = analise
                    st.markdown("---")

        # Comparação entre colaboradores
        elif opcao_visualizacao == "Comparação entre Colaboradores":
            # Analisar todos os colaboradores
            for colaborador in colaboradores_julio:
                df = dados_julio.get(colaborador)
                analise = analisar_dados_colaborador(df, colaborador)
                todas_analises["Grupo Julio"][colaborador] = analise
            
            for colaborador in colaboradores_leandro:
                df = dados_leandro.get(colaborador)
                analise = analisar_dados_colaborador(df, colaborador)
                todas_analises["Grupo Leandro"][colaborador] = analise
            
            # Exibir comparação
            exibir_comparacao_colaboradores(todas_analises)

        # Rodapé
        st.sidebar.markdown("---")
        st.sidebar.info("Dashboard desenvolvido para análise de dados dos colaboradores")
        st.sidebar.write(f"Total de colaboradores: {len(colaboradores_julio) + len(colaboradores_leandro)}")

if __name__ == "__main__":
    try:
        dashboard = DashboardManager()
        dashboard.iniciar_dashboard()
    except Exception as e:
        st.error(f"Erro ao iniciar o dashboard: {str(e)}")
        logging.error(f"Erro ao iniciar o dashboard: {str(e)}\n{traceback.format_exc()}")
