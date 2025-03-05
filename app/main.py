from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import uvicorn
from datetime import datetime
import json
from typing import List, Dict, Any
from pathlib import Path

# Importar módulos locais
from database import SessionLocal, engine, Colaborador, RelatorioSemanal
from pipeline_dashboard import DashboardPipeline
from schemas import ColaboradorCreate, RelatorioCreate
from analise_eficiencia import AnalisadorEficiencia
from validacao_dados import ExcelLeitor
import os
import pandas as pd

app = FastAPI(title="Sistema de Análise de Colaboradores")

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependência para obter sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Página inicial"""
    return """
    <html>
        <head>
            <title>Sistema de Análise de Colaboradores</title>
            <link href="/static/style.css" rel="stylesheet">
        </head>
        <body>
            <div class="container">
                <h1>Sistema de Análise de Colaboradores</h1>
                <nav>
                    <a href="/docs">API Docs</a>
                    <a href="/dashboard">Dashboard</a>
                    <a href="/relatorios">Relatórios</a>
                </nav>
            </div>
        </body>
    </html>
    """

@app.post("/analisar/", response_model=Dict[str, Any])
async def analisar_dados(db: Session = Depends(get_db)):
    """Executa análise e salva no banco de dados"""
    try:
        pipeline = DashboardPipeline()
        resultados = pipeline.executar_pipeline()
        
        if not resultados or 'colaboradores' not in resultados:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": "Nenhum resultado encontrado na análise"}
            )

        # Salvar resultados no banco
        for colaborador in resultados['colaboradores']:
            db_colaborador = Colaborador(
                nome=colaborador['nome'],
                grupo=colaborador['grupo'],
                score=colaborador.get('score', 0.0),
                taxa_preenchimento=colaborador.get('taxa_preenchimento', 0.0),
                taxa_padronizacao=colaborador.get('taxa_padronizacao', 0.0),
                consistencia=colaborador.get('consistencia', 0.0),
                data_analise=datetime.now(),
                metricas_detalhadas=colaborador.get('metricas_detalhadas', {})
            )
            db.add(db_colaborador)
        
        # Gerar relatório semanal
        relatorio = RelatorioSemanal(
            semana=datetime.now().isocalendar()[1],
            ano=datetime.now().year,
            data_geracao=datetime.now(),
            dados_relatorio=resultados.get('relatorio', {}),
            metricas_gerais=resultados.get('metricas_gerais', {})
        )
        db.add(relatorio)
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao salvar no banco de dados: {str(e)}"
            )

        return {
            "message": "Análise concluída e dados salvos",
            "dashboard_path": str(pipeline.output_file),
            "colaboradores": len(resultados['colaboradores']),
            "data_analise": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/colaboradores/", response_model=List[ColaboradorCreate])
async def listar_colaboradores(db: Session = Depends(get_db)):
    """Lista todos os colaboradores"""
    return db.query(Colaborador).all()

@app.get("/relatorios/", response_model=List[RelatorioCreate])
async def listar_relatorios(db: Session = Depends(get_db)):
    """Lista todos os relatórios semanais"""
    return db.query(RelatorioSemanal).all()

def main():
    # Configurar caminhos
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / 'data'
    
    # Criar diretório data se não existir
    data_dir.mkdir(exist_ok=True)
    
    # Inicializar classes
    leitor = ExcelLeitor()
    analisador = AnalisadorEficiencia()
    
    # Arquivos para processar
    arquivos = [
        data_dir / "(JULIO) LISTAS INDIVIDUAIS.xlsx",
        data_dir / "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
    ]
    
    print("=== Iniciando Análise de Eficiência ===")
    
    # Processar cada arquivo
    for arquivo in arquivos:
        if not arquivo.exists():
            print(f"Arquivo não encontrado: {arquivo}")
            continue
            
        print(f"\nProcessando: {arquivo.name}")
        
        # Primeiro ler os dados
        dados = leitor.ler_arquivo(str(arquivo))
        
        if dados['status'] == 'sucesso':
            print("✓ Arquivo lido com sucesso")
            
            # Analisar cada aba
            for nome_aba, dados_aba in dados['abas'].items():
                print(f"\nAnalisando aba: {nome_aba}")
                if dados_aba and 'dados' in dados_aba:
                    try:
                        df = pd.DataFrame(dados_aba['dados'])
                        resultado = analisador.avaliar_eficiencia(df)
                        
                        if resultado['status'] == 'sucesso':
                            print(f"Eficiência: {resultado['eficiencia']}")
                            print("Métricas principais:")
                            for metrica, valor in resultado['metricas'].items():
                                print(f"- {metrica}: {valor:.2f}")
                            
                            if resultado['recomendacoes']:
                                print("\nRecomendações:")
                                for rec in resultado['recomendacoes']:
                                    print(f"- {rec}")
                    except Exception as e:
                        print(f"Erro ao analisar aba {nome_aba}: {str(e)}")
        else:
            print(f"✗ Erro ao ler arquivo: {dados['mensagem']}")

if __name__ == "__main__":
    main() 