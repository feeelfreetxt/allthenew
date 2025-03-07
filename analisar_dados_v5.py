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
import jinja2
import base64
from io import BytesIO

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
        
        # Status prioritários (mais importantes)
        self.status_prioritarios = ['APROVADO', 'QUITADO']
        
        # Horas de trabalho por dia
        self.horas_trabalho = 8
        
        self.modelos = {}
        warnings.filterwarnings('ignore')
        
    def calcular_metricas_avancadas(self, dados_grupos):
        """Calcula métricas avançadas de produtividade e eficiência"""
        metricas_avancadas = []
        
        for grupo, dados in dados_grupos.items():
            for colaborador, df in dados['colaboradores'].items():
                if df.empty:
                    continue
                
                # Contagem de status
                status_counts = self.contar_status_especificos(df)
                
                # Calcular métricas de produtividade
                total_registros = len(df)
                total_prioritarios = sum(status_counts.get(status, 0) for status in self.status_prioritarios)
                taxa_prioritarios = (total_prioritarios / total_registros * 100) if total_registros > 0 else 0
                
                # Calcular produtividade por hora
                dias_unicos = len(df['DIA'].unique()) if 'DIA' in df.columns else 1
                horas_totais = dias_unicos * self.horas_trabalho
                produtividade_hora = total_registros / horas_totais if horas_totais > 0 else 0
                produtividade_prioritarios = total_prioritarios / horas_totais if horas_totais > 0 else 0
                
                # Calcular tempo médio para aprovação/quitação
                tempo_medio = 0
                if 'TEMPO_PROCESSAMENTO' in df.columns:
                    df_concluidos = df[df['STATUS'].isin(self.status_prioritarios)]
                    if not df_concluidos.empty:
                        tempo_medio = df_concluidos['TEMPO_PROCESSAMENTO'].mean()
                
                # Adicionar métricas
                metricas_avancadas.append({
                    'grupo': grupo,
                    'colaborador': colaborador,
                    'total_registros': total_registros,
                    'aprovados': status_counts.get('APROVADO', 0),
                    'quitados': status_counts.get('QUITADO', 0),
                    'pendentes': status_counts.get('PENDENTE', 0),
                    'taxa_prioritarios': taxa_prioritarios,
                    'produtividade_hora': produtividade_hora,
                    'produtividade_prioritarios': produtividade_prioritarios,
                    'tempo_medio_dias': tempo_medio,
                    'score_eficiencia': (taxa_prioritarios * 0.4 + 
                                        produtividade_hora * 0.3 + 
                                        produtividade_prioritarios * 0.3)
                })
        
        return pd.DataFrame(metricas_avancadas)
    
    def gerar_ranking_colaboradores(self, df_metricas):
        """Gera ranking de colaboradores baseado em eficiência"""
        if df_metricas.empty:
            return pd.DataFrame()
        
        # Ordenar por score de eficiência
        df_ranking = df_metricas.sort_values('score_eficiencia', ascending=False).reset_index(drop=True)
        df_ranking['ranking'] = df_ranking.index + 1
        
        # Calcular percentil
        df_ranking['percentil'] = df_ranking['score_eficiencia'].rank(pct=True) * 100
        
        return df_ranking
    
    def identificar_melhores_praticas(self, df_metricas, dados_grupos):
        """Identifica as melhores práticas dos colaboradores mais eficientes"""
        if df_metricas.empty:
            return []
        
        # Selecionar top 3 colaboradores
        top_colaboradores = df_metricas.nlargest(3, 'score_eficiencia')
        
        melhores_praticas = []
        
        for _, row in top_colaboradores.iterrows():
            grupo = row['grupo']
            colaborador = row['colaborador']
            
            # Obter dados do colaborador
            df = dados_grupos[grupo]['colaboradores'].get(colaborador)
            if df is None or df.empty:
                continue
            
            # Analisar padrões de sucesso
            # 1. Distribuição por dia da semana
            if 'DIA' in df.columns:
                df['DIA_SEMANA'] = df['DIA'].dt.day_name()
                dias_produtivos = df[df['STATUS'].isin(self.status_prioritarios)]['DIA_SEMANA'].value_counts()
                if not dias_produtivos.empty:
                    melhor_dia = dias_produtivos.idxmax()
                    melhores_praticas.append(f"O colaborador {colaborador} tem melhor desempenho às {melhor_dia}s")
            
            # 2. Verificar se há padrão de horário (se houver coluna de hora)
            hora_cols = [col for col in df.columns if 'HORA' in col]
            if hora_cols:
                df_hora = df[df['STATUS'].isin(self.status_prioritarios)]
                if not df_hora.empty and hora_cols[0] in df_hora.columns:
                    df_hora['HORA'] = pd.to_datetime(df_hora[hora_cols[0]]).dt.hour
                    horas_produtivas = df_hora['HORA'].value_counts()
                    if not horas_produtivas.empty:
                        melhor_hora = horas_produtivas.idxmax()
                        melhores_praticas.append(f"O colaborador {colaborador} é mais produtivo por volta das {melhor_hora}h")
            
            # 3. Verificar tipos de contratos com maior taxa de sucesso
            tipo_cols = [col for col in df.columns if any(tipo in col.upper() for tipo in ['TIPO', 'CATEGORIA'])]
            if tipo_cols:
                df_tipos = df[df['STATUS'].isin(self.status_prioritarios)]
                if not df_tipos.empty and tipo_cols[0] in df_tipos.columns:
                    tipos_sucesso = df_tipos[tipo_cols[0]].value_counts()
                    if not tipos_sucesso.empty:
                        melhor_tipo = tipos_sucesso.idxmax()
                        melhores_praticas.append(f"O colaborador {colaborador} tem maior sucesso com contratos do tipo '{melhor_tipo}'")
        
        return melhores_praticas
    
    def gerar_recomendacoes_estrategicas(self, df_metricas, dados_grupos):
        """Gera recomendações estratégicas para melhorar a produtividade"""
        if df_metricas.empty:
            return []
        
        recomendacoes = []
        
        # 1. Identificar colaboradores com baixa produtividade
        baixa_produtividade = df_metricas[df_metricas['produtividade_hora'] < df_metricas['produtividade_hora'].median()]
        if not baixa_produtividade.empty:
            recomendacoes.append("Oferecer treinamento adicional para colaboradores com produtividade abaixo da média")
        
        # 2. Identificar colaboradores com alta taxa de pendências
        alta_pendencia = df_metricas[df_metricas['pendentes'] > df_metricas['pendentes'].median() * 1.5]
        if not alta_pendencia.empty:
            recomendacoes.append("Redistribuir contratos pendentes de colaboradores sobrecarregados")
        
        # 3. Identificar grupos com melhor desempenho
        desempenho_grupos = df_metricas.groupby('grupo')['score_eficiencia'].mean()
        if not desempenho_grupos.empty:
            melhor_grupo = desempenho_grupos.idxmax()
            recomendacoes.append(f"Adotar práticas do grupo {melhor_grupo} que apresenta melhor eficiência média")
        
        # 4. Analisar tempo médio de processamento
        if 'tempo_medio_dias' in df_metricas.columns:
            tempo_medio = df_metricas['tempo_medio_dias'].mean()
            if tempo_medio > 5:  # Se tempo médio > 5 dias
                recomendacoes.append(f"Implementar processo de acompanhamento diário para reduzir tempo médio de {tempo_medio:.1f} dias")
        
        # 5. Recomendações baseadas em padrões de dados
        todos_dados = pd.DataFrame()
        for grupo, dados in dados_grupos.items():
            for colaborador, df in dados['colaboradores'].items():
                if not df.empty:
                    df['GRUPO'] = grupo
                    df['COLABORADOR'] = colaborador
                    todos_dados = pd.concat([todos_dados, df])
        
        if not todos_dados.empty:
            # Verificar horários mais produtivos
            if 'HORA' in todos_dados.columns:
                todos_dados['HORA'] = pd.to_datetime(todos_dados['HORA']).dt.hour
                horas_produtivas = todos_dados[todos_dados['STATUS'].isin(self.status_prioritarios)]['HORA'].value_counts()
                if not horas_produtivas.empty:
                    melhores_horas = horas_produtivas.nlargest(2).index.tolist()
                    recomendacoes.append(f"Concentrar esforços de negociação nos horários mais produtivos: {melhores_horas[0]}h e {melhores_horas[1]}h")
            
            # Verificar dias mais produtivos
            if 'DIA' in todos_dados.columns:
                todos_dados['DIA_SEMANA'] = todos_dados['DIA'].dt.day_name()
                dias_produtivos = todos_dados[todos_dados['STATUS'].isin(self.status_prioritarios)]['DIA_SEMANA'].value_counts()
                if not dias_produtivos.empty:
                    melhor_dia = dias_produtivos.idxmax()
                    recomendacoes.append(f"Priorizar negociações complexas às {melhor_dia}s, dia com maior taxa de sucesso")
        
        return recomendacoes
    
    def gerar_html_responsivo(self, df_metricas, melhores_praticas, recomendacoes):
        """Gera relatório HTML responsivo com ranking e recomendações"""
        if df_metricas.empty:
            return "Não há dados suficientes para gerar o relatório."
        
        # Gerar gráficos para incluir no HTML
        plt.figure(figsize=(10, 6))
        sns.barplot(x='colaborador', y='score_eficiencia', hue='grupo', data=df_metricas)
        plt.title('Score de Eficiência por Colaborador')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Converter gráfico para base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        # Gerar gráfico de aprovados e quitados
        plt.figure(figsize=(10, 6))
        df_plot = df_metricas.melt(
            id_vars=['colaborador', 'grupo'],
            value_vars=['aprovados', 'quitados'],
            var_name='status',
            value_name='quantidade'
        )
        sns.barplot(x='colaborador', y='quantidade', hue='status', data=df_plot)
        plt.title('Contratos Aprovados e Quitados por Colaborador')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Converter segundo gráfico para base64
        buffer2 = BytesIO()
        plt.savefig(buffer2, format='png')
        buffer2.seek(0)
        img_str2 = base64.b64encode(buffer2.read()).decode('utf-8')
        plt.close()
        
        # Calcular métricas por grupo
        metricas_grupo = df_metricas.groupby('grupo').agg({
            'aprovados': 'sum',
            'quitados': 'sum',
            'pendentes': 'sum',
            'score_eficiencia': 'mean',
            'produtividade_hora': 'mean'
        }).reset_index()
        
        # Determinar grupo líder
        grupo_lider = metricas_grupo.loc[metricas_grupo['score_eficiencia'].idxmax(), 'grupo']
        
        # Preparar dados para o template
        ranking_data = df_metricas.to_dict('records')
        grupo_data = metricas_grupo.to_dict('records')
        
        # Template HTML com Bootstrap para responsividade
        template = """
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ranking de Eficiência - Análise de Contratos</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
                .card { margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .progress { height: 20px; }
                .table-responsive { margin-bottom: 30px; }
                .badge-success { background-color: #28a745; }
                .badge-warning { background-color: #ffc107; }
                .badge-danger { background-color: #dc3545; }
                .top-performer { background-color: #d4edda; }
                .low-performer { background-color: #f8d7da; }
                .chart-container { margin-bottom: 30px; }
                .recommendations { background-color: #f8f9fa; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container mt-4">
                <h1 class="text-center mb-4">Análise de Eficiência em Contratos</h1>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-primary text-white">
                                <h5 class="mb-0">Grupo Líder: {{ grupo_lider }}</h5>
                            </div>
                            <div class="card-body">
                                <p>O grupo <strong>{{ grupo_lider }}</strong> apresenta a melhor eficiência média na aprovação e quitação de contratos.</p>
                                
                                <h6>Métricas por Grupo:</h6>
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Grupo</th>
                                            <th>Aprovados</th>
                                            <th>Quitados</th>
                                            <th>Eficiência</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for grupo in grupos %}
                                        <tr {% if grupo.grupo == grupo_lider %}class="table-success"{% endif %}>
                                            <td>{{ grupo.grupo }}</td>
                                            <td>{{ grupo.aprovados }}</td>
                                            <td>{{ grupo.quitados }}</td>
                                            <td>{{ "%.1f"|format(grupo.score_eficiencia) }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h5 class="mb-0">Melhores Práticas Identificadas</h5>
                            </div>
                            <div class="card-body">
                                <ul class="list-group">
                                    {% for pratica in melhores_praticas %}
                                    <li class="list-group-item">{{ pratica }}</li>
                                    {% endfor %}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header bg-dark text-white">
                                <h5 class="mb-0">Ranking de Colaboradores</h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped table-hover">
                                        <thead>
                                            <tr>
                                                <th>#</th>
                                                <th>Colaborador</th>
                                                <th>Grupo</th>
                                                <th>Aprovados</th>
                                                <th>Quitados</th>
                                                <th>Pendentes</th>
                                                <th>Prod./Hora</th>
                                                <th>Score</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for colab in ranking %}
                                            <tr {% if loop.index <= 3 %}class="top-performer"{% elif loop.index > (ranking|length - 3) %}class="low-performer"{% endif %}>
                                                <td>{{ loop.index }}</td>
                                                <td>{{ colab.colaborador }}</td>
                                                <td>{{ colab.grupo }}</td>
                                                <td>{{ colab.aprovados }}</td>
                                                <td>{{ colab.quitados }}</td>
                                                <td>{{ colab.pendentes }}</td>
                                                <td>{{ "%.2f"|format(colab.produtividade_hora) }}</td>
                                                <td>
                                                    <div class="progress">
                                                        <div class="progress-bar bg-success" role="progressbar" 
                                                             style="width: {{ colab.percentil }}%;" 
                                                             aria-valuenow="{{ colab.percentil }}" aria-valuemin="0" aria-valuemax="100">
                                                            {{ "%.1f"|format(colab.score_eficiencia) }}
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="chart-container">
                            <h5>Eficiência por Colaborador</h5>
                            <img src="data:image/png;base64,{{ img_eficiencia }}" class="img-fluid" alt="Gráfico de Eficiência">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="chart-container">
                            <h5>Contratos Aprovados e Quitados</h5>
                            <img src="data:image/png;base64,{{ img_contratos }}" class="img-fluid" alt="Gráfico de Contratos">
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4 mb-5">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header bg-info text-white">
                                <h5 class="mb-0">Recomendações Estratégicas</h5>
                            </div>
                            <div class="card-body recommendations">
                                <ol>
                                    {% for rec in recomendacoes %}
                                    <li class="mb-2">{{ rec }}</li>
                                    {% endfor %}
                                </ol>
                                
                                <div class="alert alert-warning mt-3">
                                    <h6 class="alert-heading">Estratégia para 8 horas de trabalho:</h6>
                                    <p>Para maximizar a produtividade durante o dia de trabalho, recomenda-se:</p>
                                    <ul>
                                        <li>Primeira hora: Revisar contratos pendentes e planejar o dia</li>
                                        <li>Segunda e terceira horas: Focar em negociações de alta prioridade</li>
                                        <li>Quarta hora: Revisar e aprovar contratos já negociados</li>
                                        <li>Após o almoço: Concentrar em novos contratos</li>
                                        <li>Últimas duas horas: Finalizar aprovações e quitações pendentes</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <footer class="text-center text-muted mb-4">
                    <small>Relatório gerado em {{ data_geracao }}</small>
                </footer>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
        """
        
        # Renderizar template
        env = jinja2.Environment()
        template_renderizado = env.from_string(template).render(
            ranking=ranking_data,
            grupos=grupo_data,
            grupo_lider=grupo_lider,
            melhores_praticas=melhores_praticas,
            recomendacoes=recomendacoes,
            img_eficiencia=img_str,
            img_contratos=img_str2,
            data_geracao=datetime.now().strftime('%d/%m/%Y %H:%M')
        )
        
        return template_renderizado
    
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
        
        # 5. Calcular métricas avançadas
        df_metricas = self.calcular_metricas_avancadas(dados_grupos)
        
        # 6. Gerar ranking de colaboradores
        df_ranking = self.gerar_ranking_colaboradores(df_metricas)
        
        # 7. Identificar melhores práticas
        melhores_praticas = self.identificar_melhores_praticas(df_ranking, dados_grupos)
        
        # 8. Gerar recomendações estratégicas
        recomendacoes = self.gerar_recomendacoes_estrategicas(df_ranking, dados_grupos)
        
        # 9. Gerar relatório HTML
        html_report = self.gerar_html_responsivo(df_ranking, melhores_praticas, recomendacoes)
        
        # 10. Salvar relatório HTML
        diretorio = self.encontrar_diretorio()
        caminho_html = diretorio / 'ranking_eficiencia.html'
        with open(caminho_html, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # 11. Gerar visualizações
        self.gerar_visualizacoes(dados_grupos)
        
        print(f"\nRelatório de ranking e estratégias salvo em: {caminho_html}")
        print("\n=== Análise Concluída com Sucesso ===")

    def encontrar_diretorio(self):
        """Encontra o primeiro diretório válido"""
        for diretorio in self.diretorios:
            if diretorio.exists():
                return diretorio
        raise FileNotFoundError("Nenhum diretório válido encontrado")

    def carregar_dados(self):
        """Carrega e normaliza dados dos arquivos Excel"""
        diretorio = self.encontrar_diretorio()
        print(f"Diretório de trabalho: {diretorio}")
        
        dados_grupos = {}
        
        for grupo, arquivo in self.arquivos.items():
            caminho = diretorio / arquivo
            if not caminho.exists():
                print(f"Arquivo não encontrado: {caminho}")
                continue
            
            print(f"\nCarregando dados do grupo {grupo}...")
            try:
                xls = pd.ExcelFile(caminho)
                abas = [aba for aba in xls.sheet_names if aba not in ["TESTE", "RELATÓRIO GERAL"]]
                
                dados_colaboradores = {}
                metricas_colaboradores = {}
                
                # Processamento das abas
                for aba in abas:
                    try:
                        df = pd.read_excel(
                            caminho, 
                            sheet_name=aba,
                            parse_dates=True
                        )
                        
                        if df.empty:
                            continue
                        
                        # Normalizar colunas
                        df.columns = [self.normalizar_valor(col) for col in df.columns]
                        
                        # Identificar coluna de status
                        col_status = next((col for col in df.columns if any(s in col for s in ['SITUACAO', 'STATUS', 'SITUAÇÃO'])), None)
                        
                        if col_status:
                            df = df.rename(columns={col_status: 'STATUS'})
                            df['STATUS'] = df['STATUS'].fillna('PENDENTE').str.upper().str.strip()
                            
                            # Mapear status
                            mapeamento_status = {
                                'VERIFICADO': 'VERIFICADO',
                                'ANÁLISE': 'ANÁLISE',
                                'ANALISE': 'ANÁLISE',
                                'PENDENTE': 'PENDENTE',
                                'APROVADO': 'APROVADO',
                                'QUITADO': 'QUITADO',
                                'CANCELADO': 'CANCELADO'
                            }
                            df['STATUS'] = df['STATUS'].map(lambda x: mapeamento_status.get(x, x))
                            
                            # Adicionar data de processamento
                            df['DIA'] = pd.to_datetime('today').date()
                            
                            dados_colaboradores[aba] = df
                            
                            # Calcular métricas básicas
                            status_counts = df['STATUS'].value_counts().to_dict()
                            
                            # Calcular métricas diárias
                            metricas_diarias = {
                                'VERIFICADO': 0,
                                'ANÁLISE': 0,
                                'PENDENTE': 0,
                                'PRIORIDADE': 0,
                                'APROVADO': 0,
                                'QUITADO': 0,
                                'CANCELADO': 0
                            }
                            metricas_diarias.update(status_counts)
                            
                            metricas_colaboradores[aba] = {
                                'total_registros': len(df),
                                'status_counts': status_counts,
                                'metricas_diarias': metricas_diarias,
                                'produtividade_hora': len(df) / self.horas_trabalho
                            }
                            
                            # Mostrar contagem de status
                            print(f"✓ {aba}: {len(df)} registros")
                            print("  Status:")
                            for status, count in metricas_diarias.items():
                                print(f"    {status}: {count}")
                              
                    except Exception as e:
                        print(f"✗ Erro ao processar {aba}: {str(e)}")
                        continue
                
                dados_grupos[grupo] = {
                    'colaboradores': dados_colaboradores,
                    'metricas': metricas_colaboradores
                }
                
            except Exception as e:
                print(f"Erro ao processar arquivo {arquivo}: {str(e)}")
                continue
        
        return dados_grupos

    def normalizar_valor(self, valor):
        if isinstance(valor, (int, float)):
            return str(valor)
        elif isinstance(valor, str):
            return valor.strip().upper()
        else:
            return str(valor)

    def gerar_relatorio_diario(self, dados_grupos):
        """Gera relatório diário com contagem de status específicos"""
        print("\n=== Relatório Diário ===")
        
        for grupo, dados in dados_grupos.items():
            print(f"\nGrupo: {grupo.upper()}")
            
            for colaborador, metricas in dados['metricas'].items():
                print(f"\n{colaborador}:")
                print("  RELATÓRIO DIÁRIO:")
                for status in self.status_especificos:
                    count = metricas['metricas_diarias'].get(status, 0)
                    print(f"  {status}: {count}")
                
                print(f"  TOTAL: {metricas['total_registros']}")
        
        print("\nRelatório diário concluído!")

    def gerar_relatorio_geral(self, dados_grupos):
        """Gera relatório geral com totais por status e colaborador"""
        print("\n=== Relatório Geral ===")
        
        totais_gerais = {status: 0 for status in self.status_especificos}
        total_geral_registros = 0
        
        for grupo, dados in dados_grupos.items():
            print(f"\nGrupo: {grupo.upper()}")
            
            totais_grupo = {status: 0 for status in self.status_especificos}
            total_grupo_registros = 0
            
            # Exibir dados por colaborador
            for colaborador, metricas in dados['metricas'].items():
                print(f"\n{colaborador}:")
                print("  RELATÓRIO GERAL:")
                
                for status in self.status_especificos:
                    count = metricas['status_counts'].get(status, 0)
                    totais_grupo[status] += count
                    totais_gerais[status] += count
                    print(f"  {status}: {count}")
                
                # Exibir total do colaborador
                total_colaborador = metricas['total_registros']
                total_grupo_registros += total_colaborador
                total_geral_registros += total_colaborador
                print(f"  TOTAL: {total_colaborador}")
            
            # Exibir totais do grupo
            print(f"\nTOTAL DO GRUPO {grupo.upper()}:")
            for status, total in totais_grupo.items():
                print(f"  {status}: {total}")
            print(f"  TOTAL GERAL: {total_grupo_registros}")
        
        # Exibir totais gerais
        print("\n=== TOTAIS CONSOLIDADOS ===")
        for status, total in totais_gerais.items():
            print(f"{status}: {total}")
        print(f"TOTAL GERAL: {total_geral_registros}")
        
        print("\nRelatório geral concluído!")

    def gerar_relatorio_produtividade_diaria(self, dados_grupos):
        """Gera relatório de produtividade diária por colaborador"""
        print("\n=== Relatório de Produtividade Diária ===")
        
        for grupo, dados in dados_grupos.items():
            print(f"\nGrupo: {grupo.upper()}")
            
            for colaborador, metricas in dados['metricas'].items():
                # Calcular produtividade por hora
                prod_hora = metricas['produtividade_hora']
                prod_diaria = prod_hora * self.horas_trabalho
                
                # Calcular produtividade por status
                status_counts = metricas['status_counts']
                status_prioritarios = {s: status_counts.get(s, 0) for s in self.status_prioritarios}
                total_prioritarios = sum(status_prioritarios.values())
                
                # Exibir resultados
                print(f"\n{colaborador}:")
                print(f"  Produtividade diária: {prod_diaria:.1f} registros/dia")
                print(f"  Produtividade horária: {prod_hora:.2f} registros/hora")
                print(f"  Status prioritários ({', '.join(self.status_prioritarios)}): {total_prioritarios}")
                print(f"  Eficiência: {(total_prioritarios/metricas['total_registros']*100 if metricas['total_registros'] > 0 else 0):.1f}%")
        
        print("\nRelatório de produtividade concluído!")

if __name__ == "__main__":
    try:
        analisador = AnalisadorInteligente()
        analisador.executar_analise_completa()
    except Exception as e:
        print(f"\nErro crítico: {str(e)}") 