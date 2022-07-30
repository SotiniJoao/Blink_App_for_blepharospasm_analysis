import datetime
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import PIL
import cv2
from MódulosBlefaro1 import Detector
import tempfile
import datetime
from test_credenciais import *
import gspread
import secrets
from streamlit.legacy_caching import caching
from streamlit.scriptrunner import RerunException
import seaborn as sns
import re

st.set_page_config(page_title='Blink App', layout="centered", page_icon=":eye:")
with open('app_styles.css') as f:
    st.markdown(f"""<style>{f.read()}</style>""", unsafe_allow_html=True)

credenciais = {
  "type": st.secrets.sheets_api_credencials.type,
  "project_id": st.secrets.sheets_api_credencials.project_id,
  "private_key_id": st.secrets.sheets_api_credencials.private_key_id,
  "private_key": st.secrets.sheets_api_credencials.private_key,
  "client_email": st.secrets.sheets_api_credencials.client_email,
  "client_id": st.secrets.sheets_api_credencials.client_id,
  "auth_uri": st.secrets.sheets_api_credencials.auth_uri,
  "token_uri": st.secrets.sheets_api_credencials.token_uri,
  "auth_provider_x509_cert_url": st.secrets.sheets_api_credencials.auth_provider_x509_cert_url,
  "client_x509_cert_url": st.secrets.sheets_api_credencials.client_x509_cert_url
}


@st.cache(allow_output_mutation=True, max_entries=5)
def open_main_sheets():
    sa = gspread.service_account_from_dict(credenciais)
    sh = sa.open('Pessoas_App')
    db = sh.worksheet('Cadastro')
    db = pd.DataFrame(db.get_all_records())
    return db, sh

class DBConnect:
    def __init__(self, sh):
        self.sh = sh
    def hash_sh_reference(sh_ref):
        sh = sh_ref.sh
        return sh

@st.cache(allow_output_mutation=True, max_entries=5, hash_func={DBConnect:hash_sh_reference})
def open_personal_db(sh, ids):
    personal_db_raw = open_credencials(sh, ids)
    personal_db = pd.DataFrame(personal_db_raw.get_all_records())
    return personal_db, personal_db_raw


def register(p_db, values):
    insert_values(p_db, values)
    caching.clear_cache()
    st.experimental_rerun()
    succs = st.success('Dados Registrados!')


# def state_freeze(name, password):
#     st.session_state.name = name
#     st.session_state.password = password


def quit(x):
    st.session_state.check = x
    st.session_state.name = ""
    st.session_state.password = ""
    st.session_state.nome = ""


def iniciar(x):
    st.session_state.run = x


def stop():
    st.session_state.run = 0


if 'check' not in st.session_state:
    st.session_state.check = 0
if 'nome' not in st.session_state:
    st.session_state.nome = ''
if 'run' not in st.session_state:
    st.session_state.run = 0
if 'p_db' not in st.session_state:
    st.session_state.p_db = 0

imagem = Image.open("Unifesp_simples_policromia_RGB.png")
imagem = imagem.resize((960, 250))
db, sh = open_main_sheets()

menu = ["Home", "Analysis", "Register"]
c = st.sidebar.selectbox("Menu", menu)
if c == "Home":
    st.image(imagem, use_column_width=True)
    st.write("## Welcome to Blink App")
    with st.container():
        with st.expander('History'):
            st.write(
                'It is challenging to assess hemifacial spasm patients as they exhibit high-frequency and heterogeneous anomalous eyelid movements. '
                "To assess treatment response, João Luiz Sotini da Silva, a student of Biomedical Engineering, guided by Dr. Regina Célia Coelho, developed this app to facilitate and monitor patient's analysis.")
        with st.expander('Purpose'):
            st.write(
                'The app comes with the intention of reducing the effort to diagnose the disease at an early stage, so that treatment can be done as quickly as possible. To this end, the app is made available '
                'for both computers and mobile devices, in order to reach as many patients of the disease as possible.')
        with st.expander('How it works'):
            st.write(
                'To use the app, first make your registration in the "Create Registration" tab. Then just login with your username and password, and you will be redirected to a page containing a bar with 3 '
                ' options: Pre Treatment, Post Treatment and Real Time Video. Choose one of the three options (for the first two, you need to download a video file) to start performing the analysis.'
                 ' For best results, record the video in a comfortable, light position and try not to move too much so that the recognition algorithm can best capture the image.'
                    'Enjoy!')

elif c == "Analysis":
    db, sh = open_main_sheets()
    with st.sidebar.form("form", clear_on_submit=True):
        name = st.text_input("Login", "", key='name')
        password = st.text_input("Password", "", type='password', key='password')
        for index, n in enumerate(zip(db['Login'].values, db['Senha'].values)):
            if n[0] == name and str(n[1]) == password:
                st.session_state.p_db, p_dbr = open_personal_db(sh, str(db['ID'][index]))
                st.session_state.check = 1
                st.session_state.nome = db['Nome'][index]
        submit_button = st.form_submit_button("Login")
    if st.session_state.check == 0:
        st.image(imagem, use_column_width=True)
        st.write('## Blefaro App')
        st.image(Image.open("istockphoto-485347378-170667a.jpg"),use_column_width=True)
        st.subheader('Log-in to begin the analysis!')
        name = ""
        password = ""
    elif st.session_state.check == 1:
        st.image(imagem, use_column_width=True)
        st.success(f"Welcome {st.session_state.nome}")
        st.title("Analysis")
        st.markdown(
            "**Upload** the video clicking the box **_'Browse Files'_**. You may choose the treatment phase between **'pre-treatment'** and **'post-treament'**. The video will be cut to **1 minute long**! "
            "To access previous results, select the **History** and to see the historical results in a chart access the **Charts** section!")
        choice = ['Pre-treatment', 'Post-treatment', 'History', 'Charts']
        select = st.selectbox("Selecione o estágio:", choice)
        if select == 'Pre-treatment':
            st.write("### Upload the video below:")
            video_file = st.file_uploader('Pre-treatment diagnosis video', type=['MOV', 'MP4'])
            msg = st.empty()
            msg.write("### Click start to initiate the 1 minute video:")
            video = tempfile.NamedTemporaryFile(delete=False)
            botao = st.empty()
            botao.button("Start", on_click=iniciar, args=[1], key='iniciar')
            while st.session_state.run == 1:
                msg.empty()
                try:
                    video.write(video_file.read())
                except AttributeError:
                    msg.write("### Insira um arquivo antes de começar!")
                    st.error("Unable to identify the video")
                    st.session_state.run = 0
                    botao.button("Start", on_click=iniciar, args=[1], key='iniciar_after')
                    break
                if video_file is not None:
                    botao.button('Stop', on_click=stop, key=secrets.token_hex(20))
                    stframe = st.empty()
                    captura = cv2.VideoCapture(video.name)
                    t = Detector.calibragem(captura)
                    olhoe, olhod, total, txdeframes, thresh, st.session_state.run = Detector.Captura(captura, t)
                    pre = {'Data': datetime.datetime.today().strftime("%d/%m/%Y"), 'EAR1': str(olhoe),
                           'EAR2': str(olhod), 'Piscadas': [total], 'Estágio': 'pre', 'Taxa de Frames': str(txdeframes),
                           'Limiar': str([thresh])}
                    st.button('Register Data', on_click=register, args=[p_dbr, pre])
            st.button("Quit", on_click=quit, args=[0])
        elif select == 'Post-treatment':
            st.write("### Upload the video below:")
            video_file = st.file_uploader('Post-treatment diagnosis video', type=['MOV', 'MP4'])
            msg = st.empty()
            msg.write("### Click start to initiate the 1 minute video:")
            video = tempfile.NamedTemporaryFile(delete=False)
            botao = st.empty()
            botao.button("Start", on_click=iniciar, args=[1])
            while st.session_state.run == 1:
                botao.button('Stop', on_click=stop, key=secrets.token_hex(15))
                msg.empty()
                try:
                    video.write(video_file.read())
                except AttributeError:
                    st.error("Unable to identify the video")
                    st.session_state.run = 0
                    break
                if video_file is not None:
                    stframe = st.empty()
                    captura1 = cv2.VideoCapture(video.name)
                    captura2 = cv2.VideoCapture(video.name)
                    t = Detector.calibragem(captura1)
                    olhoe, olhod, total, txdeframes, thresh, st.session_state.run = Detector.Captura(captura2, t)
                    pos = {'Data': datetime.datetime.today().strftime("%d/%m/%Y"), 'EAR1': str(olhoe),
                           'EAR2': str(olhod), 'Piscadas': [total], 'Estágio': 'post', 'Taxa de Frames': str(txdeframes),
                           'Limiar': str([thresh])}

                    st.button('Register Data', on_click=register, args=[p_dbr, pos])
            st.button("Quit", on_click=quit, args=[0])
        elif select == 'History':
            st.write('## History')
            st.dataframe(st.session_state.p_db[['Data', 'Piscadas', 'Estágio', 'EAR1', 'EAR2']].style.set_properties(
                **{'background-color': 'white',
                   'color': 'green'}))
            st.button("Quit", on_click=quit, args=[0])
        elif select == 'Charts':
            st.write('## Charts from History data')
            try:
                data = st.selectbox('Select the date:', np.unique(st.session_state.p_db['Data'].values))
                stage = st.selectbox('Select the phase:', np.unique(st.session_state.p_db['Estágio'].values))
            except ValueError:
                st.write('## No records found!')
            try:
                earesq, eardir, piscadas, txdeframes, limiar = read_values_from_date(st.session_state.p_db, data, stage)
                sns.set(style="whitegrid")
                fig1, ax1 = plt.subplots(figsize=(30, 10))
                sns.lineplot(x=txdeframes, y=earesq, ax=ax1, color='blue', label='EAR olho dir').axhline(limiar,
                                                                                                         c='darkblue',
                                                                                                         label='Limiar',
                                                                                                         ls=':')
                ax1.set_title('Eye Aspect Ratio per Time', fontsize=25)
                ax1.set_xlabel('Time (s)', fontsize=20)
                ax1.set_ylabel('EAR', fontsize=20)
                plt.legend()
                fig2, ax2 = plt.subplots(figsize=(30, 10))
                sns.lineplot(x=txdeframes, y=eardir, ax=ax2, color='red', label='EAR olho esq').axhline(limiar,
                                                                                                        c='darkblue',
                                                                                                        label='Limiar',
                                                                                                        ls=':')
                ax2.set_title('Eye Aspect Ratio per Time',fontsize=25)
                ax2.set_xlabel('Time (s)',fontsize=20)
                ax2.set_ylabel('EAR', fontsize=20)
                plt.legend()
                st.pyplot(fig1)
                st.pyplot(fig2)
            except ValueError:
                st.write('## No records found!')
            st.button("Quit", on_click=quit, args=[0])

elif c == "Register":
    st.image(imagem, use_column_width=True)
    st.write("""
        ## Register
    """)
    form = st.form("form2", clear_on_submit=True)
    with form:
        logincadastro = st.text_input('Login:')
        nome1 = st.text_input("First name:")
        nome2 = st.text_input("Last name:")
        idade = st.text_input("Age:")
        cidade = st.text_input("City:")
        senha = st.text_input("Password (only 8 numbers or letters):", type='password')
        verificasenha = st.text_input("Repeat password:", type='password')
        if logincadastro not in db['Nome'].values and logincadastro is not '':
            if senha == verificasenha:
                dados = {'Login': logincadastro, 'Nome': nome1, 'Sobrenome': nome2, 'Idade': [idade], 'Cidade': cidade,
                         'Senha': [senha], 'ID': secrets.token_hex(10)}
            else:
                st.error("The passwords don't match.")
        else:
            if logincadastro == '':
                pass
            else:
                st.error("Login name already taken.")
        submit = st.form_submit_button("Enviar")
        regex = re.compile('[@!#$%^&*()<>?/|}{~:âãíáàç,]')
        if submit:
            if logincadastro == '' or regex.search(logincadastro) is not None:
                st.error('Insert a valid login name')
            elif nome1 == '':
                st.error('Insert your name')
            elif nome2 == '':
                st.error('Insert your last name')
            elif idade == '':
                st.error('Insert your age')
            elif cidade == '':
                st.error('Insert your city')
            elif senha == '':
                st.error('Insert password')
            else:
                create_credencials(sh, dados)
                caching.clear_cache()
                st.experimental_rerun()
