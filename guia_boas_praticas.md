# Guia de Boas Práticas: Análise de Dados com Python

## 1. Estrutura de Diretórios e Arquivos

### 1.1 Organização Recomendada
```
projeto/
│
├── data/                  # Dados brutos
├── notebooks/            # Jupyter notebooks para análises
├── src/                  # Código fonte Python
├── tests/               # Testes unitários
└── config/              # Arquivos de configuração
```

### 1.2 Configuração de Ambiente
```python
from pathlib import Path
import logging

# Configurar estrutura de diretórios
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Configurar logging
logging.basicConfig(
    filename='analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
```

## 2. Tratamento de Erros Comuns

### 2.1 Arquivos Excel
```python
def carregar_excel(caminho: Path) -> pd.DataFrame:
    """
    Carrega arquivo Excel com tratamento de erros
    """
    try:
        # Suprimir avisos específicos do openpyxl
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings('ignore', category=UserWarning)
            return pd.read_excel(caminho)
    except Exception as e:
        logging.error(f"Erro ao carregar {caminho}: {e}")
        return pd.DataFrame()
```

### 2.2 Busca de Arquivos
```python
def localizar_arquivo(nome: str, diretorios: list) -> Path:
    """
    Localiza arquivo evitando duplicatas
    """
    arquivos_encontrados = []
    for diretorio in diretorios:
        caminho = Path(diretorio) / nome
        if caminho.exists():
            arquivos_encontrados.append(caminho)
    
    if not arquivos_encontrados:
        raise FileNotFoundError(f"Arquivo {nome} não encontrado")
        
    # Retorna o primeiro arquivo encontrado
    return arquivos_encontrados[0]
```

## 3. Normalização de Dados

### 3.1 Padronização de Colunas
```python
def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Padroniza nomes de colunas
    """
    mapeamento = {
        'SITUAÇÃO': 'SITUACAO',
        'STATUS': 'SITUACAO',
        'ESTADO': 'SITUACAO'
    }
    
    df.columns = [col.strip().upper() for col in df.columns]
    return df.rename(columns=mapeamento)
```

### 3.2 Limpeza de Dados
```python
def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e padroniza dados
    """
    if 'SITUACAO' in df.columns:
        df['SITUACAO'] = (df['SITUACAO']
            .fillna('NÃO INFORMADO')
            .str.upper()
            .str.strip()
            .replace({
                'CONCLUÍDO': 'CONCLUIDO',
                'EM ANDAMENTO': 'EM_ANDAMENTO'
            })
        )
    return df
```

## 4. Análise e Validação

### 4.1 Validação de Dados
```python
def validar_dados(df: pd.DataFrame) -> bool:
    """
    Valida estrutura e conteúdo dos dados
    """
    colunas_requeridas = ['SITUACAO', 'DATA']
    if not all(col in df.columns for col in colunas_requeridas):
        return False
        
    if df.empty:
        return False
        
    return True
```

### 4.2 Métricas de Análise
```python
def calcular_metricas(df: pd.DataFrame) -> dict:
    """
    Calcula métricas principais
    """
    return {
        'total_registros': len(df),
        'eficiencia': (df['SITUACAO'] == 'CONCLUIDO').mean() * 100,
        'pendencias': (df['SITUACAO'] == 'PENDENTE').sum()
    }
```

## 5. Boas Práticas

### 5.1 Logging Efetivo
```python
def processar_dados(df: pd.DataFrame, nome: str) -> dict:
    """
    Processa dados com logging adequado
    """
    logger = logging.getLogger(__name__)
    
    try:
        df = limpar_dados(df)
        if not validar_dados(df):
            logger.warning(f"Dados inválidos: {nome}")
            return {}
            
        metricas = calcular_metricas(df)
        logger.info(f"Processamento concluído: {nome}")
        return metricas
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        return {}
```

### 5.2 Cache Inteligente
```python
from functools import lru_cache

@lru_cache(maxsize=32)
def analisar_dados(caminho: str) -> dict:
    """
    Análise com cache para performance
    """
    df = carregar_excel(Path(caminho))
    return processar_dados(df, caminho)
```

## 6. Execução e Monitoramento

### 6.1 Script Principal
```python
def main():
    logger = logging.getLogger(__name__)
    logger.info("Iniciando análise")
    
    try:
        # Configuração
        config = carregar_configuracao()
        
        # Processamento
        resultados = processar_dados(config)
        
        # Relatório
        gerar_relatorio(resultados)
        
    except Exception as e:
        logger.error(f"Erro na execução: {str(e)}")
        raise
```

### 6.2 Monitoramento
```python
def monitorar_execucao():
    """
    Monitora uso de recursos
    """
    import psutil
    
    processo = psutil.Process()
    memoria = processo.memory_info().rss / 1024 / 1024
    
    logging.info(f"Uso de memória: {memoria:.2f} MB")
```

## 7. Recomendações Finais

1. Sempre use controle de versão (git)
2. Documente seu código
3. Implemente testes unitários
4. Use tipagem estática quando possível
5. Mantenha logs organizados
6. Faça backup dos dados
7. Monitore performance
8. Revise código em equipe 