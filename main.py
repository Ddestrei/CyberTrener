import streamlit as st
import time
import cv2

# Importy modułów projektu
from src.processor.camera import CameraManager
from src.processor.pose import PoseDetector
from src.ui.visualizer import Visualizer
from src.utils.smoothing import LandmarkSmoother
from src.ui.dashboard import (
    render_sidebar, 
    render_camera_controls, 
    render_video_layout,
    display_frame
)

# Konfiguracja strony Streamlit
st.set_page_config(layout="wide", page_title="Cyber Trener")

# --- SINGLETONY ---
@st.cache_resource
def get_manager():
    return CameraManager()

@st.cache_resource
def get_pose_detector():
    return PoseDetector(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

@st.cache_resource
def get_visualizer():
    return Visualizer()

@st.cache_resource
def get_smoother():
    return LandmarkSmoother(window_size=5, min_visibility=0.5)

# Inicjalizacja obiektów
manager = get_manager()
pose_detector = get_pose_detector()
visualizer = get_visualizer()
smoother = get_smoother()

# --- STATE ---
if 'devices' not in st.session_state:
    st.session_state['devices'] = manager.passive_scan()
if 'last_scan' not in st.session_state:
    st.session_state['last_scan'] = "Nigdy"
if 'shown_errors' not in st.session_state:
    st.session_state['shown_errors'] = set()

# --- UI ASSEMBLY ---
render_sidebar()
camera_active, sel_front, sel_side = render_camera_controls(manager)

# Renderowanie layoutu wideo (Bez statystyk)
ph_front, ph_side, ph_msg = render_video_layout()

# --- LOGIKA STEROWANIA ---
single_mode = (sel_front == sel_side)

if camera_active:
    try:
        manager.start_camera('front', sel_front)
        if not single_mode:
            manager.start_camera('side', sel_side)
        else:
            manager.stop_role('side')
    except Exception as e:
        st.error(f"Blad startu: {e}")
else:
    manager.stop_all()

# --- GŁÓWNA PĘTLA APLIKACJI ---
try:
    # Zmienna sterująca kolorem (na razie mock)
    is_bad_form = False 
    
    while True:
        if camera_active:
            # 1. POBRANIE KLATKI
            frame_f = manager.get_frame('front', resize_width=640)
            status_f = manager.get_status('front')

            # 2. PRZETWARZANIE AI & WIZUALIZACJA
            if frame_f is not None and pose_detector is not None:
                # A. Detekcja
                landmarks = pose_detector.detect(frame_f)
                
                # B. Wygładzanie
                if landmarks:
                    landmarks = smoother.update(landmarks)
                
                # C. Rysowanie
                visualizer.draw_skeleton(frame_f, landmarks, has_error=is_bad_form)

            # 3. DRUGA KAMERA
            if single_mode:
                frame_s = frame_f.copy() if frame_f is not None else None
                status_s = status_f
            else:
                frame_s = manager.get_frame('side', resize_width=640)
                status_s = manager.get_status('side')

            # 4. WYŚWIETLANIE
            display_frame(ph_front, frame_f, status_f)
            display_frame(ph_side, frame_s, status_s)
            
            if frame_f is None and frame_s is None:
                time.sleep(0.1)
        else:
            time.sleep(0.5)

except Exception as e:
    ph_msg.error(f"Pętla przerwana: {e}")
    if pose_detector:
        pose_detector.close()