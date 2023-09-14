import datetime
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
import PIL
import cv2
from blepharo_detectors import Detector
import tempfile
import datetime
from credentials_utils import *
import gspread
import secrets
import seaborn as sns
import re
import json
import os

st.set_page_config(page_title='Blink App', layout="centered", page_icon=":eye:")
with open('app_styles.css') as f:
    st.markdown(f"""<style>{f.read()}</style>""", unsafe_allow_html=True)

#If using local credentials, uncomment the following lines and line 17
f = open('secrets.json')
credenciais = dict(json.load(f))

# credenciais = st.secrets['gcp_service_account']


@st.cache_resource
def open_main_sheets(_credenciais):
    sa = gspread.service_account_from_dict(_credenciais)
    sh = sa.open('Pessoas_App')
    db = sh.worksheet('Cadastro')
    db = pd.DataFrame(db.get_all_records())
    return db

@st.cache_resource
def open_main_sheets_raw(_credenciais):
    sa = gspread.service_account_from_dict(_credenciais)
    sh = sa.open('Pessoas_App')
    return sh

@st.cache_resource
def open_personal_db(_sh, _ids):
    personal_db_raw = open_credencials(_sh, _ids)
    personal_db = pd.DataFrame(personal_db_raw.get_all_records())
    return personal_db

@st.cache_resource
def open_personal_db_raw(_sh, _ids):
    personal_db_raw = open_credencials(_sh, _ids)
    return personal_db_raw


def register(_p_db, _values):
    insert_values(_p_db, _values)
    st.cache_resource.clear()
    db = open_main_sheets(credenciais)
    sh = open_main_sheets_raw(credenciais)
    st.session_state.p_db = open_personal_db(sh, st.session_state.p_id)
    p_dbr = open_personal_db_raw(sh, st.session_state.p_id)
    succs = st.success('Data Registered Successfully')
    
def restart_analysis(video, video_temp):
    video.close()
    video_temp.close()
    st.session_state.run = 0

def delete_account(_sh, _p_db, _p_id):
    delete_worksheet(_sh, _p_db, _p_id)
    st.session_state.check = 0

def quit(x, video=None):
    if video is not None:
        video.close()
        os.remove(video.name)
    st.session_state.check = x
    st.session_state.name = ""
    st.session_state.password = ""
    st.session_state.nome = ""
    st.session_state.p_id = ""
    st.session_state.p_db = ""


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
if 'p_id' not in st.session_state:
    st.session_state.p_id = ''

imagem = Image.open("./data/Unifesp_simples_policromia_RGB.png")
imagem = imagem.resize((960, 250))
db = open_main_sheets(credenciais)
sh = open_main_sheets_raw(credenciais)

menu = ["Home", "Analysis", "Register", "Delete Account"]
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
    db = open_main_sheets(credenciais)
    with st.sidebar.form("form", clear_on_submit=True):
        name = st.text_input("Login", "", key='name')
        password = st.text_input("Password", "", type='password', key='password')
        for index, n in enumerate(zip(db['Login'].values, db['Senha'].values)):
            if n[0] == name and str(n[1]) == password:
                st.session_state.p_id = str(db['ID'][index])
                p_dbr = open_personal_db_raw(sh, st.session_state.p_id)
                st.session_state.p_db = open_personal_db(sh, st.session_state.p_id)
                st.session_state.check = 1
                st.session_state.nome = db['Nome'][index]
        submit_button = st.form_submit_button("Submit")
    quit_button = st.sidebar.button("Quit", on_click=quit, args=[0], key=secrets.token_hex(20))
    if st.session_state.check == 0:
        st.image(imagem, use_column_width=True)
        st.write('## Blefaro App')
        st.image(Image.open("./data/istockphoto-485347378-170667a.jpg"),use_column_width=True)
        st.subheader('Log-in to begin the analysis!')
        name = ""
        password = ""
    elif st.session_state.check == 1:
        st.image(imagem, use_column_width=True)
        st.success(f"Welcome {st.session_state.nome}")
        st.markdown(
            "**Upload** the video clicking the box **_'Browse Files'_**. You may choose the treatment phase between **'pre-treatment'** and **'post-treament'**. The video will be cut to **1 minute long**! "
            "To access previous results, select the **History** and to see the historical results in a chart access the **Charts** section!")
        choice = ['Analysis', 'History', 'Charts']
        select = st.selectbox("Menu", choice)
        if select == 'Analysis':
            st.title("Analysis")
            st.write("### Upload the video below:")
            video_file = st.file_uploader('Pre-treatment diagnosis video', type=['MOV', 'MP4'])
            video_temp = None
            msg = st.empty()
            msg.write("### Select the type of analysis:")
            analysis_sel = ['Pre-treatment', 'Post-treatment']
            analysis = st.selectbox("Select the type of analysis:", analysis_sel)
            analysis_type = 'post' if analysis == 'Post-treatment' else 'pre'
            msg.write("### Click start to initiate the 1 minute video:")
            video = tempfile.NamedTemporaryFile(delete=False)
            botao = st.empty()
            botao.button("Start", on_click=iniciar, args=[1], key='iniciar')
            while st.session_state.run == 1:
                msg.empty()
                try:
                    video.write(video_file.read())
                except AttributeError:
                    msg.write("### Upload a video below!")
                    st.error("Unable to identify the video")
                    st.session_state.run = 0
                    botao.button("Start", on_click=iniciar, args=[1], key='iniciar_after')
                    break
                if video_file is not None:
                    botao.button('Stop', on_click=stop, key=secrets.token_hex(20))
                    stframe = st.empty()
                    captura = cv2.VideoCapture(video.name)
                    t = Detector.calibragem(captura)
                    olhoe, olhod, total1, total2, txdeframes, thresh, st.session_state.run, video_temp = Detector.Captura(captura, t)
                    result_dict = {'Data': datetime.datetime.today().strftime("%d/%m/%Y, %H:%M:%S"), 'EAR1': str(olhoe),
                           'EAR2': str(olhod), 'Piscadas': [total1, total2], 'Estágio': analysis_type, 'Taxa de Frames': str(txdeframes),
                           'Limiar': str([thresh])}
                    try:
                        botao.empty()
                        st.button('Register Data', on_click=register, args=[p_dbr, result_dict], key=secrets.token_hex(20))
                        video.close()
                        os.remove(video.name)
                    except NameError:
                        botao.empty()
                        p_dbr = open_personal_db_raw(sh, st.session_state.p_id)
                        st.button('Register Data', on_click=register, args=[p_dbr, result_dict], key=secrets.token_hex(20))
                        video.close()
                    try:
                        botao.empty()
                        st.button("Make Another Analysis", on_click=restart_analysis, args=[video, video_temp], key=secrets.token_hex(20))
                    except NameError:
                        pass
            if video_temp is not None:
                st.button("Quit", on_click=quit, args=[0, video_temp], key=secrets.token_hex(20))
            else:
                st.button("Quit", on_click=quit, args=[0], key=secrets.token_hex(20))
        elif select == 'History':
            p_dbr = open_personal_db_raw(sh, st.session_state.p_id)
            st.title('History')
            try:
                st.dataframe(st.session_state.p_db[['Data', 'Piscadas', 'Estágio', 'EAR1', 'EAR2']].style.set_properties(
                    **{'background-color': 'white',
                    'color': 'green'}))
            except KeyError:
                st.error("There is still no data for this visualization", icon="🚨")
            st.button("Quit", on_click=quit, args=[0])
        elif select == 'Charts':
            st.title('Charts of History data')
            try:
                data = st.selectbox('Select the date:', np.unique(st.session_state.p_db['Data'].values))
                stage = st.selectbox('Select the phase:', np.unique(st.session_state.p_db['Estágio'].values))
                earesq, eardir, piscadas, txdeframes, limiar = read_values_from_date(open_personal_db(sh, st.session_state.p_id), data, stage)
            except KeyError:
                earesq, eardir, piscadas, txdeframes, limiar = None, None, None, None, None
            if earesq is None:
                st.error("There is still no data for this visualization", icon="🚨")
                st.button("Quit", on_click=quit, args=[0], key=secrets.token_hex(20))
            else:
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
                st.button("Quit", on_click=quit, args=[0], key=secrets.token_hex(20))

elif c == "Register":
    st.image(imagem, use_column_width=True)
    st.title("Create Account")
    form = st.form("form2", clear_on_submit=True)
    with form:
        logincadastro = st.text_input('Login:')
        nome1 = st.text_input("First name:")
        nome2 = st.text_input("Last name:")
        idade = st.text_input("Age:")
        cidade = st.text_input("City:")
        senha = st.text_input("Password (only 8 numbers or letters):", type='password')
        verificasenha = st.text_input("Repeat password:", type='password')
        submit = st.form_submit_button("Enviar")
        regex = re.compile('[@!#$%^&*()<>?/|}{~:âãíáàç,]')
        if submit:
            verification = 1
            if logincadastro in db['Nome'].values:
                st.error("Login name already in use", icon="🚨")
                verification = 0
            if senha != verificasenha:
                st.error("Password verification does not match", icon="🚨")
                verification = 0
            if logincadastro == '' or regex.search(logincadastro) is not None:
                st.error('Insert a valid login name',icon="🚨")
                verification = 0
            elif nome1 == '':
                st.error('Insert your name', icon="🚨")
                verification = 0
            elif nome2 == '':
                st.error('Insert your last name', icon="🚨")
                verification = 0
            elif idade == '':
                st.error('Insert your age', icon="🚨")
                verification = 0
            elif cidade == '':
                st.error('Insert your city',icon="🚨")
                verification = 0
            elif senha == '':
                st.error('Insert password',icon="🚨")
                verification = 0
            elif verification == 1:
                dados = {'Login': logincadastro, 'Nome': nome1, 'Sobrenome': nome2, 'Idade': [idade], 'Cidade': cidade,
                        'Senha': [senha], 'ID': secrets.token_hex(10)}
                try:    
                    create_credencials(sh, dados)
                except Exception as e:
                    st.error('Error creating credentials', icon="🚨")
                    st.error(e)
                else:
                    st.cache_resource.clear()
                    st.experimental_rerun()
                    st.success('Credentials created successfully!', icon="✅")
                        
elif c == 'Delete Account':
    st.title("Delete Account")
    success_check = 0
    submitted_form = False
    if st.session_state.check == 0 and success_check == 0 and submitted_form==False:
        st.error("You need to be logged in to delete your account", icon="🚨")
        st.error("If you are logged in but the page is not updating, click the button below")
        st.button("Refresh")
        db = open_main_sheets(credenciais)
        with st.sidebar.form("form", clear_on_submit=True):
            name = st.text_input("Login", "", key='name')
            password = st.text_input("Password", "", type='password', key='password')
            for index, n in enumerate(zip(db['Login'].values, db['Senha'].values)):
                if n[0] == name and str(n[1]) == password:
                    st.session_state.p_id = str(db['ID'][index])
                    p_dbr = open_personal_db_raw(sh, st.session_state.p_id)
                    st.session_state.p_db = open_personal_db(sh, st.session_state.p_id)
                    st.session_state.check = 1
                    st.session_state.nome = db['Nome'][index]
                    submited_form = True
            submit_button = st.form_submit_button("Submit")
        quit_button = st.sidebar.button("Quit", on_click=quit, args=[0], key=secrets.token_hex(20))
    elif st.session_state.check == 1:
        st.info(f":warning: Are you sure you want to delete your account, {st.session_state.nome}?  All data will be lost in the process :disappointed_relieved:")
        try:
            button = st.button("Delete Account")
            if button:
                st.info("Are you sure?")
                col1, col2 = st.columns(2)
                with col1:
                    button2 = st.button("Confirm",  on_click=delete_account, args=[
                                                                        sh, 
                                                                        open_personal_db_raw(sh, st.session_state.p_id), 
                                                                        st.session_state.p_id
                                                                        ], key=secrets.token_hex(20))
                with col2:   
                    button3 = st.button("Cancel", on_click=quit, args=[0], key=secrets.token_hex(20))
            
        except Exception as e:
            st.error('Error deleting account', icon="🚨")
            st.error(e)
        else:
            if st.session_state.check == 0:
                st.cache_resource.clear()
                st.experimental_rerun()
                success_check = 1
            if success_check == 1:
                st.success('Account deleted successfully!', icon="✅")