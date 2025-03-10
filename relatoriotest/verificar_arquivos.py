import os
from pathlib import Path

def verificar_estrutura():
    # Diretório base
    base_dir = Path('F:/relatoriotest')
    
    # Arquivos necessários
    arquivos_necessarios = {
        'codigo': 'analisar_dados_v5.py',
        'template': 'dashboard.html',
        'excel_julio': '(JULIO) LISTAS INDIVIDUAIS.xlsx',
        'excel_leandro': '(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx'
    }
    
    print("=== Verificando estrutura de arquivos ===\n")
    
    # Verificar diretório base
    if not base_dir.exists():
        print(f"✗ Diretório base não encontrado: {base_dir}")
        return False
    print(f"✓ Diretório base encontrado: {base_dir}")
    
    # Verificar arquivos
    todos_encontrados = True
    for key, filename in arquivos_necessarios.items():
        file_path = base_dir / filename
        if file_path.exists():
            print(f"✓ Arquivo encontrado: {filename}")
        else:
            print(f"✗ Arquivo não encontrado: {filename}")
            todos_encontrados = False
    
    # Verificar/criar diretório de saída
    output_dir = base_dir / 'dashboard_output'
    if not output_dir.exists():
        try:
            output_dir.mkdir()
            print(f"✓ Diretório dashboard_output criado: {output_dir}")
        except Exception as e:
            print(f"✗ Erro ao criar diretório dashboard_output: {e}")
            todos_encontrados = False
    else:
        print(f"✓ Diretório dashboard_output encontrado: {output_dir}")
    
    print("\n=== Resultado da verificação ===")
    if todos_encontrados:
        print("✓ Todos os arquivos necessários foram encontrados!")
    else:
        print("✗ Alguns arquivos estão faltando. Por favor, verifique os itens marcados com ✗ acima.")
    
    return todos_encontrados

if __name__ == "__main__":
    verificar_estrutura() 