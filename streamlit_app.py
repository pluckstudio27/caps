import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Date, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from fpdf import FPDF
import io

# Configuração da Página
st.set_page_config(page_title="CAPS Infantil - Sistema Completo", layout="wide")

# Configuração do Banco de Dados
Base = declarative_base()
engine = create_engine('sqlite:///caps_data.db')
Session = sessionmaker(bind=engine)

# --- MODELOS DO BANCO DE DADOS ---

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user") # user, admin

class Avaliacao(Base):
    __tablename__ = 'avaliacoes'
    id = Column(Integer, primary_key=True)
    data_criacao = Column(Date, default=datetime.today)
    
    # Cabeçalho
    cidade = Column(String, default="Angicos")
    estado = Column(String, default="RN")
    profissional_responsavel = Column(String)
    
    # Acolhimento Inicial
    paciente_nome = Column(String)
    crianca_identificada = Column(Boolean)
    responsavel_presente = Column(Boolean)
    responsavel_nome = Column(String)
    motivo_atendimento = Column(Text)
    encaminhamento_origem = Column(String)
    observacao_comportamento = Column(Text)
    
    # Caderneta Vacinal
    caderneta_apresentada = Column(Boolean)
    vacinas_conferidas = Column(Boolean)
    esquema_completo = Column(Boolean)
    vacinas_atraso = Column(Boolean)
    orientacao_responsavel_vacina = Column(Boolean)
    encaminhamento_ubs_vacina = Column(Boolean)
    
    # Avaliação Nutricional
    peso = Column(Float)
    altura = Column(Float)
    imc = Column(Float)
    classificacao_nutricional = Column(String)
    queixa_alimentar = Column(String)
    orientacao_nutricional = Column(Boolean)
    encaminhamento_nutricao = Column(Boolean)
    
    # Avaliação Odontológica
    higiene_bucal = Column(Boolean)
    carie_visivel = Column(Boolean)
    dor_relatada = Column(Boolean)
    orientacao_higiene_bucal = Column(Boolean)
    encaminhamento_odontologico = Column(Boolean)
    classificacao_odonto = Column(String)
    
    # Plano Inicial
    inserido_caps = Column(Boolean)
    encaminhamento_ubs_plano = Column(Boolean)
    encaminhamento_nutricao_plano = Column(Boolean)
    encaminhamento_odonto_plano = Column(Boolean)
    encaminhamento_assistencia_social = Column(Boolean)
    proxima_avaliacao = Column(Date)
    registro_prontuario = Column(Boolean)

# Criar tabelas
Base.metadata.create_all(engine)

# --- FUNÇÕES UTILITÁRIAS ---

def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hash_val):
    return make_hash(password) == hash_val

def init_db():
    session = Session()
    # Criar admin padrão se não existir
    admin = session.query(User).filter_by(username='admin').first()
    if not admin:
        admin_user = User(username='admin', password_hash=make_hash('admin'), role='admin')
        session.add(admin_user)
        session.commit()
    session.close()

# Inicializa DB e usuário admin
init_db()

def login_user(username, password):
    session = Session()
    user = session.query(User).filter_by(username=username).first()
    session.close()
    if user and check_hash(password, user.password_hash):
        return user
    return None

def save_avaliacao(data, avaliacao_id=None):
    session = Session()
    try:
        if avaliacao_id:
            # Atualizar existente
            avaliacao = session.query(Avaliacao).filter_by(id=avaliacao_id).first()
            if avaliacao:
                for key, value in data.items():
                    setattr(avaliacao, key, value)
        else:
            # Criar nova
            nova_avaliacao = Avaliacao(**data)
            session.add(nova_avaliacao)
        session.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False
    finally:
        session.close()

def delete_avaliacao(avaliacao_id):
    session = Session()
    try:
        avaliacao = session.query(Avaliacao).filter_by(id=avaliacao_id).first()
        if avaliacao:
            session.delete(avaliacao)
            session.commit()
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return False
    finally:
        session.close()

def delete_user(user_id):
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    finally:
        session.close()

def create_user(username, password, role):
    session = Session()
    try:
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            return False, "Usuário já existe"
        
        new_user = User(username=username, password_hash=make_hash(password), role=role)
        session.add(new_user)
        session.commit()
        return True, "Usuário criado com sucesso"
    except Exception as e:
        return False, str(e)
    finally:
        session.close()

def update_user(user_id, new_password=None, new_role=None, new_username=None):
    session = Session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            if new_username and new_username != user.username:
                existing = session.query(User).filter_by(username=new_username).first()
                if existing:
                    return False, "Nome de usuário já existe"
                user.username = new_username
            if new_password:
                user.password_hash = make_hash(new_password)
            if new_role:
                user.role = new_role
            session.commit()
            return True, "Usuário atualizado com sucesso"
        return False, "Usuário não encontrado"
    except Exception as e:
        return False, str(e)
    finally:
        session.close()

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="CHECKLIST RÁPIDO – AVALIAÇÃO INICIAL", ln=True, align='C')
    pdf.cell(200, 10, txt="CAPS INFANTIL", ln=True, align='C')
    pdf.ln(5)
    
    def checkbox(label, value):
        mark = "X" if value else " "
        pdf.set_font("Arial", size=10)
        pdf.cell(10, 5, txt=f"[{mark}]", ln=0)
        pdf.cell(0, 5, txt=label, ln=1)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="ACOLHIMENTO INICIAL", ln=1, fill=False)
    checkbox(f"Criança/adolescente identificado: {dados.paciente_nome or ''}", dados.crianca_identificada)
    checkbox(f"Responsável legal presente: {dados.responsavel_nome or ''}", dados.responsavel_presente)
    checkbox(f"Motivo do atendimento: {dados.motivo_atendimento or ''}", bool(dados.motivo_atendimento))
    checkbox(f"Encaminhamento de origem: {dados.encaminhamento_origem or ''}", bool(dados.encaminhamento_origem))
    checkbox(f"Observação do comportamento: {dados.observacao_comportamento or ''}", bool(dados.observacao_comportamento))
    checkbox(f"Profissional responsável: {dados.profissional_responsavel or ''}", bool(dados.profissional_responsavel))
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="CADERNETA VACINAL", ln=1)
    checkbox("Caderneta apresentada", dados.caderneta_apresentada)
    checkbox("Vacinas conferidas conforme idade", dados.vacinas_conferidas)
    checkbox("Esquema vacinal completo", dados.esquema_completo)
    checkbox("Vacinas em atraso", dados.vacinas_atraso)
    checkbox("Orientação ao responsável realizada", dados.orientacao_responsavel_vacina)
    checkbox("Encaminhamento à UBS (se necessário)", dados.encaminhamento_ubs_vacina)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="AVALIAÇÃO NUTRICIONAL", ln=1)
    checkbox(f"Peso aferido: {dados.peso} kg", True)
    checkbox(f"Altura aferida: {dados.altura} m", True)
    checkbox(f"IMC calculado: {dados.imc:.2f}", True)
    checkbox(f"Classificação nutricional: {dados.classificacao_nutricional}", True)
    checkbox(f"Queixa alimentar: {dados.queixa_alimentar or 'Nenhuma'}", bool(dados.queixa_alimentar))
    checkbox("Orientação nutricional realizada", dados.orientacao_nutricional)
    checkbox("Encaminhamento realizado (se necessário)", dados.encaminhamento_nutricao)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="AVALIAÇÃO ODONTOLÓGICA", ln=1)
    checkbox("Higiene bucal adequada", dados.higiene_bucal)
    checkbox("Presença de cárie visível", dados.carie_visivel)
    checkbox("Dor ou desconforto relatado", dados.dor_relatada)
    checkbox("Orientação de higiene bucal realizada", dados.orientacao_higiene_bucal)
    checkbox("Encaminhamento odontológico", dados.encaminhamento_odontologico)
    checkbox(f"Classificação: {dados.classificacao_odonto}", True)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="PLANO INICIAL DE CUIDADO", ln=1)
    checkbox("Inserido no acompanhamento CAPS", dados.inserido_caps)
    checkbox("Encaminhamento para UBS", dados.encaminhamento_ubs_plano)
    checkbox("Encaminhamento para Nutrição", dados.encaminhamento_nutricao_plano)
    checkbox("Encaminhamento para Odontologia", dados.encaminhamento_odonto_plano)
    checkbox("Encaminhamento para Assistência Social", dados.encaminhamento_assistencia_social)
    prox_data = dados.proxima_avaliacao.strftime('%d/%m/%Y') if dados.proxima_avaliacao else "Não agendada"
    checkbox(f"Próxima avaliação agendada: {prox_data}", bool(dados.proxima_avaliacao))
    checkbox("Registro em prontuário realizado", dados.registro_prontuario)
    pdf.ln(10)

    data_formatada = dados.data_criacao.strftime('%d de %B de %Y')
    pdf.cell(0, 10, txt=f"Angicos/RN, {data_formatada}.", ln=1, align='R')
    pdf.ln(15)
    pdf.cell(0, 10, txt="__________________________________________", ln=1, align='C')
    pdf.cell(0, 5, txt=f"{dados.profissional_responsavel or 'Profissional Responsável'}", ln=1, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACE GRÁFICA ---

def login_page():
    st.title("CAPS Infantil - Login")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            user = login_user(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user.username
                st.session_state['role'] = user.role
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")

def main_app():
    st.sidebar.title(f"Bem-vindo, {st.session_state['username']}")
    if st.sidebar.button("Sair"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.title("CAPS INFANTIL - AVALIAÇÃO INICIAL")
    
    tabs = ["Avaliação", "Histórico / Gerenciar"]
    if st.session_state['role'] == 'admin':
        tabs.append("Usuários")
        
    current_tab = st.tabs(tabs)
    
    # --- ABA AVALIAÇÃO ---
    with current_tab[0]:
        st.subheader("Ficha de Avaliação")
        
        # Recuperar dados se estiver editando
        edit_data = st.session_state.get('edit_data', None)
        edit_id = st.session_state.get('edit_id', None)
        
        if edit_data:
            st.info(f"Editando avaliação de: {edit_data.get('paciente_nome', '')} (ID: {edit_id})")
            if st.button("Cancelar Edição"):
                st.session_state['edit_data'] = None
                st.session_state['edit_id'] = None
                st.rerun()
        
        with st.form("checklist_form"):
            col_data, col_prof = st.columns(2)
            default_date = edit_data['data_criacao'] if edit_data else datetime.today()
            data_atual = col_data.date_input("Data", default_date)
            profissional = col_prof.text_input("Profissional Responsável", value=edit_data.get('profissional_responsavel', '') if edit_data else '')
            
            st.markdown("---")
            st.header("ACOLHIMENTO INICIAL")
            col1, col2 = st.columns(2)
            paciente_nome = col1.text_input("Nome da Criança/Adolescente", value=edit_data.get('paciente_nome', '') if edit_data else '')
            
            # Checkboxes defaults
            def get_val(key):
                return bool(edit_data.get(key)) if edit_data else False
            
            crianca_identificada = col2.checkbox("Criança/adolescente identificado", value=get_val('crianca_identificada'))
            
            col3, col4 = st.columns(2)
            responsavel_nome = col3.text_input("Nome do Responsável Legal", value=edit_data.get('responsavel_nome', '') if edit_data else '')
            responsavel_presente = col4.checkbox("Responsável legal presente", value=get_val('responsavel_presente'))
            
            motivo_atendimento = st.text_area("Motivo do atendimento registrado", value=edit_data.get('motivo_atendimento', '') if edit_data else '')
            encaminhamento_origem = st.text_input("Encaminhamento de origem identificado", value=edit_data.get('encaminhamento_origem', '') if edit_data else '')
            observacao_comportamento = st.text_area("Observação inicial do comportamento", value=edit_data.get('observacao_comportamento', '') if edit_data else '')
            
            st.markdown("---")
            st.header("CADERNETA VACINAL")
            c1, c2, c3 = st.columns(3)
            caderneta_apresentada = c1.checkbox("Caderneta apresentada", value=get_val('caderneta_apresentada'))
            vacinas_conferidas = c2.checkbox("Vacinas conferidas conforme idade", value=get_val('vacinas_conferidas'))
            esquema_completo = c3.checkbox("Esquema vacinal completo", value=get_val('esquema_completo'))
            
            c4, c5, c6 = st.columns(3)
            vacinas_atraso = c4.checkbox("Vacinas em atraso", value=get_val('vacinas_atraso'))
            orientacao_responsavel_vacina = c5.checkbox("Orientação ao responsável realizada", value=get_val('orientacao_responsavel_vacina'))
            encaminhamento_ubs_vacina = c6.checkbox("Encaminhamento à UBS (se necessário)", value=get_val('encaminhamento_ubs_vacina'))

            st.markdown("---")
            st.header("AVALIAÇÃO NUTRICIONAL")
            nc1, nc2, nc3 = st.columns(3)
            peso = nc1.number_input("Peso (kg)", min_value=0.0, format="%.2f", value=edit_data.get('peso', 0.0) if edit_data else 0.0)
            altura = nc2.number_input("Altura (m)", min_value=0.0, format="%.2f", value=edit_data.get('altura', 0.0) if edit_data else 0.0)
            
            imc = 0.0
            if altura > 0:
                imc = peso / (altura * altura)
            nc3.metric("IMC Calculado", f"{imc:.2f}")
            
            class_options = ["Não avaliado", "Baixo peso", "Eutrofia (Peso adequado)", "Sobrepeso", "Obesidade"]
            default_class_idx = 0
            if edit_data and edit_data.get('classificacao_nutricional') in class_options:
                default_class_idx = class_options.index(edit_data.get('classificacao_nutricional'))
            
            classificacao_nutricional = st.selectbox("Classificação nutricional definida", class_options, index=default_class_idx)
            queixa_alimentar = st.text_input("Queixa alimentar identificada", value=edit_data.get('queixa_alimentar', '') if edit_data else '')
            
            nc4, nc5 = st.columns(2)
            orientacao_nutricional = nc4.checkbox("Orientação nutricional realizada", value=get_val('orientacao_nutricional'))
            encaminhamento_nutricao = nc5.checkbox("Encaminhamento realizado (Nutrição)", value=get_val('encaminhamento_nutricao'))

            st.markdown("---")
            st.header("AVALIAÇÃO ODONTOLÓGICA")
            oc1, oc2, oc3 = st.columns(3)
            higiene_bucal = oc1.checkbox("Higiene bucal adequada", value=get_val('higiene_bucal'))
            carie_visivel = oc2.checkbox("Presença de cárie visível", value=get_val('carie_visivel'))
            dor_relatada = oc3.checkbox("Dor ou desconforto relatado", value=get_val('dor_relatada'))
            
            oc4, oc5 = st.columns(2)
            orientacao_higiene_bucal = oc4.checkbox("Orientação de higiene bucal realizada", value=get_val('orientacao_higiene_bucal'))
            encaminhamento_odontologico = oc5.checkbox("Encaminhamento odontológico", value=get_val('encaminhamento_odontologico'))
            
            odonto_options = ["Rotina", "Urgência"]
            default_odonto_idx = 0
            if edit_data and edit_data.get('classificacao_odonto') in odonto_options:
                default_odonto_idx = odonto_options.index(edit_data.get('classificacao_odonto'))
            
            classificacao_odonto = st.radio("Classificação Odontológica", odonto_options, index=default_odonto_idx, horizontal=True)

            st.markdown("---")
            st.header("PLANO INICIAL DE CUIDADO")
            pc1, pc2, pc3 = st.columns(3)
            inserido_caps = pc1.checkbox("Inserido no acompanhamento CAPS", value=get_val('inserido_caps'))
            encaminhamento_ubs_plano = pc2.checkbox("Encaminhamento para UBS", value=get_val('encaminhamento_ubs_plano'))
            encaminhamento_nutricao_plano = pc3.checkbox("Encaminhamento para Nutrição", value=get_val('encaminhamento_nutricao_plano'))
            
            pc4, pc5, pc6 = st.columns(3)
            encaminhamento_odonto_plano = pc4.checkbox("Encaminhamento para Odontologia", value=get_val('encaminhamento_odonto_plano'))
            encaminhamento_assistencia_social = pc5.checkbox("Encaminhamento para Assistência Social", value=get_val('encaminhamento_assistencia_social'))
            registro_prontuario = pc6.checkbox("Registro em prontuário realizado", value=get_val('registro_prontuario'))
            
            prox_val = edit_data['proxima_avaliacao'] if edit_data and edit_data.get('proxima_avaliacao') else None
            proxima_avaliacao = st.date_input("Próxima avaliação agendada", value=prox_val)

            st.markdown("---")
            st.text(f"Angicos/RN, {data_atual.strftime('%d de %B de %Y')}")
            
            btn_label = "Atualizar Avaliação" if edit_id else "Salvar Avaliação"
            submitted = st.form_submit_button(btn_label)
            
            if submitted:
                if not paciente_nome:
                    st.error("Por favor, informe o nome do paciente.")
                else:
                    dados = {
                        "data_criacao": data_atual,
                        "profissional_responsavel": profissional,
                        "paciente_nome": paciente_nome,
                        "crianca_identificada": crianca_identificada,
                        "responsavel_presente": responsavel_presente,
                        "responsavel_nome": responsavel_nome,
                        "motivo_atendimento": motivo_atendimento,
                        "encaminhamento_origem": encaminhamento_origem,
                        "observacao_comportamento": observacao_comportamento,
                        "caderneta_apresentada": caderneta_apresentada,
                        "vacinas_conferidas": vacinas_conferidas,
                        "esquema_completo": esquema_completo,
                        "vacinas_atraso": vacinas_atraso,
                        "orientacao_responsavel_vacina": orientacao_responsavel_vacina,
                        "encaminhamento_ubs_vacina": encaminhamento_ubs_vacina,
                        "peso": peso,
                        "altura": altura,
                        "imc": imc,
                        "classificacao_nutricional": classificacao_nutricional,
                        "queixa_alimentar": queixa_alimentar,
                        "orientacao_nutricional": orientacao_nutricional,
                        "encaminhamento_nutricao": encaminhamento_nutricao,
                        "higiene_bucal": higiene_bucal,
                        "carie_visivel": carie_visivel,
                        "dor_relatada": dor_relatada,
                        "orientacao_higiene_bucal": orientacao_higiene_bucal,
                        "encaminhamento_odontologico": encaminhamento_odontologico,
                        "classificacao_odonto": classificacao_odonto,
                        "inserido_caps": inserido_caps,
                        "encaminhamento_ubs_plano": encaminhamento_ubs_plano,
                        "encaminhamento_nutricao_plano": encaminhamento_nutricao_plano,
                        "encaminhamento_odonto_plano": encaminhamento_odonto_plano,
                        "encaminhamento_assistencia_social": encaminhamento_assistencia_social,
                        "proxima_avaliacao": proxima_avaliacao,
                        "registro_prontuario": registro_prontuario,
                        "cidade": "Angicos",
                        "estado": "RN"
                    }
                    if save_avaliacao(dados, avaliacao_id=edit_id):
                        st.success("Avaliação salva com sucesso!")
                        if edit_id:
                            st.session_state['edit_data'] = None
                            st.session_state['edit_id'] = None
                            st.rerun()

    # --- ABA HISTÓRICO / GERENCIAR ---
    with current_tab[1]:
        st.header("Gerenciar Avaliações")
        session = Session()
        try:
            df = pd.read_sql(session.query(Avaliacao).statement, session.bind)
            
            if not df.empty:
                # Filtros
                col_filt, col_export = st.columns([3, 1])
                filtro_nome = col_filt.text_input("Filtrar por nome do paciente")
                if filtro_nome:
                    df = df[df['paciente_nome'].str.contains(filtro_nome, case=False, na=False)]
                
                # Botão CSV
                csv = df.to_csv(index=False).encode('utf-8')
                col_export.download_button("Baixar CSV", csv, "avaliacoes.csv", "text/csv")
                
                st.dataframe(df)
                
                st.markdown("---")
                st.subheader("Ações (Editar / Excluir / PDF)")
                
                # Seletor de Avaliação para Ação
                # Criar lista de strings para seleção amigável
                df['display_name'] = df['id'].astype(str) + " - " + df['paciente_nome'] + " (" + pd.to_datetime(df['data_criacao']).dt.strftime('%d/%m/%Y') + ")"
                
                selected_display = st.selectbox("Selecione uma avaliação para gerenciar:", df['display_name'].tolist())
                
                if selected_display:
                    selected_id = int(selected_display.split(" - ")[0])
                    
                    c_act1, c_act2, c_act3 = st.columns(3)
                    
                    if c_act1.button("✏️ Editar Avaliação"):
                        # Carregar dados para sessão e ir para aba de avaliação
                        avaliacao_obj = session.query(Avaliacao).filter_by(id=selected_id).first()
                        if avaliacao_obj:
                            # Converter objeto SQLAlchemy para dict
                            data_dict = {c.name: getattr(avaliacao_obj, c.name) for c in avaliacao_obj.__table__.columns}
                            st.session_state['edit_data'] = data_dict
                            st.session_state['edit_id'] = selected_id
                            st.rerun()
                            
                    if c_act2.button("🗑️ Excluir Avaliação", type="primary"):
                        if delete_avaliacao(selected_id):
                            st.success("Avaliação excluída!")
                            st.rerun()
                            
                    if c_act3.button("📄 Gerar PDF"):
                        avaliacao_obj = session.query(Avaliacao).filter_by(id=selected_id).first()
                        if avaliacao_obj:
                            pdf_bytes = gerar_pdf(avaliacao_obj)
                            st.download_button(
                                label="⬇️ Baixar PDF",
                                data=pdf_bytes,
                                file_name=f"ficha_{selected_id}.pdf",
                                mime='application/pdf'
                            )
            else:
                st.info("Nenhuma avaliação registrada.")
        except Exception as e:
            st.error(f"Erro: {e}")
        finally:
            session.close()

    # --- ABA USUÁRIOS (ADMIN) ---
    if st.session_state['role'] == 'admin':
        with current_tab[2]:
            st.header("Gerenciar Usuários")
            
            # Criar Novo Usuário
            with st.expander("Cadastrar Novo Usuário"):
                with st.form("new_user"):
                    new_user = st.text_input("Novo Usuário")
                    new_pass = st.text_input("Nova Senha", type="password")
                    new_role = st.selectbox("Função", ["user", "admin"])
                    if st.form_submit_button("Criar"):
                        success, msg = create_user(new_user, new_pass, new_role)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            # Listar Usuários
            st.subheader("Lista de Usuários")
            session = Session()
            users = session.query(User).all()
            session.close()
            
            user_data = [{"ID": u.id, "Usuário": u.username, "Função": u.role} for u in users]
            st.dataframe(pd.DataFrame(user_data))

            # Atualizar Usuário
            st.subheader("Atualizar Usuário")
            user_to_update_name = st.selectbox("Selecione para atualizar:", [u['Usuário'] for u in user_data])
            if user_to_update_name:
                u_to_up = next(u for u in user_data if u['Usuário'] == user_to_update_name)
                with st.form("update_user_form"):
                    st.write(f"Editando: {u_to_up['Usuário']}")
                    new_username_val = st.text_input("Novo Nome de Usuário", value=u_to_up['Usuário'])
                    new_role_val = st.selectbox("Nova Função", ["user", "admin"], index=0 if u_to_up['Função'] == "user" else 1)
                    new_pass_val = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
                    
                    if st.form_submit_button("Atualizar"):
                        # Só passa a senha se não estiver vazia
                        pass_arg = new_pass_val if new_pass_val else None
                        username_arg = new_username_val if new_username_val != u_to_up['Usuário'] else None
                        
                        success, msg = update_user(u_to_up['ID'], new_password=pass_arg, new_role=new_role_val, new_username=username_arg)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            
            # Excluir Usuário
            st.subheader("Excluir Usuário")
            user_to_del = st.selectbox("Selecione para excluir:", [u['Usuário'] for u in user_data if u['Usuário'] != 'admin'])
            if st.button("Excluir Usuário Selecionado"):
                u_id = next(u['ID'] for u in user_data if u['Usuário'] == user_to_del)
                if delete_user(u_id):
                    st.success("Usuário excluído!")
                    st.rerun()

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        
    if not st.session_state['logged_in']:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
