import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Date, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from fpdf import FPDF
import io

# Configuração da Página
st.set_page_config(page_title="CAPS Infantil - Checklist", layout="wide")

# Configuração do Banco de Dados
Base = declarative_base()
engine = create_engine('sqlite:///caps_data.db')
Session = sessionmaker(bind=engine)

class Avaliacao(Base):
    __tablename__ = 'avaliacoes'
    id = Column(Integer, primary_key=True)
    data_criacao = Column(Date, default=datetime.today)
    
    # Cabeçalho
    cidade = Column(String, default="Angicos")
    estado = Column(String, default="RN")
    profissional_responsavel = Column(String)
    
    # Acolhimento Inicial
    paciente_nome = Column(String) # Adicionado para identificação
    crianca_identificada = Column(Boolean)
    responsavel_presente = Column(Boolean)
    responsavel_nome = Column(String) # Adicionado para detalhe
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
    classificacao_odonto = Column(String) # Rotina / Urgência
    
    # Plano Inicial
    inserido_caps = Column(Boolean)
    encaminhamento_ubs_plano = Column(Boolean)
    encaminhamento_nutricao_plano = Column(Boolean)
    encaminhamento_odonto_plano = Column(Boolean)
    encaminhamento_assistencia_social = Column(Boolean)
    proxima_avaliacao = Column(Date)
    registro_prontuario = Column(Boolean)

# Criar tabelas se não existirem
Base.metadata.create_all(engine)

def save_avaliacao(data):
    session = Session()
    nova_avaliacao = Avaliacao(**data)
    session.add(nova_avaliacao)
    session.commit()
    session.close()

def gerar_pdf(dados):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Título
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="CHECKLIST RÁPIDO – AVALIAÇÃO INICIAL", ln=True, align='C')
    pdf.cell(200, 10, txt="CAPS INFANTIL", ln=True, align='C')
    pdf.ln(5)
    
    # Função auxiliar para checkbox
    def checkbox(label, value):
        mark = "X" if value else " "
        pdf.set_font("Arial", size=10)
        pdf.cell(10, 5, txt=f"[{mark}]", ln=0)
        pdf.cell(0, 5, txt=label, ln=1)

    # Acolhimento Inicial
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="ACOLHIMENTO INICIAL", ln=1, fill=False)
    checkbox(f"Criança/adolescente identificado: {dados.paciente_nome or ''}", dados.crianca_identificada)
    checkbox(f"Responsável legal presente: {dados.responsavel_nome or ''}", dados.responsavel_presente)
    checkbox(f"Motivo do atendimento: {dados.motivo_atendimento or ''}", bool(dados.motivo_atendimento))
    checkbox(f"Encaminhamento de origem: {dados.encaminhamento_origem or ''}", bool(dados.encaminhamento_origem))
    checkbox(f"Observação do comportamento: {dados.observacao_comportamento or ''}", bool(dados.observacao_comportamento))
    checkbox(f"Profissional responsável: {dados.profissional_responsavel or ''}", bool(dados.profissional_responsavel))
    pdf.ln(3)

    # Caderneta Vacinal
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="CADERNETA VACINAL", ln=1)
    checkbox("Caderneta apresentada", dados.caderneta_apresentada)
    checkbox("Vacinas conferidas conforme idade", dados.vacinas_conferidas)
    checkbox("Esquema vacinal completo", dados.esquema_completo)
    checkbox("Vacinas em atraso", dados.vacinas_atraso)
    checkbox("Orientação ao responsável realizada", dados.orientacao_responsavel_vacina)
    checkbox("Encaminhamento à UBS (se necessário)", dados.encaminhamento_ubs_vacina)
    pdf.ln(3)

    # Avaliação Nutricional
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

    # Avaliação Odontológica
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, txt="AVALIAÇÃO ODONTOLÓGICA", ln=1)
    checkbox("Higiene bucal adequada", dados.higiene_bucal)
    checkbox("Presença de cárie visível", dados.carie_visivel)
    checkbox("Dor ou desconforto relatado", dados.dor_relatada)
    checkbox("Orientação de higiene bucal realizada", dados.orientacao_higiene_bucal)
    checkbox("Encaminhamento odontológico", dados.encaminhamento_odontologico)
    checkbox(f"Classificação: {dados.classificacao_odonto}", True)
    pdf.ln(3)

    # Plano Inicial
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

    # Assinatura
    data_formatada = dados.data_criacao.strftime('%d de %B de %Y')
    pdf.cell(0, 10, txt=f"Angicos/RN, {data_formatada}.", ln=1, align='R')
    pdf.ln(15)
    pdf.cell(0, 10, txt="__________________________________________", ln=1, align='C')
    pdf.cell(0, 5, txt=f"{dados.profissional_responsavel or 'Profissional Responsável'}", ln=1, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

def main():
    st.title("CAPS INFANTIL - AVALIAÇÃO INICIAL")
    st.subheader("CHECKLIST RÁPIDO")

    tab1, tab2 = st.tabs(["Nova Avaliação", "Histórico de Avaliações"])

    with tab1:
        with st.form("checklist_form"):
            # Identificação Básica (Implicito no cabeçalho/assinatura)
            col_data, col_prof = st.columns(2)
            data_atual = col_data.date_input("Data", datetime.today())
            profissional = col_prof.text_input("Profissional Responsável")
            
            st.markdown("---")
            st.header("ACOLHIMENTO INICIAL")
            col1, col2 = st.columns(2)
            paciente_nome = col1.text_input("Nome da Criança/Adolescente")
            crianca_identificada = col2.checkbox("Criança/adolescente identificado", value=True if paciente_nome else False)
            
            col3, col4 = st.columns(2)
            responsavel_nome = col3.text_input("Nome do Responsável Legal")
            responsavel_presente = col4.checkbox("Responsável legal presente", value=True if responsavel_nome else False)
            
            motivo_atendimento = st.text_area("Motivo do atendimento registrado")
            encaminhamento_origem = st.text_input("Encaminhamento de origem identificado")
            observacao_comportamento = st.text_area("Observação inicial do comportamento")
            
            st.markdown("---")
            st.header("CADERNETA VACINAL")
            c1, c2, c3 = st.columns(3)
            caderneta_apresentada = c1.checkbox("Caderneta apresentada")
            vacinas_conferidas = c2.checkbox("Vacinas conferidas conforme idade")
            esquema_completo = c3.checkbox("Esquema vacinal completo")
            
            c4, c5, c6 = st.columns(3)
            vacinas_atraso = c4.checkbox("Vacinas em atraso")
            orientacao_responsavel_vacina = c5.checkbox("Orientação ao responsável realizada")
            encaminhamento_ubs_vacina = c6.checkbox("Encaminhamento à UBS (se necessário)")

            st.markdown("---")
            st.header("AVALIAÇÃO NUTRICIONAL")
            nc1, nc2, nc3 = st.columns(3)
            peso = nc1.number_input("Peso (kg)", min_value=0.0, format="%.2f")
            altura = nc2.number_input("Altura (m)", min_value=0.0, format="%.2f")
            
            imc = 0.0
            if altura > 0:
                imc = peso / (altura * altura)
            nc3.metric("IMC Calculado", f"{imc:.2f}")
            
            classificacao_nutricional = st.selectbox("Classificação nutricional definida", 
                                                   ["Não avaliado", "Baixo peso", "Eutrofia (Peso adequado)", "Sobrepeso", "Obesidade"])
            queixa_alimentar = st.text_input("Queixa alimentar identificada")
            
            nc4, nc5 = st.columns(2)
            orientacao_nutricional = nc4.checkbox("Orientação nutricional realizada")
            encaminhamento_nutricao = nc5.checkbox("Encaminhamento realizado (Nutrição)")

            st.markdown("---")
            st.header("AVALIAÇÃO ODONTOLÓGICA")
            oc1, oc2, oc3 = st.columns(3)
            higiene_bucal = oc1.checkbox("Higiene bucal adequada")
            carie_visivel = oc2.checkbox("Presença de cárie visível")
            dor_relatada = oc3.checkbox("Dor ou desconforto relatado")
            
            oc4, oc5 = st.columns(2)
            orientacao_higiene_bucal = oc4.checkbox("Orientação de higiene bucal realizada")
            encaminhamento_odontologico = oc5.checkbox("Encaminhamento odontológico")
            
            classificacao_odonto = st.radio("Classificação Odontológica", ["Rotina", "Urgência"], horizontal=True)

            st.markdown("---")
            st.header("PLANO INICIAL DE CUIDADO")
            pc1, pc2, pc3 = st.columns(3)
            inserido_caps = pc1.checkbox("Inserido no acompanhamento CAPS")
            encaminhamento_ubs_plano = pc2.checkbox("Encaminhamento para UBS")
            encaminhamento_nutricao_plano = pc3.checkbox("Encaminhamento para Nutrição")
            
            pc4, pc5, pc6 = st.columns(3)
            encaminhamento_odonto_plano = pc4.checkbox("Encaminhamento para Odontologia")
            encaminhamento_assistencia_social = pc5.checkbox("Encaminhamento para Assistência Social")
            registro_prontuario = pc6.checkbox("Registro em prontuário realizado")
            
            proxima_avaliacao = st.date_input("Próxima avaliação agendada", value=None)

            st.markdown("---")
            st.text(f"Angicos/RN, {data_atual.strftime('%d de %B de %Y')}")
            
            submitted = st.form_submit_button("Salvar Avaliação")
            
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
                    try:
                        save_avaliacao(dados)
                        st.success("Avaliação salva com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    with tab2:
        st.header("Histórico")
        session = Session()
        try:
            # Carregar dados
            df = pd.read_sql(session.query(Avaliacao).statement, session.bind)
            
            if not df.empty:
                # Filtros
                filtro_nome = st.text_input("Filtrar por nome do paciente")
                if filtro_nome:
                    df = df[df['paciente_nome'].str.contains(filtro_nome, case=False, na=False)]
                
                st.dataframe(df)
                
                # Botão para exportar CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Baixar dados em CSV",
                    data=csv,
                    file_name='avaliacoes_caps.csv',
                    mime='text/csv',
                )
                
                st.markdown("---")
                st.subheader("Gerar Ficha Individual (PDF)")
                
                # Seleção para PDF
                nomes_disponiveis = df['paciente_nome'].unique()
                paciente_selecionado = st.selectbox("Selecione o paciente para gerar ficha:", nomes_disponiveis)
                
                if paciente_selecionado:
                    # Pegar a última avaliação desse paciente ou listar datas
                    avaliacoes_paciente = df[df['paciente_nome'] == paciente_selecionado]
                    # Convertendo data para string para exibição
                    avaliacoes_paciente['data_str'] = pd.to_datetime(avaliacoes_paciente['data_criacao']).dt.strftime('%d/%m/%Y')
                    
                    data_selecionada = st.selectbox("Selecione a data da avaliação:", avaliacoes_paciente['data_str'].unique())
                    
                    if st.button("Gerar PDF da Ficha"):
                        # Buscar o objeto completo no banco
                        avaliacao_obj = session.query(Avaliacao).filter(
                            Avaliacao.paciente_nome == paciente_selecionado,
                            Avaliacao.data_criacao == datetime.strptime(data_selecionada, '%d/%m/%Y').date()
                        ).first()
                        
                        if avaliacao_obj:
                            pdf_bytes = gerar_pdf(avaliacao_obj)
                            st.download_button(
                                label="⬇️ Baixar Ficha em PDF",
                                data=pdf_bytes,
                                file_name=f"ficha_{paciente_selecionado}_{data_selecionada.replace('/','-')}.pdf",
                                mime='application/pdf'
                            )
                        else:
                            st.error("Avaliação não encontrada.")
            else:
                st.info("Nenhuma avaliação registrada ainda.")
        except Exception as e:
            st.error(f"Erro ao carregar histórico: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    main()
