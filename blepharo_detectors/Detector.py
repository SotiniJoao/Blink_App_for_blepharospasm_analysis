import imutils
from imutils import face_utils
import dlib
import cv2
from blepharo_detectors.EAR import EAR
import streamlit as st
import matplotlib.pyplot as plt
from scipy.spatial import distance as dist
import time
import numpy as np
import seaborn as sns
from collections import defaultdict
import tempfile
import os
import io
import pandas as pd
from moviepy.editor import VideoClip
import math

sns.set(style="whitegrid")


def EARmod(eye_points_list):
    Amin = dist.euclidean(min([i[1] for i in eye_points_list], key=lambda x: x[1]), min([i[5] for i in eye_points_list], key=lambda x: x[1]))
    Bmin = dist.euclidean(min([i[2] for i in eye_points_list], key=lambda x: x[1]), min([i[4] for i in eye_points_list], key=lambda x: x[1]))
    Cmax = dist.euclidean(max([i[0] for i in eye_points_list], key=lambda x: x[1]), max([i[3] for i in eye_points_list], key=lambda x: x[1]))
    Amax = dist.euclidean(max([i[1] for i in eye_points_list], key=lambda x: x[1]), max([i[5] for i in eye_points_list], key=lambda x: x[1]))
    Bmax = dist.euclidean(max([i[2] for i in eye_points_list], key=lambda x: x[1]), max([i[4] for i in eye_points_list], key=lambda x: x[1]))
    Cmin = dist.euclidean(min([i[0] for i in eye_points_list], key=lambda x: x[1]), min([i[3] for i in eye_points_list], key=lambda x: x[1]))
    earmin = (Amin + Bmin) / (2.0 * Cmax)
    earmax = (Amax + Bmax) / (2.0 * Cmin)
    return earmin, earmax

def save_eye_points(eye_points):
    dict_points = {}
    for i in range(0, 6):
        dict_points[i] = eye_points[i]
    return dict_points

def write_to_tempfile(video_frames, fps):
    # Create a temporary file to store the video
    temp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')

    def make_frame(t):
        frame_idx = int(t * fps)
        if frame_idx < len(video_frames):
            return video_frames[frame_idx]
        else:
            return video_frames[-1]

    video_clip = VideoClip(make_frame, duration=len(video_frames) / fps)
    video_clip.write_videofile(temp_video_file.name, fps=fps)

    return temp_video_file
    
    

def calibragem(captura):
    vet = []
    left_points = []
    right_points = []
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
            left_points.append(save_eye_points(Olhoesq))
            right_points.append(save_eye_points(Olhodir))
    earesqmin, earesqmax = EARmod(left_points)
    eardirmin, eardirmax = EARmod(right_points)
    mod_ear = ((eardirmin + earesqmin) / 2 + (eardirmax + earesqmax) / 2) / 2
    msg.empty()
    return mod_ear


def Captura(captura, thresh, fourier=0):
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("eye_predictor.dat")
    if captura.get(cv2.CAP_PROP_FRAME_COUNT) > 0:
        frame_counter = 0  # Or whatever as long as it is the same as next line
        captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
    (lStart, lEnd) = (0, 6)
    (rStart, rEnd) = (6, 12)
    txdeframes, vet, olhoe, olhod = [], [], [], []
    msg = st.empty()
    cont1, cont2, total1, total2, quadros = 0, 0, 0, 0, 0
    ar_frames = 1
    video = []
    holder = st.empty()
    run = 1
    progress_text = "Please wait, the video is being processed..."
    progress_bar = st.progress(0, text=progress_text)
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
            video.append(cap)
            progress_bar.progress(math.ceil(limitante/60 * 100), text=progress_text)
        if limitante == 60:
            progress_bar.empty()
            progress_bar.success('Video processed!', icon="✅")
            video_temp = write_to_tempfile(video, 30)
            holder.video(video_temp.name)
            with pd.option_context('mode.use_inf_as_na', True):
                # video_shown = video_writer(video, 30, 500, 500)    
                time.sleep(2)
                msg.write("### Charts & Video")
                if fourier == 1:
                    fft = np.abs(np.fft.fft(vet))
                    freq = np.arange(0, 1 / 30, (1 / 30) / fft.size)
                    fig1, ax1 = plt.subplots(figsize=(30, 10))
                    ax1.plot(freq, fft)
                    ax1.set_title('Transformada Rápida de Fourier do EAR')
                    ax1.set_xlabel('Frequência')
                    ax1.set_ylabel('Magnitude')
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

                # holder.empty()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric('Left Eye Blinks', total2)
                with col2:
                    st.metric('Right Eye Blinks', total1)
                
                st.pyplot(fig2)
                st.pyplot(fig3)
                run = 0
                break
    return olhoe, olhod, total1, total2, txdeframes, thresh, run, video_temp
