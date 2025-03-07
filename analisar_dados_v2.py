import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import warnings

# Suprimir avisos específicos do openpyxl
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

class AnalisadorDados:
    def __init__(self):
        # Usar apenas o primeiro diretório válido encontrado
        self.diretorios_ordem = [
            Path('F:/okok/data'),
            Path('F:/okok'),
            Path('.'),
            Path('./data')
        ]
        
        self.diretorio = self.encontrar_diretorio_valido()
        
        self.arquivos = {
            'julio': '(JULIO) LISTAS INDIVIDUAIS.xlsx',
            'leandro': '(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx'
        }
        
        self.colunas_situacao = [
            'SITUACAO', 'STATUS', 'SITUAÇÃO', 'ESTADO',
            'Status', 'Situacao', 'Situação', 'Estado'
        ]

    def encontrar_diretorio_valido(self):
        """Encontra o primeiro diretório válido que contém os arquivos"""
        for diretorio in self.diretorios_ordem:
            if diretorio.exists():
                print(f"Usando diretório: {diretorio}")
                return diretorio
        raise FileNotFoundError("Nenhum diretório válido encontrado")

    def encontrar_arquivos(self):
        """Localiza os arquivos Excel sem duplicatas"""
        arquivos_encontrados = {}
        
        for tipo, nome in self.arquivos.items():
            caminho = self.diretorio / nome
            if caminho.exists():
                arquivos_encontrados[tipo] = str(caminho)
                print(f"Arquivo {tipo}: {caminho}")
            else:
                print(f"AVISO: Arquivo {tipo} não encontrado em {caminho}")
                
        return arquivos_encontrados

    def carregar_excel(self, caminho: str) -> pd.DataFrame:
        """Carrega arquivo Excel com tratamento de erros"""
        try:
            return pd.read_excel(
                caminho,
                parse_dates=True,
                date_parser=lambda x: pd.to_datetime(x, errors='coerce')
            )
        except Exception as e:
            print(f"Erro ao carregar {caminho}: {e}")
            return pd.DataFrame()

    def analisar_grupo(self, caminho):
        """Analisa dados de um grupo"""
        try:
            xls = pd.ExcelFile(caminho)
            abas_validas = [aba for aba in xls.sheet_names 
                           if aba not in ["TESTE", "RELATÓRIO GERAL"]]
            
            analises = {}
            print("\nProcessando abas:")
            for aba in abas_validas:
                print(f"- {aba}: ", end="")
                try:
                    df = pd.read_excel(
                        caminho, 
                        sheet_name=aba,
                        parse_dates=True,
                        date_parser=lambda x: pd.to_datetime(x, errors='coerce')
                    )
                    
                    if df.empty:
                        print("Vazia")
                        continue
                        
                    df, tem_situacao = self.normalizar_dados(df)
                    if tem_situacao:
                        analise = self.analisar_colaborador(df)
                        if analise:
                            analises[aba] = analise
                            print(f"OK ({analise['total_registros']} registros)")
                        else:
                            print("Sem dados válidos")
                    else:
                        print("Sem coluna de situação")
                            
                except Exception as e:
                    print(f"Erro: {str(e)}")
                    continue
                    
            return analises
            
        except Exception as e:
            print(f"Erro ao analisar arquivo: {str(e)}")
            return {}

    def gerar_relatorio(self):
        """Gera relatório completo"""
        arquivos = self.encontrar_arquivos()
        if not arquivos:
            print("Nenhum arquivo encontrado!")
            return
            
        relatorio = {
            'data_analise': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'diretorio': str(self.diretorio),
            'grupos': {}
        }
        
        for grupo, caminho in arquivos.items():
            print(f"\n=== Análise do Grupo {grupo.title()} ===")
            analises = self.analisar_grupo(caminho)
            relatorio['grupos'][grupo] = analises
            
            if analises:
                self.imprimir_resumo_grupo(grupo, analises)
        
        # Salvar relatório
        arquivo_saida = self.diretorio / 'analise_grupos.json'
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
            print(f"\nRelatório salvo em: {arquivo_saida}")

    def imprimir_resumo_grupo(self, grupo: str, analises: dict):
        """Imprime resumo formatado do grupo"""
        total_registros = sum(a['total_registros'] for a in analises.values())
        media_eficiencia = np.mean([a['eficiencia'] for a in analises.values()])
        total_pendencias = sum(a['pendencias'] for a in analises.values())
        
        print(f"\nResumo do Grupo {grupo.title()}:")
        print(f"{'Total de colaboradores:':<25} {len(analises)}")
        print(f"{'Total de registros:':<25} {total_registros}")
        print(f"{'Média de eficiência:':<25} {media_eficiencia:.1f}%")
        print(f"{'Total de pendências:':<25} {total_pendencias}")

if __name__ == "__main__":
    try:
        print("=== Iniciando Análise de Dados ===")
        analisador = AnalisadorDados()
        analisador.gerar_relatorio()
        print("\n=== Análise Concluída ===")
    except Exception as e:
        print(f"\nERRO CRÍTICO: {str(e)}") 