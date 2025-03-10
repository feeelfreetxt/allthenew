import unittest
from fastapi.testclient import TestClient
from app import app, get_db
import sqlite3
import os
import json

class TestDashboardApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup test environment before all tests"""
        cls.client = TestClient(app)
        cls.test_db_path = "test_relatorio_dashboard.db"
        
        # Criar banco de dados de teste
        conn = sqlite3.connect(cls.test_db_path)
        cursor = conn.cursor()
        
        # Criar tabelas necessárias
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS grupos (
            id INTEGER PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            grupo_id INTEGER NOT NULL,
            FOREIGN KEY (grupo_id) REFERENCES grupos (id),
            UNIQUE (nome, grupo_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS relatorio_geral (
            id INTEGER PRIMARY KEY,
            colaborador_id INTEGER NOT NULL,
            data_relatorio DATE NOT NULL,
            verificado INTEGER DEFAULT 0,
            analise INTEGER DEFAULT 0,
            pendente INTEGER DEFAULT 0,
            prioridade INTEGER DEFAULT 0,
            prioridade_total INTEGER DEFAULT 0,
            aprovado INTEGER DEFAULT 0,
            apreendido INTEGER DEFAULT 0,
            cancelado INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id),
            UNIQUE (colaborador_id, data_relatorio)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metricas_produtividade (
            id INTEGER PRIMARY KEY,
            colaborador_id INTEGER NOT NULL,
            data_relatorio DATE NOT NULL,
            prod_diaria REAL DEFAULT 0,
            prod_horaria REAL DEFAULT 0,
            eficiencia REAL DEFAULT 0,
            FOREIGN KEY (colaborador_id) REFERENCES colaboradores (id),
            UNIQUE (colaborador_id, data_relatorio)
        )
        ''')
        
        # Inserir dados de teste
        cursor.execute("INSERT INTO grupos (nome) VALUES (?)", ("GRUPO TESTE",))
        grupo_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO colaboradores (nome, grupo_id) VALUES (?, ?)", 
                      ("COLABORADOR TESTE", grupo_id))
        colab_id = cursor.lastrowid
        
        cursor.execute("""
        INSERT INTO relatorio_geral 
        (colaborador_id, data_relatorio, verificado, analise, pendente, total) 
        VALUES (?, date('now'), 10, 5, 15, 30)
        """, (colab_id,))
        
        cursor.execute("""
        INSERT INTO metricas_produtividade 
        (colaborador_id, data_relatorio, prod_diaria, prod_horaria, eficiencia) 
        VALUES (?, date('now'), 30.0, 3.75, 85.5)
        """, (colab_id,))
        
        conn.commit()
        conn.close()

    def test_01_read_root(self):
        """Teste da rota principal"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard de Análise de Contratos", response.content)

    def test_02_status_endpoint(self):
        """Teste do endpoint de status"""
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["message"], "Servidor funcionando corretamente")

    def test_03_health_check(self):
        """Teste do endpoint de verificação de saúde"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("servidor", data)
        self.assertIn("banco_dados", data)
        self.assertIn("recursos", data)

    def test_04_atualizar_endpoint(self):
        """Teste do endpoint de atualização"""
        response = self.client.post("/atualizar")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "Dados atualizados com sucesso")

    def test_05_exportar_dados(self):
        """Teste dos endpoints de exportação"""
        formatos = ["excel", "csv"]
        tipos = ["diario", "geral", "metricas"]
        
        for formato in formatos:
            for tipo in tipos:
                response = self.client.get(f"/exportar/{tipo}/{formato}")
                self.assertIn(response.status_code, [200, 404])  # 404 é aceitável se não houver dados

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        try:
            os.remove(cls.test_db_path)
        except:
            pass

if __name__ == '__main__':
    unittest.main() 