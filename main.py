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

# [FIX] Dodajemy argument 'key', aby wymusić stworzenie DWÓCH oddzielnych detektorów.
# Jeden będzie pamiętał historię ruchu z przodu, drugi z boku.
@st.cache_resource
def get_pose_detector(key):
    return PoseDetector(
        static_image_mode=False,
        model_complexity=1, 
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

# Wizualizator jest "głupi" (nie ma pamięci), więc wystarczy jeden wspólny.
@st.cache_resource
def get_visualizer():
    return Visualizer()

# [FIX] To samo dla wygładzania. Musimy mieć osobne bufory dla przodu i boku.
# Inaczej średnia krocząca mieszałaby współrzędne z dwóch kamer!
@st.cache_resource
def get_smoother(key):
    return LandmarkSmoother(window_size=5, min_visibility=0.5)

# Inicjalizacja obiektów
manager = get_manager()
visualizer = get_visualizer()

# TWORZYMY OSOBNE INSTANCJE!
detector_front = get_pose_detector("front_detector")
detector_side = get_pose_detector("side_detector")

smoother_front = get_smoother("front_smoother")
smoother_side = get_smoother("side_smoother")

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

# Renderowanie layoutu wideo
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
    is_bad_form = False 
    
    while True:
        if camera_active:
            # ==========================================
            # 1. KAMERA PRZEDNIA (FRONT)
            # ==========================================
            frame_f = manager.get_frame('front', resize_width=640)
            status_f = manager.get_status('front')

            if frame_f is not None and detector_front is not None:
                # Używamy dedykowanego detektora dla przodu
                landmarks_f = detector_front.detect(frame_f)
                
                # Używamy dedykowanego wygładzania dla przodu
                if landmarks_f:
                    landmarks_f = smoother_front.update(landmarks_f)
                
                visualizer.draw_skeleton(frame_f, landmarks_f, has_error=is_bad_form)

            # ==========================================
            # 2. KAMERA BOCZNA (SIDE)
            # ==========================================
            if single_mode:
                # W trybie single po prostu kopiujemy obraz z Frontu
                frame_s = frame_f.copy() if frame_f is not None else None
                status_s = status_f
            else:
                frame_s = manager.get_frame('side', resize_width=640)
                status_s = manager.get_status('side')
                
                if frame_s is not None and detector_side is not None:
                    # Używamy dedykowanego detektora dla boku
                    landmarks_s = detector_side.detect(frame_s)
                    
                    # Używamy dedykowanego wygładzania dla boku
                    if landmarks_s:
                        landmarks_s = smoother_side.update(landmarks_s)

                    visualizer.draw_skeleton(frame_s, landmarks_s, has_error=is_bad_form)

            # 3. WYŚWIETLANIE
            display_frame(ph_front, frame_f, status_f)
            display_frame(ph_side, frame_s, status_s)
            
            if frame_f is None and frame_s is None:
                time.sleep(0.1)
        else:
            time.sleep(0.5)

except Exception as e:
    ph_msg.error(f"Pętla przerwana: {e}")
    # Zamykamy oba detektory
    if detector_front: detector_front.close()
    if detector_side: detector_side.close()