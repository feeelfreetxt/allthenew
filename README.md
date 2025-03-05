# Sistema de Análise de Colaboradores

Sistema completo para análise de desempenho e geração de relatórios de colaboradores.

## Estrutura do Projeto

- `pipeline_dashboard.py`: Dashboard principal que integra todas as análises
- `analise_paralela.py`: Análise paralela de múltiplos colaboradores
- `analise_detalhada.py`: Análise detalhada individual de colaboradores
- `validacao_metricas.py`: Validação e cálculo de métricas de qualidade
- `debug_excel.py`: Funções auxiliares para manipulação de arquivos Excel

## Funcionalidades

- Análise de métricas de qualidade
- Geração de relatórios HTML responsivos
- Dashboard interativo com gráficos
- Análise paralela de múltiplos arquivos
- Validação de dados e métricas

## Como Usar

1. Configure o ambiente:

## Tecnologias Utilizadas

- Backend: Python/Flask
- Frontend: HTML5, CSS3, JavaScript
- Visualização de Dados: Plotly
- Análise de Dados: Pandas, NumPy
- UI Framework: Bootstrap 5
- Processamento de Excel: OpenPyXL

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/data-analytics-saas.git
cd data-analytics-saas
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração

1. Crie um arquivo `.env` na raiz do projeto:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui
```

2. Configure os arquivos de dados:
- Coloque seus arquivos Excel na pasta raiz do projeto
- Verifique se os nomes dos arquivos correspondem aos esperados no código

## Uso

1. Inicie o servidor de desenvolvimento:
```bash
flask run
```

2. Acesse a aplicação em seu navegador:
```
http://localhost:5000
```

## Estrutura do Projeto

```
data-analytics-saas/
├── app.py                 # Aplicação Flask principal
├── auditoria_dados.py     # Módulo de auditoria de dados
├── analise_360.py         # Módulo de análise 360
├── static/
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── js/
│       └── main.js       # JavaScript principal
├── templates/
│   └── index.html        # Template principal
├── requirements.txt       # Dependências do projeto
└── README.md             # Este arquivo
```

## API Endpoints

- `GET /`: Página principal do dashboard
- `POST /api/data`: Obtém dados filtrados por seção
- `GET /api/update_title/<section>`: Atualiza o título baseado na seção

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

Para suporte, envie um email para suporte@exemplo.com ou abra uma issue no GitHub.
