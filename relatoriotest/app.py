from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from pathlib import Path
import uvicorn
from datetime import datetime, timedelta
import os

# Criar diretório para templates e arquivos estáticos se não existirem
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="Dashboard de Análise de Contratos")

# Montar diretórios para arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Função para conectar ao banco de dados
def get_db():
    db_path = "F:/relatoriotest/relatorio_dashboard.db"
    # Usar check_same_thread=False para evitar o erro de thread
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Para retornar dicionários
    try:
        yield conn
    finally:
        conn.close()

# Função para gerar gráficos
def gerar_grafico_pizza(df_status):
    plt.figure(figsize=(10, 6))
    labels = ['Verificado', 'Análise', 'Pendente', 'Prioridade', 
              'Prioridade Total', 'Aprovado', 'Apreendido', 'Cancelado']
    valores = [df_status[0][col] for col in ['verificado', 'analise', 'pendente', 'prioridade', 
                                           'prioridade_total', 'aprovado', 'apreendido', 'cancelado']]
    
    plt.pie(valores, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Distribuição de Status')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    return img_str

def gerar_grafico_barras(df_metricas):
    plt.figure(figsize=(12, 8))
    df_top10 = df_metricas.nlargest(10, 'eficiencia')
    sns.barplot(x='colaborador', y='eficiencia', hue='grupo', data=df_top10)
    plt.title('Top 10 Colaboradores por Eficiência')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    return img_str

# Rota principal - Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, conn: sqlite3.Connection = Depends(get_db)):
    try:
        # Consultas SQL
        cursor = conn.cursor()
        
        # Dados dos grupos
        cursor.execute("""
        SELECT g.nome, COUNT(c.id) AS total_colaboradores
        FROM grupos g
        LEFT JOIN colaboradores c ON g.id = c.grupo_id
        GROUP BY g.nome
        """)
        grupos = cursor.fetchall()
        
        # Verificar se há dados
        if not grupos:
            # Renderizar template com mensagem de erro
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "error": "Não há dados disponíveis no banco de dados. Execute o analisador primeiro."
            })
        
        # Dados de status
        cursor.execute("""
        SELECT 
            SUM(verificado) as verificado,
            SUM(analise) as analise,
            SUM(pendente) as pendente,
            SUM(prioridade) as prioridade,
            SUM(prioridade_total) as prioridade_total,
            SUM(aprovado) as aprovado,
            SUM(apreendido) as apreendido,
            SUM(cancelado) as cancelado
        FROM relatorio_geral
        """)
        status = cursor.fetchall()
        
        # Dados de métricas
        cursor.execute("""
        SELECT 
            c.nome AS colaborador,
            g.nome AS grupo,
            rg.total,
            mp.prod_diaria,
            mp.prod_horaria,
            mp.eficiencia
        FROM colaboradores c
        JOIN grupos g ON c.grupo_id = g.id
        JOIN relatorio_geral rg ON c.id = rg.colaborador_id
        JOIN metricas_produtividade mp ON c.id = mp.colaborador_id
        WHERE rg.data_relatorio = mp.data_relatorio
        ORDER BY mp.eficiencia DESC
        """)
        metricas = cursor.fetchall()
        
        # Converter para DataFrame para gráficos
        df_metricas = pd.DataFrame(metricas)
        
        # Gerar gráficos
        grafico_pizza = gerar_grafico_pizza(status)
        grafico_barras = gerar_grafico_barras(df_metricas)
        
        # Renderizar template
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "grupos": grupos,
            "status": status[0],
            "metricas": metricas,
            "grafico_pizza": grafico_pizza,
            "grafico_barras": grafico_barras
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar dashboard: {str(e)}")

# Rota para exportar dados
@app.get("/exportar/{tipo}/{formato}")
async def exportar_dados(tipo: str, formato: str, conn: sqlite3.Connection = Depends(get_db)):
    from fastapi.responses import FileResponse
    
    try:
        cursor = conn.cursor()
        
        if tipo == "diario":
            query = """
            SELECT c.nome as colaborador, g.nome as grupo, rd.*
            FROM relatorio_diario rd
            JOIN colaboradores c ON rd.colaborador_id = c.id
            JOIN grupos g ON c.grupo_id = g.id
            """
            nome_arquivo = "relatorio_diario"
        
        elif tipo == "geral":
            query = """
            SELECT c.nome as colaborador, g.nome as grupo, rg.*
            FROM relatorio_geral rg
            JOIN colaboradores c ON rg.colaborador_id = c.id
            JOIN grupos g ON c.grupo_id = g.id
            """
            nome_arquivo = "relatorio_geral"
        
        elif tipo == "metricas":
            query = """
            SELECT c.nome as colaborador, g.nome as grupo, mp.*
            FROM metricas_produtividade mp
            JOIN colaboradores c ON mp.colaborador_id = c.id
            JOIN grupos g ON c.grupo_id = g.id
            """
            nome_arquivo = "metricas_produtividade"
        
        else:
            raise HTTPException(status_code=400, detail="Tipo de relatório inválido")
        
        # Executar consulta
        cursor.execute(query)
        dados = cursor.fetchall()
        df = pd.DataFrame(dados)
        
        # Caminho para salvar o arquivo
        data_atual = datetime.now().strftime("%Y%m%d")
        caminho_arquivo = f"static/{nome_arquivo}_{data_atual}"
        
        # Exportar conforme formato solicitado
        if formato == "excel":
            caminho_completo = f"{caminho_arquivo}.xlsx"
            df.to_excel(caminho_completo, index=False)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        elif formato == "csv":
            caminho_completo = f"{caminho_arquivo}.csv"
            df.to_csv(caminho_completo, index=False)
            media_type = "text/csv"
        
        else:
            raise HTTPException(status_code=400, detail="Formato inválido")
        
        return FileResponse(
            path=caminho_completo,
            filename=os.path.basename(caminho_completo),
            media_type=media_type
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao exportar dados: {str(e)}")

# Criar template HTML
def criar_template_html():
    """Cria o template HTML para o dashboard"""
    template_html = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Análise de Contratos</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
        }
        .card {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            transition: transform 0.3s;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .nav-tabs .nav-link {
            color: #495057;
        }
        .nav-tabs .nav-link.active {
            font-weight: bold;
            color: #0d6efd;
        }
        .header {
            background: linear-gradient(120deg, #2c3e50, #4ca1af);
            color: white;
            padding: 20px 0;
            margin-bottom: 30px;
        }
        .status-box {
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            color: white;
            font-weight: bold;
        }
        .bg-verificado { background-color: #3498db; }
        .bg-analise { background-color: #f39c12; }
        .bg-pendente { background-color: #e74c3c; }
        .bg-prioridade { background-color: #9b59b6; }
        .bg-aprovado { background-color: #2ecc71; }
        .bg-apreendido { background-color: #c0392b; }
        .bg-cancelado { background-color: #7f8c8d; }
        .table-responsive {
            max-height: 400px;
            overflow-y: auto;
        }
        .table th {
            position: sticky;
            top: 0;
            background-color: #f8f9fa;
            z-index: 10;
        }
    </style>
</head>
<body>
    <div class="header text-center">
        <h1>Análise de Contratos</h1>
        <p class="lead">Dashboard Interativo</p>
    </div>

    <div class="container">
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h3>Dashboard</h3>
                    </div>
                    <div class="card-body">
                        <ul class="nav nav-tabs" id="myTab" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="overview-tab" data-bs-toggle="tab" data-bs-target="#overview" type="button" role="tab">Visão Geral</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="collaborators-tab" data-bs-toggle="tab" data-bs-target="#collaborators" type="button" role="tab">Colaboradores</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="reports-tab" data-bs-toggle="tab" data-bs-target="#reports" type="button" role="tab">Relatórios</button>
                            </li>
                        </ul>
                        
                        <div class="tab-content mt-3" id="myTabContent">
                            <!-- Visão Geral -->
                            <div class="tab-pane fade show active" id="overview" role="tabpanel">
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="card">
                                            <div class="card-header bg-info text-white">
                                                <h4>Grupos</h4>
                                            </div>
                                            <div class="card-body">
                                                <div class="table-responsive">
                                                    <table class="table table-hover">
                                                        <thead>
                                                            <tr>
                                                                <th>Grupo</th>
                                                                <th>Colaboradores</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {% for grupo in grupos %}
                                                            <tr>
                                                                <td>{{ grupo.nome }}</td>
                                                                <td>{{ grupo.total_colaboradores }}</td>
                                                            </tr>
                                                            {% endfor %}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="col-md-8">
                                        <div class="card">
                                            <div class="card-header bg-info text-white">
                                                <h4>Distribuição de Status</h4>
                                            </div>
                                            <div class="card-body text-center">
                                                <img src="data:image/png;base64,{{ grafico_pizza }}" class="img-fluid">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row mt-4">
                                    <div class="col-md-12">
                                        <div class="card">
                                            <div class="card-header bg-info text-white">
                                                <h4>Status</h4>
                                            </div>
                                            <div class="card-body">
                                                <div class="row">
                                                    <div class="col-md-3">
                                                        <div class="status-box bg-verificado">
                                                            VERIFICADO: {{ status.verificado }}
                                                        </div>
                                                    </div>
                                                    <div class="col-md-3">
                                                        <div class="status-box bg-analise">
                                                            ANÁLISE: {{ status.analise }}
                                                        </div>
                                                    </div>
                                                    <div class="col-md-3">
                                                        <div class="status-box bg-pendente">
                                                            PENDENTE: {{ status.pendente }}
                                                        </div>
                                                    </div>
                                                    <div class="col-md-3">
                                                        <div class="status-box bg-prioridade">
                                                            PRIORIDADE: {{ status.prioridade }}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="row mt-3">
                                                    <div class="col-md-3">
                                                        <div class="status-box bg-aprovado">
                                                            APROVADO: {{ status.aprovado }}
                                                        </div>
                                                    </div>
                                                    <div class="col-md-3">
                                                        <div class="status-box bg-apreendido">
                                                            APREENDIDO: {{ status.apreendido }}
                                                        </div>
                                                    </div>
                                                    <div class="col-md-3">
                                                        <div class="status-box bg-cancelado">
                                                            CANCELADO: {{ status.cancelado }}
                                                        </div>
                                                    </div>
                                                    <div class="col-md-3">
                                                        <div class="status-box" style="background-color: #1abc9c;">
                                                            PRIORIDADE TOTAL: {{ status.prioridade_total }}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Colaboradores -->
                            <div class="tab-pane fade" id="collaborators" role="tabpanel">
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="card">
                                            <div class="card-header bg-success text-white">
                                                <h4>Top Colaboradores</h4>
                                            </div>
                                            <div class="card-body text-center">
                                                <img src="data:image/png;base64,{{ grafico_barras }}" class="img-fluid">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row mt-4">
                                    <div class="col-md-12">
                                        <div class="card">
                                            <div class="card-header bg-success text-white">
                                                <h4>Métricas por Colaborador</h4>
                                            </div>
                                            <div class="card-body">
                                                <div class="table-responsive">
                                                    <table class="table table-striped table-hover">
                                                        <thead>
                                                            <tr>
                                                                <th>Colaborador</th>
                                                                <th>Grupo</th>
                                                                <th>Total</th>
                                                                <th>Prod. Diária</th>
                                                                <th>Prod. Horária</th>
                                                                <th>Eficiência (%)</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {% for m in metricas %}
                                                            <tr>
                                                                <td>{{ m.colaborador }}</td>
                                                                <td>{{ m.grupo }}</td>
                                                                <td>{{ m.total }}</td>
                                                                <td>{{ "%.1f"|format(m.prod_diaria) }}</td>
                                                                <td>{{ "%.2f"|format(m.prod_horaria) }}</td>
                                                                <td>{{ "%.1f"|format(m.eficiencia) }}</td>
                                                            </tr>
                                                            {% endfor %}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Relatórios -->
                            <div class="tab-pane fade" id="reports" role="tabpanel">
                                <div class="row">
                                    <div class="col-md-12">
                                        <div class="card">
                                            <div class="card-header bg-warning text-dark">
                                                <h4>Exportar Relatórios</h4>
                                            </div>
                                            <div class="card-body">
                                                <div class="row">
                                                    <div class="col-md-6">
                                                        <div class="mb-3">
                                                            <label for="reportType" class="form-label">Tipo de Relatório</label>
                                                            <select class="form-select" id="reportType">
                                                                <option value="diario">Relatório Diário</option>
                                                                <option value="geral">Relatório Geral</option>
                                                                <option value="metricas">Métricas de Produtividade</option>
                                                            </select>
                                                        </div>
                                                    </div>
                                                    <div class="col-md-6">
                                                        <div class="mb-3">
                                                            <label for="exportFormat" class="form-label">Formato</label>
                                                            <select class="form-select" id="exportFormat">
                                                                <option value="excel">Excel</option>
                                                                <option value="csv">CSV</option>
                                                            </select>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                                                    <button type="button" class="btn btn-primary" id="exportBtn">
                                                        <i class="bi bi-download me-1"></i> Exportar
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Exportar relatórios
            document.getElementById('exportBtn').addEventListener('click', function() {
                const reportType = document.getElementById('reportType').value;
                const exportFormat = document.getElementById('exportFormat').value;
                
                window.location.href = `/exportar/${reportType}/${exportFormat}`;
            });
        });
    </script>
</body>
</html>
    """
    
    # Criar diretório de templates se não existir
    os.makedirs("templates", exist_ok=True)
    
    # Salvar o template
    with open("templates/dashboard.html", "w", encoding="utf-8") as f:
        f.write(template_html)
    
    print("Template HTML criado com sucesso!")

# Adicione esta rota para verificar se o servidor está funcionando
@app.get("/status")
async def status():
    return {"status": "online", "message": "Servidor funcionando corretamente"}

# Iniciar o servidor se executado diretamente
if __name__ == "__main__":
    criar_template_html()
    print("Iniciando servidor FastAPI na porta 8000...")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 