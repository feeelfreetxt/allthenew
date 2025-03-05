import os
import sys
from pathlib import Path
import unittest
from fastapi.testclient import TestClient
from datetime import datetime

# Corrigir o caminho para importação dos módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importar módulos locais com o caminho correto
from .main import app
from .database import SessionLocal, engine, Base
from .pipeline_dashboard import DashboardPipeline

class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Configurar ambiente de teste"""
        self.client = TestClient(app)
        self.test_db = SessionLocal()
        
        # Criar diretórios necessários
        os.makedirs('data', exist_ok=True)
        os.makedirs('static', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Verificar arquivos Excel
        self.arquivo_julio = Path("F:\\okok\\(JULIO) LISTAS INDIVIDUAIS.xlsx")
        self.arquivo_leandro = Path("F:\\okok\\(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx")
        
        print("\nVerificando arquivos necessários...")
        if not self.arquivo_julio.exists():
            print(f"AVISO: Arquivo não encontrado: {self.arquivo_julio}")
        if not self.arquivo_leandro.exists():
            print(f"AVISO: Arquivo não encontrado: {self.arquivo_leandro}")

    def test_1_root_endpoint(self):
        """Testar endpoint raiz"""
        print("\nTestando endpoint raiz...")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        print("✓ Endpoint raiz OK")

    def test_2_pipeline_integration(self):
        """Testar integração com o pipeline"""
        print("\nTestando integração com pipeline...")
        try:
            pipeline = DashboardPipeline()
            pipeline.executar_pipeline()
            print("✓ Pipeline executado com sucesso")
        except Exception as e:
            self.fail(f"Pipeline falhou: {str(e)}")

    def test_3_database_integration(self):
        """Testar integração com banco de dados"""
        print("\nTestando integração com banco de dados...")
        try:
            # Tentar criar todas as tabelas
            Base.metadata.create_all(bind=engine)
            print("✓ Banco de dados criado com sucesso")
        except Exception as e:
            self.fail(f"Criação do banco de dados falhou: {str(e)}")

    def test_4_analise_endpoint(self):
        """Testar endpoint de análise"""
        print("\nTestando endpoint de análise...")
        try:
            response = self.client.post("/analisar/")
            if response.status_code != 200:
                print(f"Erro na resposta: {response.json()}")
            self.assertEqual(response.status_code, 200)
            print("✓ Endpoint de análise OK")
        except Exception as e:
            print(f"Erro durante o teste: {str(e)}")
            raise

    def test_5_relatorios_endpoint(self):
        """Testar endpoint de relatórios"""
        print("\nTestando endpoint de relatórios...")
        response = self.client.get("/relatorios/")
        self.assertEqual(response.status_code, 200)
        print("✓ Endpoint de relatórios OK")

    def tearDown(self):
        """Limpar após os testes"""
        self.test_db.close()

if __name__ == "__main__":
    print("Iniciando testes de integração...")
    unittest.main(verbosity=2) 