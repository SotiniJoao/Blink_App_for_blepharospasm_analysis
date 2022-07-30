import imutils
from imutils import face_utils
import dlib
import cv2
from MódulosBlefaro1.EAR import EAR
import streamlit as st
import matplotlib.pyplot as plt
from scipy.spatial import distance as dist
import time
import numpy as np
import seaborn as sns

sns.set(style="whitegrid")


def EARmod(olho1, olho2, olho3, olho4, olho5, olho6):
    Amin = dist.euclidean(min(olho2, key=lambda item: item[1]), min(olho6, key=lambda item: item[1]))
    Bmin = dist.euclidean(min(olho3, key=lambda item: item[1]), min(olho5, key=lambda item: item[1]))
    Cmax = dist.euclidean(max(olho1, key=lambda item: item[1]), max(olho4, key=lambda item: item[1]))
    Amax = dist.euclidean(max(olho2, key=lambda item: item[1]), max(olho6, key=lambda item: item[1]))
    Bmax = dist.euclidean(max(olho3, key=lambda item: item[1]), max(olho5, key=lambda item: item[1]))
    Cmin = dist.euclidean(min(olho1, key=lambda item: item[1]), min(olho4, key=lambda item: item[1]))
    earmin = (Amin + Bmin) / (2.0 * Cmax)
    earmax = (Amax + Bmax) / (2.0 * Cmin)
    return earmin, earmax


def calibragem(captura):
    vet = []
    ep1 = []
    ep2 = []
    ep3 = []
    ep4 = []
    ep5 = []
    ep6 = []
    dp1 = []
    dp2 = []
    dp3 = []
    dp4 = []
    dp5 = []
    dp6 = []
    q = 0
    msg = st.empty()
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("eye_predictor.dat")
    (lStart, lEnd) = (0, 6)
    (rStart, rEnd) = (6, 12)
    while True:
        ret, frame = captura.read()
        msg.info('Calibrating...')
        q += 1
        if not ret:
            break
        if q == 1000:
            break
        frame = imutils.resize(frame, width=500)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray_frame, 0)
        for face in faces:
            shape = predictor(gray_frame, face)
            shape = face_utils.shape_to_np(shape)
            Olhoesq = shape[lStart:lEnd]
            Olhodir = shape[rStart:rEnd]
            EAResq = EAR(Olhoesq)
            EARdir = EAR(Olhodir)
            ear = (EAResq + EARdir) / 2.0
            vet.append(ear)
            ep1.append(Olhoesq[0])
            ep2.append(Olhoesq[1])
            ep3.append(Olhoesq[2])
            ep4.append(Olhoesq[3])
            ep5.append(Olhoesq[4])
            ep6.append(Olhoesq[5])
            dp1.append(Olhodir[0])
            dp2.append(Olhodir[1])
            dp3.append(Olhodir[2])
            dp4.append(Olhodir[3])
            dp5.append(Olhodir[4])
            dp6.append(Olhodir[5])
    earesqmin, earesqmax = EARmod(ep1, ep2, ep3, ep4, ep5, ep6)
    eardirmin, eardirmax = EARmod(dp1, dp2, dp3, dp4, dp5, dp6)
    modear = ((eardirmin + earesqmin) / 2 + (eardirmax + earesqmax) / 2) / 2
    msg.empty()
    return modear


def Captura(captura, thresh):
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("eye_predictor.dat")
    if captura.get(cv2.CAP_PROP_FRAME_COUNT) > 0:
        frame_counter = 0  # Or whatever as long as it is the same as next line
        captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
    (lStart, lEnd) = (0, 6)
    (rStart, rEnd) = (6, 12)
    txdeframes = []
    vet = []
    olhoe = []
    olhod = []
    bar = st.empty()
    msg = st.empty()
    msg.write("### Video:")
    cont1 = 0
    cont2 = 0
    total = 0
    total1 = 0
    total2 = 0
    thresh = thresh
    ar_frames = 1
    quadros = 0
    holder = st.empty()
    holder.image([])
    run = 1
    while captura.isOpened():
        ret, frame = captura.read()
        quadros += 1
        limitante = quadros / 30
        st.spinner('Making predictions...')
        if not ret:
            break
        cap = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cap = imutils.resize(cap, width=500)
        frame = imutils.resize(frame, width=500)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray_frame, 0)
        for face in faces:
            shape = predictor(gray_frame, face)
            shape = face_utils.shape_to_np(shape)
            olhoesq = shape[lStart:lEnd]
            olhodir = shape[rStart:rEnd]
            earesq = EAR(olhoesq)
            eardir = EAR(olhodir)
            ear = (earesq + eardir) / 2.0
            vet.append(ear)
            olhoe.append(round(earesq, 3))
            olhod.append(round(eardir, 3))
            txdeframes.append(quadros / 30)
            hullesq = cv2.convexHull(olhoesq)
            hulldir = cv2.convexHull(olhodir)
            cv2.drawContours(cap, [hullesq], -1, (255, 0, 0), 1)
            cv2.drawContours(cap, [hulldir], -1, (0, 0, 255), 1)
            if eardir < thresh:
                cont1 += 1
            elif cont1 >= ar_frames:
                total1 += 1
                cont1 = 0
            if earesq < thresh:
                cont2 += 1
            elif cont2 >= ar_frames:
                total2 += 1
                cont2 = 0
            holder.image(cap, use_column_width=True)
        if limitante == 60:
            time.sleep(2)
            msg.write("### Charts")
            # fft = np.abs(np.fft.fft(vet))
            # freq = np.arange(0, 1 / 30, (1 / 30) / fft.size)
            # fig1, ax1 = plt.subplots(figsize=(30, 10))
            # ax1.plot(freq, fft)
            # ax1.set_title('Transformada Rápida de Fourier do EAR')
            # ax1.set_xlabel('Frequência')
            # ax1.set_ylabel('Magnitude')
            fig2, ax2 = plt.subplots(figsize=(30, 10))
            sns.lineplot(x=txdeframes, y=olhoe, ax=ax2, color='blue', label='EAR right eye').axhline(thresh,
                                                                                                    c='darkblue',
                                                                                                    label='Threshold',
                                                                                                    ls=':')
            ax2.set_title('Left Eye Aspect Ratio per Time', fontsize=25)
            ax2.set_xlabel('Time (s)',fontsize=20)
            ax2.set_ylabel('EAR',fontsize=20)
            ax2.legend(prop={'size': 15})

            fig3, ax3 = plt.subplots(figsize=(30, 10))
            sns.lineplot(x=txdeframes, y=olhod, ax=ax3, color='red', label='EAR left eye').axhline(thresh, c='darkblue',
                                                                                                   label='Threshold',
                                                                                                   ls=':')
            ax3.set_title('Right Eye Aspect Ratio per Time', fontsize=25)
            ax3.set_xlabel('Time (s)',fontsize=20)
            ax3.set_ylabel('EAR', fontsize=20)
            ax3.legend(prop={'size': 15})

            holder.empty()
            st.metric('Right Eye Blinks', total1)
            st.metric('Left Eye Blinks', total2)
            st.pyplot(fig2)
            st.pyplot(fig3)
            run = 0
            break
    return olhoe, olhod, total, txdeframes, thresh, run
