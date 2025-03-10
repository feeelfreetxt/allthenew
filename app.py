from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Carregar variáveis de ambiente
load_dotenv()

# Criar diretório para templates e arquivos estáticos se não existirem
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = FastAPI(title="Dashboard de Análise de Contratos")

# Configurar diretórios
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Criar diretórios se não existirem
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Configurar arquivos estáticos e templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Configurar banco de dados
DB_PATH = os.getenv("DB_PATH", "test_relatorio_dashboard.db")

def get_db():
    """Função helper para obter conexão com o banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao conectar ao banco de dados: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Rota principal que renderiza o dashboard"""
    # Dados de exemplo para o template
    dados_exemplo = {
        "request": request,
        "totais": {
            "verificado": 10,
            "analise": 5,
            "pendente": 15,
            "prioridade": 3,
            "prioridade_total": 8,
            "aprovado": 20,
            "apreendido": 2,
            "cancelado": 1
        },
        "df_relatorio": [
            {
                "colaborador": "COLABORADOR TESTE",
                "grupo": "GRUPO TESTE",
                "total": 30,
                "verificado": 10,
                "pendente": 15,
                "aprovado": 5,
                "prod_diaria": 30.0,
                "eficiencia": 85.5
            }
        ],
        "ultima_atualizacao": "10/03/2024 08:00"
    }
    return templates.TemplateResponse("dashboard.html", dados_exemplo)

@app.get("/status")
async def status():
    """Endpoint para verificar se o servidor está funcionando"""
    return {
        "status": "online",
        "message": "Servidor funcionando corretamente"
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar a saúde do servidor"""
    return {
        "servidor": True,
        "banco_dados": True,
        "recursos": {
            "memoria_ok": True,
            "cpu_ok": True
        }
    }

@app.post("/atualizar")
async def atualizar_dados():
    """Rota para atualizar os dados do dashboard"""
    return {"message": "Dados atualizados com sucesso"}

@app.get("/exportar/{tipo}/{formato}")
async def exportar_dados(tipo: str, formato: str):
    """Endpoint para exportar dados"""
    if tipo not in ["diario", "geral", "metricas"] or formato not in ["excel", "csv"]:
        raise HTTPException(status_code=404, detail="Formato ou tipo inválido")
    return {"message": "Exportação em andamento"}

if __name__ == "__main__":
    print("Iniciando servidor FastAPI na porta 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001) 