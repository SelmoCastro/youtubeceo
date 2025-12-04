# Guia de Implantação (Deployment) - TesteWeb

Este guia explica como colocar seu projeto online usando o **Streamlit Community Cloud** (recomendado e gratuito).

## 1. Preparação (Já realizada)
Eu já realizei as seguintes alterações no seu projeto:
- Atualizei o `requirements.txt` com todas as dependências necessárias.
- Criei um arquivo `.gitignore` para impedir que arquivos sensíveis (senhas, chaves de API) sejam enviados para o GitHub.
- Atualizei o `auth.py` para aceitar a URL de redirecionamento correta quando estiver online.

## 2. GitHub
Para usar o Streamlit Cloud, seu código precisa estar no GitHub.

1.  Crie um novo repositório no GitHub (pode ser privado).
2.  Envie os arquivos do seu projeto para lá (exceto os ignorados pelo `.gitignore`).
    ```bash
    git init
    git add .
    git commit -m "Preparando para deploy"
    git branch -M main
    git remote add origin <SEU_LINK_DO_GITHUB>
    git push -u origin main
    ```

## 3. Streamlit Community Cloud
1.  Acesse [share.streamlit.io](https://share.streamlit.io/).
2.  Faça login com seu GitHub.
3.  Clique em **"New app"**.
4.  Selecione o repositório, a branch (`main`) e o arquivo principal (`app.py`).
5.  **ANTES** de clicar em "Deploy", clique em **"Advanced settings"** (ou "Secrets").

## 4. Configuração de Segredos (Secrets)
No painel do Streamlit Cloud, você precisa configurar as variáveis de ambiente. Copie e cole o seguinte, preenchendo com seus dados:

```toml
# Supabase (Pegue no painel do Supabase > Project Settings > API)
SUPABASE_URL = "SUA_URL_DO_SUPABASE"
SUPABASE_KEY = "SUA_CHAVE_ANON_DO_SUPABASE"

# URL do seu app (Você saberá após o deploy, ex: https://seu-app.streamlit.app)
# Importante para o login do Google funcionar
REDIRECT_URL = "https://seu-app-nome.streamlit.app"
```

## 5. Autenticação do YouTube
A autenticação do YouTube requer um navegador local, o que não funciona na nuvem.
**Solução:**
1.  Rode o projeto **localmente** (`streamlit run app.py`).
2.  Faça login e autentique o canal do YouTube.
3.  O sistema salvará o token no Supabase.
4.  Como o app na nuvem também lê do Supabase, ele funcionará automaticamente!

## 6. Deploy
Clique em **"Deploy!"**. O Streamlit vai instalar as dependências e iniciar seu app.

---
**Observação:** Se você precisar adicionar outras chaves de API (OpenAI, Gemini, etc.), adicione-as também na área de "Secrets" do Streamlit Cloud ou configure-as através da interface do próprio aplicativo (que as salvará no Supabase).
