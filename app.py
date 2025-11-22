import streamlit as st
import sqlite3
import json
import os
import hashlib
import smtplib
import time
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import base64
import io
import csv
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ============================================================================
# CONFIGURAÇÕES E CONSTANTES
# ============================================================================

ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'txt', 'json', 'yaml', 'csv',
    'py', 'mp3', 'mp4', 'jpg', 'jpeg', 'png', 'zip', 'rar'
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
DB_PATH = "ribeiro_forms.db"
UPLOAD_DIR = "uploads"
LOGO_DIR = "logos"

# Criar diretórios necessários
Path(UPLOAD_DIR).mkdir(exist_ok=True)
Path(LOGO_DIR).mkdir(exist_ok=True)

# ============================================================================
# BANCO DE DADOS
# ============================================================================

def init_db():
    """Inicializa o banco de dados SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela de configurações
    c.execute('''CREATE TABLE IF NOT EXISTS config
                 (key TEXT PRIMARY KEY, value TEXT)''')
    
    # Tabela de campos personalizados
    c.execute('''CREATE TABLE IF NOT EXISTS fields
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  label TEXT NOT NULL,
                  field_type TEXT NOT NULL,
                  required INTEGER DEFAULT 0,
                  options TEXT,
                  position INTEGER,
                  is_default INTEGER DEFAULT 0)''')
    
    # Tabela de respostas
    c.execute('''CREATE TABLE IF NOT EXISTS responses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  data TEXT NOT NULL,
                  files TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Inicializar campos padrão se não existirem
    c.execute("SELECT COUNT(*) FROM fields")
    if c.fetchone()[0] == 0:
        default_fields = [
            ('nome', 'Nome', 'text', 1, None, 1, 1),
            ('telefone', 'Tel/WhatsApp', 'phone', 0, None, 2, 1),
            ('email', 'E-mail', 'email', 1, None, 3, 1),
            ('mensagem', 'Mensagem', 'textarea', 0, None, 4, 1),
            ('termos', 'Aceito que meus dados sejam armazenados para comunicação futura', 'checkbox', 1, None, 5, 1),
            ('anexos', 'Upload de Anexos', 'file', 0, None, 6, 1)
        ]
        c.executemany('''INSERT INTO fields 
                        (name, label, field_type, required, options, position, is_default)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', default_fields)
    
    # Configurações iniciais
    c.execute("SELECT value FROM config WHERE key='title'")
    if not c.fetchone():
        c.execute("INSERT INTO config VALUES ('title', 'Ribeiro Forms')")
        c.execute("INSERT INTO config VALUES ('description', 'Preencha o formulário abaixo')")
        
        # Hash da senha padrão
        default_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        hashed = hashlib.sha256(default_password.encode()).hexdigest()
        c.execute("INSERT INTO config VALUES ('admin_password', ?)", (hashed,))
    
    conn.commit()
    conn.close()

# ============================================================================
# FUNÇÕES DE BANCO DE DADOS
# ============================================================================

def get_config(key: str) -> Optional[str]:
    """Busca valor de configuração"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE key=?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_config(key: str, value: str):
    """Define valor de configuração"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_fields() -> List[Dict]:
    """Retorna todos os campos ordenados por posição"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM fields ORDER BY position")
    fields = []
    for row in c.fetchall():
        fields.append({
            'id': row[0],
            'name': row[1],
            'label': row[2],
            'field_type': row[3],
            'required': bool(row[4]),
            'options': json.loads(row[5]) if row[5] else None,
            'position': row[6],
            'is_default': bool(row[7])
        })
    conn.close()
    return fields

def add_field(name: str, label: str, field_type: str, required: bool, options: Optional[List[str]] = None):
    """Adiciona novo campo"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT MAX(position) FROM fields")
    max_pos = c.fetchone()[0] or 0
    
    options_json = json.dumps(options) if options else None
    c.execute('''INSERT INTO fields (name, label, field_type, required, options, position)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (name, label, field_type, int(required), options_json, max_pos + 1))
    conn.commit()
    conn.close()

def delete_field(field_id: int):
    """Remove campo"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM fields WHERE id=? AND is_default=0", (field_id,))
    conn.commit()
    conn.close()

def update_field_positions(field_ids: List[int]):
    """Atualiza posições dos campos"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for pos, field_id in enumerate(field_ids, 1):
        c.execute("UPDATE fields SET position=? WHERE id=?", (pos, field_id))
    conn.commit()
    conn.close()

def save_response(data: Dict, files: List[str]):
    """Salva resposta no banco"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO responses (data, files) VALUES (?, ?)",
              (json.dumps(data), json.dumps(files)))
    conn.commit()
    response_id = c.lastrowid
    conn.close()
    return response_id

def get_responses() -> List[Dict]:
    """Retorna todas as respostas"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM responses ORDER BY created_at DESC")
    responses = []
    for row in c.fetchall():
        responses.append({
            'id': row[0],
            'data': json.loads(row[1]),
            'files': json.loads(row[2]) if row[2] else [],
            'created_at': row[3]
        })
    conn.close()
    return responses

# ============================================================================
# FUNÇÕES DE EMAIL COM RETRY E BACKOFF
# ============================================================================

def send_email_with_retry(subject: str, body: str, attachments: List[str], max_retries: int = 3):
    """Envia email com retry exponencial e jitter"""
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_PASSWORD')
    recipient = os.getenv('RECIPIENT_EMAIL')
    
    if not all([gmail_user, gmail_password, recipient]):
        raise ValueError("Variáveis de ambiente de email não configuradas")
    
    for attempt in range(max_retries):
        try:
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            # Anexar arquivos
            for filepath in attachments:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition',
                                      f'attachment; filename={os.path.basename(filepath)}')
                        msg.attach(part)
            
            # Conectar e enviar
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_user, gmail_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                # Backoff exponencial com jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                raise e

def format_email_body(data: Dict, fields: List[Dict]) -> str:
    """Formata corpo do email em HTML"""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; }}
            .content {{ padding: 20px; }}
            .field {{ margin: 15px 0; }}
            .label {{ font-weight: bold; color: #333; }}
            .value {{ color: #666; margin-left: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Nova Resposta - Ribeiro Forms</h2>
            <p>Recebido em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
        </div>
        <div class="content">
    """
    
    for field in fields:
        if field['name'] in data and field['field_type'] != 'file':
            value = data[field['name']]
            if field['field_type'] == 'checkbox':
                value = "✓ Sim" if value else "✗ Não"
            html += f'''
            <div class="field">
                <span class="label">{field['label']}:</span>
                <span class="value">{value}</span>
            </div>
            '''
    
    html += """
        </div>
    </body>
    </html>
    """
    return html

# ============================================================================
# FUNÇÕES DE UPLOAD E VALIDAÇÃO
# ============================================================================

def validate_file(uploaded_file) -> tuple[bool, str]:
    """Valida arquivo enviado"""
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f"Arquivo muito grande. Máximo: 25MB"
    
    ext = uploaded_file.name.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Tipo de arquivo não permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, ""

def save_uploaded_file(uploaded_file, response_id: int) -> str:
    """Salva arquivo enviado e retorna o caminho"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{response_id}_{timestamp}_{uploaded_file.name}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath

# ============================================================================
# FUNÇÕES DE INTERFACE - FORMULÁRIO PÚBLICO
# ============================================================================

def render_form():
    """Renderiza o formulário público"""
    # Logo/Banner
    logo_path = get_config('logo_path')
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    
    # Título e descrição
    title = get_config('title') or '📝 Ribeiro Forms'
    description = get_config('description') or 'Preencha o formulário abaixo:'
    
    st.title(title)
    st.markdown(description)
    
    # Buscar campos
    fields = get_fields()
    
    # Formulário
    with st.form("main_form", clear_on_submit=True):
        form_data = {}
        uploaded_files = []
        
        for field in fields:
            if field['field_type'] == 'text':
                value = st.text_input(
                    field['label'],
                    key=f"field_{field['id']}",
                    help="Campo obrigatório" if field['required'] else None
                )
                form_data[field['name']] = value
                
            elif field['field_type'] == 'phone':
                value = st.text_input(
                    field['label'],
                    key=f"field_{field['id']}",
                    placeholder="(00) 00000-0000",
                    help="Formato: (00) 00000-0000"
                )
                form_data[field['name']] = value
                
            elif field['field_type'] == 'email':
                value = st.text_input(
                    field['label'],
                    key=f"field_{field['id']}",
                    help="Campo obrigatório" if field['required'] else None
                )
                form_data[field['name']] = value
                
            elif field['field_type'] == 'textarea':
                value = st.text_area(
                    field['label'],
                    key=f"field_{field['id']}",
                    height=150
                )
                form_data[field['name']] = value
                
            elif field['field_type'] == 'number':
                value = st.number_input(
                    field['label'],
                    key=f"field_{field['id']}"
                )
                form_data[field['name']] = value
                
            elif field['field_type'] == 'date':
                value = st.date_input(
                    field['label'],
                    key=f"field_{field['id']}"
                )
                form_data[field['name']] = str(value)
                
            elif field['field_type'] == 'select':
                if field['options']:
                    value = st.selectbox(
                        field['label'],
                        options=field['options'],
                        key=f"field_{field['id']}"
                    )
                    form_data[field['name']] = value
                    
            elif field['field_type'] == 'multiselect':
                if field['options']:
                    value = st.multiselect(
                        field['label'],
                        options=field['options'],
                        key=f"field_{field['id']}"
                    )
                    form_data[field['name']] = ', '.join(value)
                    
            elif field['field_type'] == 'checkbox':
                value = st.checkbox(
                    field['label'],
                    key=f"field_{field['id']}"
                )
                form_data[field['name']] = value
                
            elif field['field_type'] == 'file':
                files = st.file_uploader(
                    field['label'],
                    accept_multiple_files=True,
                    key=f"field_{field['id']}",
                    help=f"Formatos aceitos: {', '.join(ALLOWED_EXTENSIONS)}"
                )
                if files:
                    uploaded_files = files
        
        submitted = st.form_submit_button("📤 Enviar Formulário", use_container_width=True)
        
        if submitted:
            # Validar campos obrigatórios
            errors = []
            for field in fields:
                if field['required'] and field['field_type'] != 'file':
                    value = form_data.get(field['name'])
                    if not value or (isinstance(value, str) and not value.strip()):
                        errors.append(f"• {field['label']} é obrigatório")
            
            if errors:
                st.error("Por favor, preencha todos os campos obrigatórios:\n" + "\n".join(errors))
                return
            
            # Validar email
            if 'email' in form_data:
                email = form_data['email']
                if '@' not in email or '.' not in email:
                    st.error("Por favor, insira um e-mail válido")
                    return
            
            # Processar envio
            with st.spinner("Processando seu formulário..."):
                try:
                    # Salvar arquivos
                    file_paths = []
                    if uploaded_files:
                        # Salvar resposta primeiro para obter ID
                        response_id = save_response(form_data, [])
                        
                        for uploaded_file in uploaded_files:
                            valid, error_msg = validate_file(uploaded_file)
                            if not valid:
                                st.warning(f"Arquivo '{uploaded_file.name}' ignorado: {error_msg}")
                                continue
                            
                            filepath = save_uploaded_file(uploaded_file, response_id)
                            file_paths.append(filepath)
                        
                        # Atualizar com caminhos dos arquivos
                        conn = sqlite3.connect(DB_PATH)
                        c = conn.cursor()
                        c.execute("UPDATE responses SET files=? WHERE id=?",
                                (json.dumps(file_paths), response_id))
                        conn.commit()
                        conn.close()
                    else:
                        response_id = save_response(form_data, [])
                    
                    # Enviar email
                    email_body = format_email_body(form_data, fields)
                    send_email_with_retry(
                        "Nova resposta - Ribeiro Forms",
                        email_body,
                        file_paths
                    )
                    
                    st.success("✅ Formulário enviado com sucesso!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Erro ao processar formulário: {str(e)}")

# ============================================================================
# FUNÇÕES DE INTERFACE - PAINEL ADMIN
# ============================================================================

def check_admin_password(password: str) -> bool:
    """Verifica senha do admin"""
    stored_hash = get_config('admin_password')
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    return stored_hash == input_hash

def admin_login():
    """Tela de login do admin"""
    st.title("🔐 Acesso Administrativo")
    
    with st.form("login_form"):
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            if check_admin_password(password):
                st.session_state['admin_logged_in'] = True
                st.rerun()
            else:
                st.error("Senha incorreta")

def admin_panel():
    """Painel administrativo"""
    st.title("⚙️ Painel Administrativo")
    
    # Botão de logout
    if st.button("🚪 Sair do Painel Admin"):
        st.session_state['admin_logged_in'] = False
        st.rerun()
    
    st.markdown("---")
    
    # Abas
    tab1, tab2, tab3 = st.tabs(["📝 Configurações", "🎯 Campos", "📊 Respostas"])
    
    with tab1:
        admin_config_tab()
    
    with tab2:
        admin_fields_tab()
    
    with tab3:
        admin_responses_tab()

def admin_config_tab():
    """Aba de configurações"""
    st.subheader("Configurações Gerais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("Título do Formulário", 
                              value=get_config('title') or 'Ribeiro Forms')
        if st.button("Salvar Título"):
            set_config('title', title)
            st.success("Título atualizado!")
    
    with col2:
        description = st.text_area("Descrição", 
                                   value=get_config('description') or '',
                                   height=100)
        if st.button("Salvar Descrição"):
            set_config('description', description)
            st.success("Descrição atualizada!")
    
    st.markdown("---")
    st.subheader("Logo/Banner")
    
    uploaded_logo = st.file_uploader("Upload de Logo (PNG ou JPG)", 
                                     type=['png', 'jpg', 'jpeg'])
    if uploaded_logo:
        logo_path = os.path.join(LOGO_DIR, f"logo.{uploaded_logo.name.split('.')[-1]}")
        with open(logo_path, 'wb') as f:
            f.write(uploaded_logo.getbuffer())
        set_config('logo_path', logo_path)
        st.success("Logo atualizado!")
        st.image(logo_path, width=300)
    
    current_logo = get_config('logo_path')
    if current_logo and os.path.exists(current_logo):
        st.image(current_logo, caption="Logo atual", width=300)
        if st.button("Remover Logo"):
            os.remove(current_logo)
            set_config('logo_path', '')
            st.success("Logo removido!")
            st.rerun()
    
    st.markdown("---")
    st.subheader("Alterar Senha Admin")
    
    with st.form("change_password"):
        new_password = st.text_input("Nova Senha", type="password")
        confirm_password = st.text_input("Confirmar Senha", type="password")
        
        if st.form_submit_button("Alterar Senha"):
            if new_password == confirm_password and new_password:
                hashed = hashlib.sha256(new_password.encode()).hexdigest()
                set_config('admin_password', hashed)
                st.success("Senha alterada com sucesso!")
            else:
                st.error("As senhas não coincidem ou estão vazias")

def admin_fields_tab():
    """Aba de gerenciamento de campos"""
    st.subheader("Gerenciar Campos")
    
    # Adicionar novo campo
    with st.expander("➕ Adicionar Novo Campo"):
        with st.form("add_field"):
            col1, col2 = st.columns(2)
            
            with col1:
                field_name = st.text_input("Nome do Campo (identificador)")
                field_label = st.text_input("Rótulo (exibido no formulário)")
                field_type = st.selectbox("Tipo", 
                    ['text', 'textarea', 'number', 'email', 'phone', 'date', 
                     'select', 'multiselect', 'checkbox'])
            
            with col2:
                required = st.checkbox("Campo Obrigatório")
                
                options_str = ""
                if field_type in ['select', 'multiselect']:
                    options_str = st.text_area("Opções (uma por linha)")
            
            if st.form_submit_button("Adicionar Campo"):
                if field_name and field_label:
                    options = [opt.strip() for opt in options_str.split('\n') if opt.strip()] if options_str else None
                    add_field(field_name, field_label, field_type, required, options)
                    st.success(f"Campo '{field_label}' adicionado!")
                    st.rerun()
                else:
                    st.error("Nome e rótulo são obrigatórios")
    
    st.markdown("---")
    
    # Lista de campos
    fields = get_fields()
    st.subheader(f"Campos Cadastrados ({len(fields)})")
    
    for i, field in enumerate(fields):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([0.5, 2, 1.5, 1, 1])
            
            with col1:
                st.write(f"**{i+1}**")
            
            with col2:
                st.write(f"**{field['label']}**")
            
            with col3:
                st.write(f"Tipo: {field['field_type']}")
            
            with col4:
                if field['required']:
                    st.write("🔴 Obrigatório")
            
            with col5:
                if not field['is_default'] or field['name'] not in ['nome', 'email', 'termos']:
                    if st.button("🗑️", key=f"del_{field['id']}"):
                        delete_field(field['id'])
                        st.success("Campo removido!")
                        st.rerun()
            
            st.markdown("---")

def admin_responses_tab():
    """Aba de respostas"""
    st.subheader("Respostas Recebidas")
    
    responses = get_responses()
    
    if not responses:
        st.info("Nenhuma resposta recebida ainda")
        return
    
    st.write(f"**Total de respostas:** {len(responses)}")
    
    # Exportar CSV
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Baixar CSV"):
            csv_data = export_responses_csv(responses)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"respostas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📧 Enviar CSV por Email"):
            try:
                csv_data = export_responses_csv(responses)
                filename = f"respostas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                filepath = os.path.join(UPLOAD_DIR, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(csv_data)
                
                send_email_with_retry(
                    "Exportação de Respostas - Ribeiro Forms",
                    f"<p>Segue anexo o arquivo CSV com as respostas recebidas.</p><p>Total: {len(responses)} respostas</p>",
                    [filepath]
                )
                
                os.remove(filepath)
                st.success("CSV enviado por email!")
            except Exception as e:
                st.error(f"Erro ao enviar email: {str(e)}")
    
    st.markdown("---")
    
    # Listar respostas
    for response in responses:
        with st.expander(f"Resposta #{response['id']} - {response['created_at']}"):
            data = response['data']
            
            for key, value in data.items():
                st.write(f"**{key.title()}:** {value}")
            
            if response['files']:
                st.write("**Arquivos:**")
                for file in response['files']:
                    st.write(f"- {os.path.basename(file)}")

def export_responses_csv(responses: List[Dict]) -> str:
    """Exporta respostas para CSV"""
    output = io.StringIO()
    
    if not responses:
        return ""
    
    # Cabeçalhos
    all_keys = set()
    for resp in responses:
        all_keys.update(resp['data'].keys())
    
    headers = ['ID', 'Data/Hora'] + sorted(list(all_keys)) + ['Arquivos']
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for resp in responses:
        row = [resp['id'], resp['created_at']]
        for key in sorted(list(all_keys)):
            row.append(resp['data'].get(key, ''))
        
        # Adicionar nomes dos arquivos
        files_str = ', '.join([os.path.basename(f) for f in resp['files']]) if resp['files'] else ''
        row.append(files_str)
        
        writer.writerow(row)
    
    return output.getvalue()

# ============================================================================
# APLICAÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da aplicação"""
    
    # Configuração da página
    st.set_page_config(
        page_title="Ribeiro Forms",
        page_icon="📝",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Inicializar banco de dados
    init_db()
    
    # Inicializar session state
    if 'admin_logged_in' not in st.session_state:
        st.session_state['admin_logged_in'] = False
    if 'show_admin_login' not in st.session_state:
        st.session_state['show_admin_login'] = False
    
    # CSS customizado
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            font-weight: 600;
        }
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 8px;
        }
        div[data-testid="stForm"] {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }
        .footer {
            position: fixed;
            bottom: 10px;
            right: 10px;
            z-index: 999;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Botão flutuante para acesso admin
    if not st.session_state['admin_logged_in'] and not st.session_state['show_admin_login']:
        st.markdown("""
            <div class="footer">
                <style>
                .admin-btn {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 24px;
                    border-radius: 50px;
                    border: none;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 14px;
                    transition: all 0.3s;
                }
                .admin-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                }
                </style>
            </div>
        """, unsafe_allow_html=True)
        
        # Usar sidebar para botão admin
        with st.sidebar:
            st.markdown("### 🔐 Acesso Restrito")
            if st.button("🔑 Painel Admin", use_container_width=True):
                st.session_state['show_admin_login'] = True
                st.rerun()
    
    # Lógica de exibição
    if st.session_state['show_admin_login'] and not st.session_state['admin_logged_in']:
        admin_login()
        
        # Botão para voltar ao formulário
        if st.button("← Voltar ao Formulário"):
            st.session_state['show_admin_login'] = False
            st.rerun()
    
    elif st.session_state['admin_logged_in']:
        admin_panel()
    
    else:
        render_form()
        
        # Rodapé
        st.markdown(
            "<div style='text-align: center; color: #7f8c8d; padding: 1rem;'>"
            "<strong>Por Ary Ribeiro</strong> "
            "<a href='mailto:aryribeiro@gmail.com' style='color: #667eea; text-decoration: none;'>aryribeiro@gmail.com</a> | "
            "Desenvolvido em Python e Streamlit"
            "</div>",
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()

st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        color: #333333;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    /* Esconde completamente todos os elementos da barra padrão do Streamlit */
    header {display: none !important;}
    footer {display: none !important;}
    #MainMenu {display: none !important;}
    /* Remove qualquer espaço em branco adicional */
    div[data-testid="stAppViewBlockContainer"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    /* Remove quaisquer margens extras */
    .element-container {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)