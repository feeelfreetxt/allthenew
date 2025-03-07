import subprocess
import sys
import logging
from pathlib import Path
import json
from typing import Dict, List, Tuple
import os

class DependencyInstaller:
    def __init__(self):
        self.logger = self._setup_logging()
        self.pip_path = sys.executable.replace('python.exe', 'pip.exe')
        
        # Versões atualizadas compatíveis com Python 3.12
        self.installation_order = [
            ('pip', 'upgrade'),
            ('wheel', 'latest'),
            ('setuptools', 'latest'),
            ('protobuf', '3.20.0'),
            ('numpy', '1.26.4'),  # Versão mais recente compatível
            ('pandas', '2.2.0'),  # Versão mais recente compatível
            ('streamlit', '1.31.0'),  # Versão mais recente
            ('plotly', '5.18.0'),
            ('openpyxl', '3.1.2'),
            ('matplotlib', '3.8.2'),
            ('seaborn', '0.13.2')
        ]

    def _setup_logging(self) -> logging.Logger:
        """Configuração de logging"""
        logger = logging.getLogger('dependency_installer')
        logger.setLevel(logging.DEBUG)
        
        # Handler para arquivo
        fh = logging.FileHandler('installation_v2.log', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Handler para console
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    def run_pip_command(self, command: List[str]) -> Tuple[bool, str]:
        """Executa comando pip com tratamento de erros"""
        try:
            result = subprocess.run(
                [self.pip_path] + command,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def install_package(self, package: str, version: str) -> bool:
        """Instala pacote específico com retry"""
        max_retries = 3
        for attempt in range(max_retries):
            self.logger.info(f"Instalando {package} (tentativa {attempt + 1}/{max_retries})...")
            
            # Limpar cache do pip antes de tentar
            self.run_pip_command(['cache', 'purge'])
            
            # Desinstalar versão atual
            self.run_pip_command(['uninstall', '-y', package])
            
            # Instalar nova versão
            if version == 'latest':
                success, output = self.run_pip_command(['install', '--upgrade', package])
            elif version == 'upgrade':
                success, output = self.run_pip_command(['install', '--upgrade', 'pip'])
            else:
                success, output = self.run_pip_command(['install', f"{package}=={version}"])
            
            if success:
                self.logger.info(f"[OK] {package} instalado com sucesso")
                return True
            else:
                self.logger.warning(f"Tentativa {attempt + 1} falhou: {output}")
                
        self.logger.error(f"[ERRO] Falha ao instalar {package} após {max_retries} tentativas")
        return False

    def verify_imports(self) -> bool:
        """Verifica se todas as importações necessárias funcionam"""
        required_imports = [
            'numpy',
            'pandas',
            'streamlit',
            'plotly.express',
            'plotly.graph_objects',
            'matplotlib',
            'seaborn',
            'openpyxl'
        ]
        
        for module in required_imports:
            try:
                __import__(module)
                self.logger.info(f"[OK] {module} importado com sucesso")
            except ImportError as e:
                self.logger.error(f"[ERRO] Falha ao importar {module}: {str(e)}")
                return False
        return True

    def install_all(self) -> bool:
        """Instala todas as dependências"""
        self.logger.info("Iniciando instalação de dependências...")
        
        success = True
        for package, version in self.installation_order:
            if not self.install_package(package, version):
                success = False
                self.logger.error(f"[ERRO] Falha na instalação de {package}")
        
        if success and self.verify_imports():
            self.logger.info("[SUCESSO] Todas as dependências instaladas e verificadas")
            return True
        return False

if __name__ == "__main__":
    print("Iniciando instalação de dependências (v2)...")
    installer = DependencyInstaller()
    
    if installer.install_all():
        print("\n[SUCESSO] Instalação concluída!")
        print("\nPara executar o dashboard:")
        print("1. cd F:/okok")
        print("2. streamlit run dashboard_interativo.py")
    else:
        print("\n[ERRO] Alguns problemas ocorreram.")
        print("Verifique installation_v2.log para mais detalhes") 