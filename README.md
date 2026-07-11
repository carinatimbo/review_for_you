# Review For You - Ingestor & Scheduler

Este projeto é uma ferramenta de automação e ingestão de dados projetada para monitorar canais, descobrir novos conteúdos, extrair transcrições e gerenciar o estado do pipeline de dados de forma agendada.

## 🚀 Arquitetura e Estrutura do Projeto

O projeto está organizado da seguinte forma:

```text
review_for_you/
├── config/
│   └── canais.yaml         # Configuração dos canais/fontes a serem monitorados
├── docs/
│   └── CARTA_DO_PROJETO.md # Documentação de escopo e objetivos do projeto
├── ingestor/               # Módulo principal de ingestão de dados
│   ├── __init__.py
│   ├── discovery.py        # Descoberta de novos conteúdos/vídeos nos canais
│   ├── pipeline.py         # Orquestração do fluxo de dados (ETL)
│   ├── state.py            # Controle de estado (o que já foi processado)
│   └── transcript.py       # Extração e processamento de transcrições de áudio/texto
├── scheduler.py            # Script principal que gerencia o agendamento da rotina
├── requirements.txt        # Dependências do projeto
└── .gitignore              # Arquivos ignorados pelo Git (.venv, dados, etc)
```

# 🛠️ Componentes Principais
scheduler.py: O ponto de entrada da aplicação. Ele orquestra quando e como o pipeline deve rodar, aceitando parâmetros como --once para execuções únicas ou rodando em loops definidos.

ingestor/discovery.py: Responsável por varrer as fontes configuradas no canais.yaml para identificar novos itens que ainda não foram processados.

ingestor/transcript.py: Cuida da extração de texto/transcrições dos conteúdos descobertos.

ingestor/state.py: Garante a resiliência do projeto. Ele salva o estado atual para que o ingestor saiba de onde parar e não processe o mesmo conteúdo duas vezes.

ingestor/pipeline.py: Une todas as partes (descoberta, transcrição e estado) em um fluxo unificado de dados.

# 🔧 Pré-requisitos
Antes de começar, certifique-se de ter o Python 3.10+ instalado em sua máquina.

# 📦 Configuração
Crie e ative o seu ambiente virtual (.venv):
Bash
# No Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# No Linux/macOS
python -m venv .venv
source .venv/bin/activate
Instale as dependências necessárias:

Bash
pip install -r requirements.txt
Configure os canais ou fontes que deseja monitorar editando o arquivo:

Bash
config/canais.yaml
▶️ Como Executar
A execução do projeto deve ser feita a partir da raiz do projeto (review_for_you) utilizando o ambiente virtual ativo.

Execução Única (Modo Manual/Teste)
Para rodar o pipeline apenas uma vez para processar os dados atuais e encerrar:

Bash
python scheduler.py --once
Execução Contínua (Agendador Ativo)
Para deixar o agendador rodando continuamente em segundo plano (respeitando os intervalos definidos):

Bash
python scheduler.py
📄 Documentação Adicional
Para entender mais sobre as regras de negócio, objetivos e metas deste sistema, consulte o arquivo docs/CARTA_DO_PROJETO.md.