# YouTube SEO Manager 🚀

Este projeto evoluiu para uma aplicação completa de gerenciamento e otimização de canais do YouTube, com um dashboard interativo em Streamlit e relatórios detalhados em Excel. Ele utiliza IA (Google Gemini) para analisar e otimizar títulos, descrições e tags, visando aumentar o CTR (Click-Through Rate) e o engajamento.

## ✨ Funcionalidades

### 🖥️ Dashboard Interativo (Streamlit)
*   **🛠️ Configuração Simplificada**: Tela de "Primeiro Acesso" para configurar o banco de dados sem editar arquivos.
*   **🔐 Autenticação Segura**: Login e cadastro via Supabase, com suporte a Google OAuth e persistência de sessão.
*   **🚀 Performance**: Visualização de métricas do canal (Views, Subs, Likes) com gráficos interativos e cache inteligente para economia de cota.
*   **💰 Monetização**: Acompanhamento do progresso para monetização (1.000 inscritos e 4.000 horas) e simulador de receita.
*   **📤 Upload & Otimização**: Upload de vídeos diretamente para o YouTube com metadados gerados por IA.
*   **✨ Otimização de Existentes**:
    *   **Modo Manual**: Selecione vídeos individualmente para otimizar.
    *   **Modo Automático**: Agende otimizações a cada 6h, 12h ou 24h.
*   **📝 Revisões Pendentes**: Interface para aprovar ou rejeitar sugestões de IA antes de aplicar no canal.
*   **🔌 Integrações**: Gerencie chaves de API (Supabase, Google Gemini, OpenAI, etc.) em uma interface centralizada.

### 📊 Relatórios em Excel
*   Gera um arquivo `channel_report.xlsx` com:
    *   Visão geral de todos os vídeos.
    *   Análise de evolução diária (Views e Subs).
    *   Gráficos de correlação (Views vs CTR).

### 🤖 Automação & IA
*   **Análise Contínua**: Script em segundo plano monitora o canal.
*   **Sugestões Inteligentes**: A IA propõe melhorias apenas para vídeos com CTR baixo (< 4.5%).
*   **Gestão de Cota**: Tratamento inteligente de erros de cota da API do YouTube (reset às 05:00 BRT).

## 🛠️ Instalação

1.  Clone o repositório e entre na pasta.
2.  Instale as dependências:

```bash
pip install -r requirements.txt
```

## 🔑 Configuração Inicial

O aplicativo possui dois modos de distribuição:

### 1. Modelo SaaS (Pré-configurado)
Se você recebeu este software já configurado:
1.  Apenas inicie o aplicativo.
2.  Faça login ou crie sua conta na tela inicial.
3.  O banco de dados já está conectado.

### 2. Modelo Open Source (Nova Instalação)
Se você baixou o código do zero ou apagou o arquivo `api_config.json`:
1.  Ao iniciar o app, você verá a tela **🛠️ Configuração Inicial**.
2.  Insira a **Project URL** e a **Anon Key** do seu projeto Supabase.
3.  O app criará o arquivo de configuração automaticamente e reiniciará.

### Requisitos Externos
*   **Google Cloud**: Credenciais OAuth (`client_secret.json`) para acesso à API do YouTube.
*   **Supabase**: Projeto criado com tabelas de autenticação e dados (SQL disponível em `supabase_schema.sql`).
*   **Google Gemini**: Chave de API para as otimizações de IA.

## 🚀 Como Usar

### Iniciar o Dashboard
Rode o comando abaixo para abrir a interface no seu navegador:

```bash
streamlit run app.py
```

### Gerar Relatório Excel
Para gerar um relatório pontual sem abrir o dashboard:

```bash
python generate_excel_report.py
```

## 📂 Estrutura de Arquivos
*   `app.py`: Aplicação principal (Dashboard Streamlit).
*   `auth.py`: Módulo de autenticação e configuração.
*   `database.py`: Camada de acesso a dados.
*   `youtube_seo_optimizer.py`: Script de automação em segundo plano.
*   `generate_excel_report.py`: Gerador de relatórios Excel.
*   `requirements.txt`: Lista de dependências.
*   `api_config.json`: Armazena configurações de API (gerado pelo app).
*   `scheduler_config.json`: Configurações de agendamento automático.
*   `.session`: Arquivo temporário de sessão (não compartilhar).
