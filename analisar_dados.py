import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import json
from datetime import datetime

class AnalisadorDados:
    def __init__(self):
        self.diretorios = [
            Path('F:/okok/data'),
            Path('F:/okok'),
            Path('.'),
            Path('./data')
        ]
        
        self.arquivos = {
            'julio': '(JULIO) LISTAS INDIVIDUAIS.xlsx',
            'leandro': '(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx'
        }
        
        self.colunas_situacao = [
            'SITUACAO', 'STATUS', 'SITUAÇÃO', 'ESTADO',
            'Status', 'Situacao', 'Situação', 'Estado'
        ]
        
    def encontrar_arquivos(self):
        """Localiza os arquivos Excel"""
        arquivos_encontrados = {}
        for diretorio in self.diretorios:
            if not diretorio.exists():
                continue
            for tipo, nome in self.arquivos.items():
                caminho = diretorio / nome
                if caminho.exists():
                    arquivos_encontrados[tipo] = str(caminho)
                    print(f"Arquivo {tipo} encontrado em: {caminho}")
        return arquivos_encontrados

    def encontrar_coluna_situacao(self, colunas):
        """Identifica a coluna de situação"""
        colunas = [str(col).strip().upper() for col in colunas]
        for nome in self.colunas_situacao:
            if nome.upper() in colunas:
                return nome
        return None

    def normalizar_dados(self, df):
        """Normaliza os dados"""
        df.columns = [str(col).strip().upper() for col in df.columns]
        coluna_situacao = self.encontrar_coluna_situacao(df.columns)
        
        if coluna_situacao:
            df = df.rename(columns={coluna_situacao: 'SITUACAO'})
            df['SITUACAO'] = df['SITUACAO'].fillna('NÃO INFORMADO')
            df['SITUACAO'] = df['SITUACAO'].astype(str).str.upper().str.strip()
            
            mapeamento = {
                'CONCLUÍDO': 'CONCLUIDO',
                'CONCLUIDA': 'CONCLUIDO',
                'FINALIZADO': 'CONCLUIDO',
                'EM ANDAMENTO': 'EM_ANDAMENTO',
                'ANDAMENTO': 'EM_ANDAMENTO'
            }
            df['SITUACAO'] = df['SITUACAO'].replace(mapeamento)
        
        return df, bool(coluna_situacao)

    def analisar_colaborador(self, df):
        """Analisa dados de um colaborador"""
        if df.empty:
            return None
            
        analise = {
            'total_registros': len(df),
            'situacoes': df['SITUACAO'].value_counts().to_dict(),
            'eficiencia': 0,
            'pendencias': 0
        }
        
        total = len(df)
        if 'CONCLUIDO' in analise['situacoes']:
            analise['eficiencia'] = (analise['situacoes']['CONCLUIDO'] / total * 100)
        
        if 'PENDENTE' in analise['situacoes']:
            analise['pendencias'] = analise['situacoes']['PENDENTE']
            
        return analise

    def analisar_grupo(self, caminho):
        """Analisa dados de um grupo"""
        try:
            xls = pd.ExcelFile(caminho)
            abas_validas = [aba for aba in xls.sheet_names 
                           if aba not in ["TESTE", "RELATÓRIO GERAL"]]
            
            analises = {}
            for aba in abas_validas:
                try:
                    df = pd.read_excel(caminho, sheet_name=aba)
                    if df.empty:
                        continue
                        
                    df, tem_situacao = self.normalizar_dados(df)
                    if tem_situacao:
                        analise = self.analisar_colaborador(df)
                        if analise:
                            analises[aba] = analise
                            print(f"\nAnálise de {aba}:")
                            print(f"- Total: {analise['total_registros']} registros")
                            print(f"- Eficiência: {analise['eficiencia']:.1f}%")
                            print(f"- Pendências: {analise['pendencias']}")
                            
                except Exception as e:
                    print(f"Erro ao analisar aba {aba}: {str(e)}")
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
            'grupos': {}
        }
        
        for grupo, caminho in arquivos.items():
            print(f"\n=== Análise do Grupo {grupo.title()} ===")
            analises = self.analisar_grupo(caminho)
            relatorio['grupos'][grupo] = analises
            
            # Calcular métricas do grupo
            if analises:
                total_registros = sum(a['total_registros'] for a in analises.values())
                media_eficiencia = np.mean([a['eficiencia'] for a in analises.values()])
                total_pendencias = sum(a['pendencias'] for a in analises.values())
                
                print(f"\nResumo do Grupo {grupo.title()}:")
                print(f"Total de colaboradores: {len(analises)}")
                print(f"Total de registros: {total_registros}")
                print(f"Média de eficiência: {media_eficiencia:.1f}%")
                print(f"Total de pendências: {total_pendencias}")
        
        # Salvar relatório
        with open('analise_grupos.json', 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
            print("\nRelatório salvo em 'analise_grupos.json'")

if __name__ == "__main__":
    print("Iniciando análise de dados...")
    analisador = AnalisadorDados()
    analisador.gerar_relatorio() 