import os
from pathlib import Path
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import base64
from io import BytesIO

class GuiaAnalisador:
    def __init__(self):
        self.titulo = "Guia de Análise de Dados com Machine Learning"
        self.data_atualizacao = datetime.now().strftime('%Y-%m-%d')
        
    def gerar_grafico_exemplo(self):
        """Gera gráfico de exemplo para o guia"""
        # Dados de exemplo
        dados = pd.DataFrame({
            'Colaborador': ['Ana', 'João', 'Maria', 'Pedro'] * 2,
            'STATUS': ['APROVADO', 'QUITADO', 'APROVADO', 'QUITADO'] * 2,
            'Quantidade': [15, 12, 18, 10, 8, 14, 16, 9]
        })
        
        # Gerar gráfico
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Colaborador', y='Quantidade', hue='STATUS', data=dados)
        plt.title('Exemplo: Distribuição de Status por Colaborador')
        
        # Converter para base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        imagem_b64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return imagem_b64
    
    def gerar_html(self):
        """Gera o HTML do guia completo"""
        imagem_grafico = self.gerar_grafico_exemplo()
        
        html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.titulo}</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Prism.js para highlight de código -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" rel="stylesheet">
    
    <style>
        /* Estilos personalizados */
        .hero-section {{
            background: linear-gradient(135deg, #4361ee, #3a0ca3);
            color: white;
            padding: 4rem 0;
        }}
        
        .feature-card {{
            transition: transform 0.3s;
        }}
        
        .feature-card:hover {{
            transform: translateY(-5px);
        }}
        
        .code-block {{
            background: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
        }}
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="bi bi-graph-up"></i> Análise Inteligente
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="#inicio">Início</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#machine-learning">Machine Learning</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#exemplos">Exemplos</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#instalacao">Instalação</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero-section" id="inicio">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-lg-8">
                    <h1 class="display-4 fw-bold">Análise Inteligente de Dados</h1>
                    <p class="lead">
                        Um guia completo sobre análise de dados com machine learning para otimização de processos.
                    </p>
                    <p>Última atualização: {self.data_atualizacao}</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Machine Learning Section -->
    <section class="py-5" id="machine-learning">
        <div class="container">
            <h2 class="mb-4">Técnicas de Machine Learning Utilizadas</h2>
            
            <div class="row g-4">
                <!-- Random Forest Card -->
                <div class="col-md-6">
                    <div class="card feature-card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="bi bi-diagram-3"></i> Random Forest
                            </h5>
                            <p class="card-text">
                                Utilizado para classificação de prioridades e previsão de tempo de conclusão.
                            </p>
                            <div class="code-block">
<pre><code class="language-python">from sklearn.ensemble import RandomForestClassifier

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=None,
    min_samples_split=2,
    random_state=42
)</code></pre>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Gradient Boosting Card -->
                <div class="col-md-6">
                    <div class="card feature-card h-100">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="bi bi-graph-up-arrow"></i> Gradient Boosting
                            </h5>
                            <p class="card-text">
                                Aplicado para previsão de métricas de eficiência e produtividade.
                            </p>
                            <div class="code-block">
<pre><code class="language-python">from sklearn.ensemble import GradientBoostingRegressor

gb_model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    random_state=42
)</code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Exemplo Prático Section -->
    <section class="py-5 bg-light" id="exemplos">
        <div class="container">
            <h2 class="mb-4">Exemplo Prático</h2>
            
            <div class="row">
                <div class="col-lg-6">
                    <div class="card mb-4">
                        <div class="card-body">
                            <h5 class="card-title">Visualização de Dados</h5>
                            <img src="data:image/png;base64,{imagem_grafico}" 
                                 class="img-fluid" 
                                 alt="Gráfico de exemplo">
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-6">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Código de Exemplo</h5>
                            <div class="code-block">
<pre><code class="language-python">def calcular_metricas(self, df):
    # Calcular métricas básicas
    total_registros = len(df)
    status_counts = df['STATUS'].value_counts()
    
    # Calcular eficiência
    aprovados = status_counts.get('APROVADO', 0)
    quitados = status_counts.get('QUITADO', 0)
    taxa_eficiencia = (aprovados + quitados) / total_registros
    
    return {
        'total_registros': total_registros,
        'status_counts': status_counts,
        'taxa_eficiencia': taxa_eficiencia
    }</code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Instalação Section -->
    <section class="py-5" id="instalacao">
        <div class="container">
            <h2 class="mb-4">Instalação e Configuração</h2>
            
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Requisitos</h5>
                    <div class="code-block">
<pre><code class="language-bash"># requirements.txt
pandas==1.5.3
numpy==1.23.5
scikit-learn==1.2.2
matplotlib==3.7.1
seaborn==0.12.2</code></pre>
                    </div>
                    
                    <h5 class="mt-4">Passos para Instalação</h5>
                    <ol>
                        <li>Clone o repositório</li>
                        <li>Crie um ambiente virtual: <code>python -m venv venv</code></li>
                        <li>Ative o ambiente virtual</li>
                        <li>Instale as dependências: <code>pip install -r requirements.txt</code></li>
                    </ol>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-dark text-light py-4">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5>Links Úteis</h5>
                    <ul class="list-unstyled">
                        <li><a href="https://scikit-learn.org/" class="text-light">Scikit-learn</a></li>
                        <li><a href="https://pandas.pydata.org/" class="text-light">Pandas</a></li>
                        <li><a href="https://seaborn.pydata.org/" class="text-light">Seaborn</a></li>
                    </ul>
                </div>
                <div class="col-md-6">
                    <h5>Contato</h5>
                    <p>
                        <i class="bi bi-envelope"></i> suporte@analisador.com<br>
                        <i class="bi bi-github"></i> github.com/analisador
                    </p>
                </div>
            </div>
        </div>
    </footer>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
</body>
</html>"""
        
        return html

    def salvar_guia(self):
        """Salva o guia HTML em um arquivo"""
        html_content = self.gerar_html()
        
        # Criar diretório de saída se não existir
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Salvar arquivo HTML
        output_file = output_dir / 'guia_analise.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"Guia gerado com sucesso em: {output_file}")

if __name__ == "__main__":
    guia = GuiaAnalisador()
    guia.salvar_guia()