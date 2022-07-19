import gspread
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import streamlit as st
import time
import cv2


def create_credencials(sh, values):
    wks = sh.worksheet('Cadastro')
    val = pd.DataFrame(values)
    insert_values(wks, val)
    nwks = create_open_values_sheet(sh, values['ID'])


def open_credencials(sh, name):
    try:
        wks = sh.worksheet(name)
        return wks
    except gspread.exceptions.WorksheetNotFound:
        return 0


def create_open_values_sheet(sh, wsname):
    try:
        work = sh.add_worksheet(title=wsname, rows=100, cols=7)
        wks = sh.worksheet(wsname)
        wks.update('A1', 'Data')
        wks.update('B1', 'EAR1')
        wks.update('C1', 'EAR2')
        wks.update('D1', 'Piscadas')
        wks.update('E1', 'Estágio')
        wks.update('F1', 'Taxa de Frames')
        wks.update('G1', 'Limiar')
        return wks
    except gspread.exceptions.APIError:
        wks = sh.worksheet(wsname)
        return wks


def first_values_update(wrks, values):
    wrks.update('A2', values['Data'])
    wks.update('B2', values['EAR1'])
    wks.update('C2', values['EAR2'])
    wks.update('D2', values['Piscadas'])
    wks.update('E2', values['Estágio'])
    wks.update('F1', values['Taxa de Frames'])
    wks.update('G1', values['Limiar'])


def insert_values(wksheet, values):
    val = pd.DataFrame(values)
    df = pd.DataFrame(wksheet.get_all_records())
    df = pd.concat([df, val]).reset_index(drop=True)
    wksheet.update([df.columns.values.tolist()] + df.values.tolist())


def read_values_from_date(wksheet, date, stage):
    df = wksheet
    row = df.loc[(df['Data'] == date) & (df['Estágio'] == stage)]
    earesq = json.loads(row['EAR1'].item())
    eardir = json.loads(row['EAR2'].item())
    txdeframes = json.loads(row['Taxa de Frames'].item())
    piscadas = row['Piscadas'].values
    limiar = json.loads(str(row['Limiar'].item()))
    return earesq, eardir, piscadas, txdeframes, limiar



