# Dashboard de Análise de Contratos

Sistema de análise e visualização de dados de contratos com dashboard interativo.

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Navegador web moderno

## Instalação Local

1. Clone o repositório ou baixe os arquivos
2. Crie um ambiente virtual Python:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente:
- Copie o arquivo `.env.example` para `.env`
- Ajuste as variáveis conforme necessário

6. Execute o servidor:
```bash
python app.py
```

7. Acesse o dashboard em `http://localhost:8000`

## Deploy no Google Cloud Platform (Gratuito)

1. Crie uma conta no Google Cloud Platform (GCP)
2. Instale o Google Cloud SDK
3. Configure o projeto:
```bash
gcloud init
```

4. Deploy no Cloud Run:
```bash
gcloud run deploy dashboard-contratos \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Deploy no Heroku (Gratuito)

1. Crie uma conta no Heroku
2. Instale o Heroku CLI
3. Faça login:
```bash
heroku login
```

4. Crie um novo app:
```bash
heroku create dashboard-contratos
```

5. Configure as variáveis de ambiente:
```bash
heroku config:set DB_PATH=relatorio_dashboard.db
```

6. Deploy:
```bash
git push heroku main
```

## Deploy no Railway (Gratuito)

1. Crie uma conta no Railway (railway.app)
2. Conecte seu repositório GitHub
3. Configure as variáveis de ambiente no dashboard do Railway
4. O deploy será automático a cada push

## Estrutura do Projeto

```
.
├── app.py                 # Aplicação FastAPI
├── analisar_dados_v5.py   # Lógica de análise de dados
├── requirements.txt       # Dependências Python
├── .env                  # Variáveis de ambiente
├── templates/            # Templates HTML
│   └── dashboard.html    # Template do dashboard
└── static/              # Arquivos estáticos
```

## Manutenção

### Backup do Banco de Dados

O banco SQLite é salvo localmente. Para backup:
1. Copie o arquivo `relatorio_dashboard.db`
2. Armazene em local seguro

### Atualização de Dados

Os dados são atualizados:
- Automaticamente a cada 30 segundos (status)
- Manualmente pelo botão "Atualizar Dados"
- Via API endpoint POST `/atualizar`

## Solução de Problemas

### Erro de Conexão com Banco de Dados
1. Verifique se o arquivo do banco existe
2. Confirme as permissões de escrita
3. Teste a conexão manualmente:
```python
import sqlite3
conn = sqlite3.connect('relatorio_dashboard.db')
```

### Erro no Carregamento de Dados
1. Verifique o formato dos arquivos Excel
2. Confirme se as colunas necessárias existem
3. Verifique os logs do servidor

### Problemas de Performance
1. Otimize as consultas SQL
2. Implemente cache quando necessário
3. Monitore o uso de memória

## API Endpoints

- `GET /`: Dashboard principal
- `GET /status`: Status do servidor e dados
- `POST /atualizar`: Atualiza os dados

## Contribuindo

1. Fork o repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Suporte

Para suporte, abra uma issue no repositório ou contate o mantenedor. 