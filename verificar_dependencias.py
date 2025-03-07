import subprocess
import pkg_resources
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    filename='dependencias.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DependencyManager:
    def __init__(self):
        self.requirements = {
            'numpy': '1.21.2',  # Versão específica para compatibilidade
            'pandas': '1.3.3',
            'plotly': '5.3.1',
            'streamlit': '1.2.0',
            'Flask': '2.0.1',
            'Flask-SQLAlchemy': '2.5.1',
            'Flask-Migrate': '3.1.0',
            'python-dotenv': '0.19.0',
            'openpyxl': '3.0.9',
            'scikit-learn': '0.24.2'
        }
        
    def check_installed_versions(self):
        """Verifica versões instaladas das dependências"""
        installed = {}
        for package in self.requirements:
            try:
                version = pkg_resources.get_distribution(package).version
                installed[package] = version
                logging.info(f"Versão instalada de {package}: {version}")
            except pkg_resources.DistributionNotFound:
                installed[package] = None
                logging.warning(f"Pacote {package} não encontrado")
        return installed

    def fix_dependencies(self):
        """Corrige versões das dependências"""
        logging.info("Iniciando correção de dependências...")
        
        # Primeiro, desinstalar versões conflitantes
        for package in self.requirements:
            try:
                subprocess.run(['pip', 'uninstall', '-y', package], 
                             capture_output=True, 
                             text=True)
                logging.info(f"Desinstalado: {package}")
            except Exception as e:
                logging.error(f"Erro ao desinstalar {package}: {str(e)}")

        # Instalar versões corretas
        for package, version in self.requirements.items():
            try:
                cmd = ['pip', 'install', f"{package}=={version}"]
                result = subprocess.run(cmd, 
                                     capture_output=True, 
                                     text=True)
                
                if result.returncode == 0:
                    logging.info(f"Instalado {package}=={version}")
                else:
                    logging.error(f"Erro ao instalar {package}: {result.stderr}")
                    # Tentar instalar sem versão específica
                    result = subprocess.run(['pip', 'install', package], 
                                         capture_output=True, 
                                         text=True)
                    if result.returncode == 0:
                        logging.info(f"Instalado {package} (última versão)")
            except Exception as e:
                logging.error(f"Erro ao instalar {package}: {str(e)}")

    def update_imports(self):
        """Atualiza imports nos arquivos Python"""
        files_to_update = {
            'analise_360.py': [
                'import numpy as np',
                'import pandas as pd',
                'import plotly.express as px',
                'import plotly.graph_objects as go',
                'import streamlit as st'
            ],
            'debug_excel.py': [
                'import numpy as np',
                'import pandas as pd'
            ]
        }

        for file, imports in files_to_update.items():
            try:
                if Path(file).exists():
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Atualizar imports
                    new_content = content
                    for imp in imports:
                        if imp not in content:
                            new_content = imp + '\n' + new_content

                    with open(file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    logging.info(f"Arquivo {file} atualizado")
            except Exception as e:
                logging.error(f"Erro ao atualizar {file}: {str(e)}")

    def run(self):
        """Executa todo o processo de verificação e correção"""
        print("Iniciando verificação de dependências...")
        
        # Verificar versões atuais
        current_versions = self.check_installed_versions()
        
        # Identificar problemas
        problems = []
        for package, required_version in self.requirements.items():
            if package not in current_versions or current_versions[package] != required_version:
                problems.append(package)

        if problems:
            print(f"\nEncontrados problemas com: {', '.join(problems)}")
            print("Iniciando correção...")
            self.fix_dependencies()
            self.update_imports()
        else:
            print("Todas as dependências estão corretas!")

        print("\nVerifique o arquivo dependencias.log para mais detalhes")

if __name__ == "__main__":
    manager = DependencyManager()
    manager.run() 