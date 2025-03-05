import os
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
from pathlib import Path
import json
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

# Importando os módulos criados anteriormente
from validacao_metricas import validar_metricas_qualidade
from analise_detalhada import analisar_detalhes_colaborador
from analise_paralela import analisar_arquivo_paralelo
from debug_excel import AnalisadorExcel

class DashboardPipeline:
    def __init__(self):
        self.base_path = Path("F:\\okok")
        self.output_path = self.base_path / "dashboard_output"
        self.output_path.mkdir(exist_ok=True)
        self.output_file = None
        
        # Configuração de estilo CSS
        self.css = """
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .header {
                background: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .metric {
                display: inline-block;
                padding: 10px;
                margin: 5px;
                background: #ecf0f1;
                border-radius: 4px;
                min-width: 150px;
            }
            .good { color: #27ae60; }
            .warning { color: #f39c12; }
            .bad { color: #c0392b; }
            .chart-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                justify-content: space-between;
            }
            .chart {
                flex: 1;
                min-width: 300px;
                max-width: 600px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #2c3e50;
                color: white;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            .nav {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            .nav-item {
                padding: 10px 20px;
                background: #2c3e50;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
            }
            .nav-item:hover {
                background: #34495e;
            }
        </style>
        """
    
    def executar_pipeline(self) -> Dict[str, Any]:
        """Executa o pipeline completo de análise"""
        try:
            # Inicializar resultados
            resultados = {
                'colaboradores': [],
                'relatorio': {},
                'metricas_gerais': {
                    'media_score': 0.0,
                    'total_colaboradores': 0,
                    'data_analise': datetime.now().isoformat()
                }
            }

            # Processar arquivos Excel
            arquivos = {
                'julio': self.base_path / "(JULIO) LISTAS INDIVIDUAIS.xlsx",
                'leandro': self.base_path / "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
            }

            for grupo, arquivo in arquivos.items():
                if not arquivo.exists():
                    print(f"Arquivo não encontrado: {arquivo}")
                    continue

                # Processar cada arquivo
                dados_grupo = self.processar_arquivo(arquivo, grupo)
                if dados_grupo:
                    resultados['colaboradores'].extend(dados_grupo)

            # Calcular métricas gerais
            if resultados['colaboradores']:
                scores = [c['score'] for c in resultados['colaboradores']]
                resultados['metricas_gerais'].update({
                    'media_score': sum(scores) / len(scores),
                    'total_colaboradores': len(resultados['colaboradores'])
                })

            # Gerar dashboard HTML
            self.gerar_dashboard_html(resultados)

            print(f"Dashboard gerado em: {self.output_file}")
            print("Pipeline concluído com sucesso!")

            return resultados

        except Exception as e:
            print(f"Erro no pipeline: {str(e)}")
            return {
                'colaboradores': [],
                'relatorio': {'erro': str(e)},
                'metricas_gerais': {
                    'status': 'erro',
                    'mensagem': str(e),
                    'data_analise': datetime.now().isoformat()
                }
            }
    
    def processar_arquivo(self, arquivo: Path, grupo: str) -> List[Dict[str, Any]]:
        """Processa um arquivo Excel e retorna dados dos colaboradores"""
        try:
            xls = pd.ExcelFile(arquivo)
            colaboradores = []

            for sheet in xls.sheet_names:
                if sheet.lower() not in ['resumo', 'índice', 'index', 'summary']:
                    df = pd.read_excel(arquivo, sheet_name=sheet)
                    metricas = self.calcular_metricas(df)
                    colaboradores.append({
                        'nome': sheet,
                        'grupo': grupo,
                        'score': metricas['score'],
                        'taxa_preenchimento': metricas['taxa_preenchimento'],
                        'taxa_padronizacao': metricas['taxa_padronizacao'],
                        'consistencia': metricas['consistencia'],
                        'metricas_detalhadas': metricas
                    })

            return colaboradores

        except Exception as e:
            print(f"Erro ao processar arquivo {arquivo}: {str(e)}")
            return []
    
    def gerar_dashboard_html(self, resultados):
        """Gera o dashboard HTML com todos os resultados"""
        print("Gerando dashboard...")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard de Análise de Colaboradores</title>
            {self.css}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Dashboard de Análise de Colaboradores</h1>
                    <p>Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
                
                <div class="nav">
                    <a href="#resumo" class="nav-item">Resumo</a>
                    <a href="#metricas" class="nav-item">Métricas</a>
                    <a href="#detalhes" class="nav-item">Detalhes</a>
                    <a href="#recomendacoes" class="nav-item">Recomendações</a>
                </div>
                
                <div id="resumo" class="card">
                    <h2>Resumo Geral</h2>
                    {self.gerar_secao_resumo(resultados)}
                </div>
                
                <div id="metricas" class="card">
                    <h2>Métricas por Colaborador</h2>
                    {self.gerar_secao_metricas(resultados)}
                </div>
                
                <div id="detalhes" class="card">
                    <h2>Análise Detalhada</h2>
                    {self.gerar_secao_detalhes(resultados)}
                </div>
                
                <div id="recomendacoes" class="card">
                    <h2>Recomendações</h2>
                    {self.gerar_secao_recomendacoes(resultados)}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Salvar o dashboard
        self.output_file = self.output_path / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Dashboard gerado em: {self.output_file}")
        
        # Abrir o dashboard no navegador
        webbrowser.open(str(self.output_file))
    
    def gerar_secao_resumo(self, resultados):
        """Gera a seção de resumo do dashboard"""
        # Implementar lógica de resumo
        return """
        <div class="chart-container">
            <div class="chart">
                <h3>Distribuição de Scores</h3>
                <!-- Adicionar gráfico de distribuição -->
            </div>
            <div class="chart">
                <h3>Top Performers</h3>
                <!-- Adicionar tabela de top performers -->
            </div>
        </div>
        """
    
    def gerar_secao_metricas(self, resultados):
        """Gera a seção de métricas do dashboard"""
        # Implementar lógica de métricas
        return """
        <table>
            <tr>
                <th>Colaborador</th>
                <th>Score</th>
                <th>Taxa Preenchimento</th>
                <th>Taxa Padronização</th>
                <th>Consistência</th>
            </tr>
            <!-- Adicionar linhas da tabela -->
        </table>
        """
    
    def gerar_secao_detalhes(self, resultados):
        """Gera a seção de detalhes do dashboard"""
        # Implementar lógica de detalhes
        return """
        <div class="chart-container">
            <!-- Adicionar gráficos detalhados -->
        </div>
        """
    
    def gerar_secao_recomendacoes(self, resultados):
        """Gera a seção de recomendações do dashboard"""
        # Implementar lógica de recomendações
        return """
        <ul>
            <!-- Adicionar recomendações -->
        </ul>
        """

if __name__ == "__main__":
    pipeline = DashboardPipeline()
    pipeline.executar_pipeline() 