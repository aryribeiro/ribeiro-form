Obs.: caso o app esteja no modo "sleeping" (dormindo) ao entrar, basta clicar no botão que estará disponível e aguardar, para ativar o mesmo. 
<img width="736" height="778" alt="print" src="https://github.com/user-attachments/assets/897b8e7b-6147-465d-8590-a57186661eb2" />

Sistema completo de formulários web com painel administrativo e integração com Gmail. O web app **Ribeiro Forms** é uma alternativa open-source ao Google Forms e Microsoft Forms, construída com Python e Streamlit. Oferece um sistema completo de criação e gerenciamento de formulários com envio automático de respostas via email.

---

## ✨ Características

### 🎯 Funcionalidades Principais

- **Formulários Personalizáveis**: Crie campos customizados de diversos tipos
- **Envio Automático por Email**: Integração SMTP com Gmail e retry automático
- **Upload de Arquivos**: Suporte para múltiplos tipos de arquivo (25MB por arquivo)
- **Painel Administrativo**: Gerencie configurações, campos e visualize respostas
- **Exportação de Dados**: Exporte respostas em CSV ou envie por email
- **Persistência de Dados**: Banco SQLite para armazenamento confiável
- **Interface Moderna**: Design responsivo e intuitivo

### 🔒 Segurança

- ✅ Autenticação com hash SHA-256
- ✅ Validação rigorosa de uploads
- ✅ Proteção contra injeção de código
- ✅ Limite de tamanho de arquivos
- ✅ Tipos de arquivo restritos

### ⚡ Performance e Confiabilidade

- ✅ Retry automático com backoff exponencial
- ✅ Jitter para evitar throttling
- ✅ Cache em memória
- ✅ Operações idempotentes
- ✅ Tratamento robusto de erros

---

## 📋 Requisitos

- Python 3.8 ou superior
- Conta Gmail com verificação em duas etapas ativada
- Senha de aplicativo do Gmail

---

## 🚀 Instalação

### 1. Clone ou baixe o projeto

```bash
git clone https://github.com/aryribeiro/ribeiro-forms.git
cd ribeiro-forms
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações de Email SMTP (Gmail)
GMAIL_USER=seu_email@gmail.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx
RECIPIENT_EMAIL=email_destinatario@gmail.com

# Senha do Painel Admin (opcional - padrão: admin123)
ADMIN_PASSWORD=sua_senha_segura
```

### 5. Execute a aplicação

```bash
streamlit run ribeiro_forms.py
```

Acesse: `http://localhost:8501`

---

## 🔑 Configurando o Gmail

Para usar o envio automático de emails, você precisa de uma **Senha de App** do Gmail:

1. Acesse sua [Conta Google](https://myaccount.google.com)
2. Vá em **Segurança**
3. Ative a **Verificação em duas etapas** (se ainda não estiver ativa)
4. Acesse **Senhas de app**: https://myaccount.google.com/apppasswords
5. Selecione **App**: Email
6. Selecione **Dispositivo**: Outro (nome personalizado)
7. Digite "Ribeiro Forms" e clique em **Gerar**
8. Copie a senha de 16 caracteres gerada
9. Cole no arquivo `.env` na variável `GMAIL_PASSWORD`

⚠️ **Importante**: Use a senha de app gerada, NÃO sua senha normal do Gmail!

---

## 📖 Como Usar

### 👤 Para Usuários (Formulário Público)

1. Acesse a URL da aplicação
2. Preencha todos os campos obrigatórios (marcados com *)
3. Faça upload de arquivos se necessário
4. Aceite os termos de uso
5. Clique em **"📤 Enviar Formulário"**
6. Aguarde a confirmação de envio

### 🔐 Para Administradores

#### Acessar o Painel Admin

1. No sidebar, clique em **"🔑 Painel Admin"**
2. Digite a senha (padrão: `admin123`)
3. Clique em **"Entrar"**

#### Personalizar o Formulário

**Aba Configurações:**
- Altere o título e descrição do formulário
- Faça upload de logo/banner personalizado (PNG ou JPG)
- Altere a senha de administrador

**Aba Campos:**
- Visualize todos os campos cadastrados
- Adicione novos campos personalizados:
  - Texto simples
  - Área de texto (múltiplas linhas)
  - Número
  - Email
  - Telefone
  - Data
  - Seleção única (dropdown)
  - Múltipla escolha
  - Checkbox
- Remova campos não-obrigatórios
- Configure campos como obrigatórios ou opcionais

**Aba Respostas:**
- Visualize todas as respostas recebidas
- Veja detalhes de cada resposta (incluindo arquivos)
- Exporte todas as respostas em CSV
- Envie o CSV por email automaticamente

---

## 📁 Estrutura do Projeto

```
ribeiro-forms/
│
├── ribeiro_forms.py          # Aplicação principal
├── requirements.txt          # Dependências Python
├── .env                      # Variáveis de ambiente (criar)
├── README.md                 # Este arquivo
│
├── ribeiro_forms.db          # Banco de dados SQLite (auto-gerado)
├── uploads/                  # Arquivos enviados (auto-gerado)
└── logos/                    # Logos/banners (auto-gerado)
```

---

## 🎨 Campos Padrão

O formulário vem pré-configurado com os seguintes campos:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| Nome | Texto | ✅ Sim | Nome completo do usuário |
| Tel/WhatsApp | Telefone | ❌ Não | Número com máscara brasileira |
| E-mail | Email | ✅ Sim | Email com validação |
| Mensagem | Área de texto | ❌ Não | Campo multilinha para mensagens |
| Termos | Checkbox | ✅ Sim | Aceite de armazenamento de dados |
| Anexos | Upload | ❌ Não | Múltiplos arquivos permitidos |

---

## 📎 Tipos de Arquivo Aceitos

### Documentos
- PDF, DOCX, TXT, JSON, YAML, CSV

### Código
- PY (Python)

### Mídia
- MP3 (áudio), MP4 (vídeo)
- JPG, JPEG, PNG (imagens)

### Compactados
- ZIP, RAR

**Limite**: 25MB por arquivo

---

## 🔧 Configurações Avançadas

### Personalizar Limite de Arquivos

No arquivo `ribeiro_forms.py`, altere a constante:

```python
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
```

### Adicionar Novos Tipos de Arquivo

No arquivo `ribeiro_forms.py`, edite:

```python
ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'txt', 'json', 'yaml', 'csv',
    'py', 'mp3', 'mp4', 'jpg', 'jpeg', 'png', 'zip', 'rar',
    'svg', 'gif'  # Adicione aqui
}
```

### Alterar Tentativas de Retry no Email

```python
send_email_with_retry(subject, body, attachments, max_retries=3)  # Padrão: 3
```

---

## 📧 Formato do Email Enviado

Cada resposta enviada gera um email automático com:

- **Assunto**: "Nova resposta - Ribeiro Forms"
- **Corpo**: HTML formatado com todos os campos preenchidos
- **Data e Hora**: Timestamp da submissão
- **Anexos**: Todos os arquivos enviados pelo usuário

Exemplo de email:

```
Nova Resposta - Ribeiro Forms
Recebido em: 21/11/2025 às 14:30:00

Nome: João Silva
Tel/WhatsApp: (21) 98765-4321
E-mail: joao@email.com
Mensagem: Gostaria de mais informações sobre o produto.
Termos: ✓ Sim

Anexos: documento.pdf, imagem.jpg
```

---

## 🛠️ Solução de Problemas

### Erro: "Variáveis de ambiente de email não configuradas"

**Solução**: Verifique se o arquivo `.env` existe e contém todas as variáveis necessárias.

### Erro ao enviar email: "Authentication failed"

**Soluções**:
1. Verifique se a verificação em duas etapas está ativada
2. Gere uma nova senha de app no Gmail
3. Use a senha de app (16 caracteres), não sua senha normal
4. Verifique se não há espaços extras no `.env`

### Erro: "Arquivo muito grande"

**Solução**: O arquivo excede 25MB. Comprima ou divida o arquivo.

### Erro: "Tipo de arquivo não permitido"

**Solução**: Verifique se a extensão do arquivo está na lista de tipos aceitos.

### Formulário não salva respostas

**Solução**: Verifique as permissões de escrita na pasta onde está o `ribeiro_forms.db`

---

## 🚀 Deploy em Produção

### Streamlit Cloud (Recomendado)

1. Faça push do código para GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Configure os **Secrets** (equivalente ao `.env`):
   ```toml
   GMAIL_USER = "seu_email@gmail.com"
   GMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
   RECIPIENT_EMAIL = "destino@email.com"
   ADMIN_PASSWORD = "senha_segura"
   ```
5. Deploy automático!

### Servidor Próprio (VPS/Cloud)

```bash
# Instale as dependências
pip install -r requirements.txt

# Execute com nohup (mantém rodando após logout)
nohup streamlit run app.py --server.port 8501 &

# Ou use PM2
pm2 start "streamlit run app.py" --name ribeiro-forms
```

**Recomendações**:
- Use HTTPS (configure um proxy reverso com Nginx)
- Configure backups automáticos do banco de dados
- Monitore o espaço em disco (pasta `uploads/`)
- Use variáveis de ambiente em vez de `.env` em produção

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abrir um Pull Request

---

## 👨‍💻 Autor


Desenvolvido com ❤️ usando Python e Streamlit por **Ary Ribeiro**: aryribeiro@gmail.com



