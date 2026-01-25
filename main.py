import streamlit as st
import time
import cv2

from State_Manager import StateManager

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

state = StateManager()
state.start()
# ==========================================
# 3. SINGLETONY (AI / KAMERY)
# ==========================================
@st.cache_resource
def get_manager(): return CameraManager()


@st.cache_resource
def get_pose_detector(): return PoseDetector(static_image_mode=False, model_complexity=1, smooth_landmarks=True)


@st.cache_resource
def get_visualizer(): return Visualizer()


@st.cache_resource
def get_smoother(): return LandmarkSmoother(window_size=5, min_visibility=0.5)


manager = get_manager()
pose_detector = get_pose_detector()
visualizer = get_visualizer()
smoother = get_smoother()

# Stan urządzeń
if 'devices' not in st.session_state: st.session_state['devices'] = manager.passive_scan()
if 'last_scan' not in st.session_state: st.session_state['last_scan'] = "Nigdy"

# ==========================================
# 4. UI ASSEMBLY (PASEK BOCZNY)
# ==========================================
render_sidebar()  # Renderuje nagłówek

# [NOWOŚĆ] Dodajemy placeholder na wykryte słowo
st.sidebar.markdown("### 🎤 Rozpoznawanie głosu")
voice_status_placeholder = st.sidebar.empty()  # Puste miejsce do aktualizacji w pętli
voice_status_placeholder.info(f"Ostatnia komenda: **{state.last_spoken_word}**")

st.sidebar.markdown("---")

camera_active, sel_front, sel_side = render_camera_controls(manager)
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

# ==========================================
# 5. GŁÓWNA PĘTLA APLIKACJI
# ==========================================
try:
    is_bad_form = False
    frame_counter = 0

    while True:
        # [NOWOŚĆ] Aktualizacja pola na pasku bocznym w czasie rzeczywistym
        # Wyświetlamy to, co ostatnio usłyszał Listener (zapisane w state)
        voice_status_placeholder.info(f"Ostatnia komenda: **{state.last_spoken_word}**")

        if camera_active:
            # 1. POBRANIE KLATKI Z FRONTU
            frame_f = manager.get_frame('front', resize_width=640)
            status_f = manager.get_status('front')

            # 2. PRZETWARZANIE AI & WIZUALIZACJA
            if frame_f is not None and pose_detector is not None:
                landmarks_f = pose_detector.detect(frame_f)
                if landmarks_f: landmarks_f = smoother.update(landmarks_f)

                visualizer.draw_skeleton(frame_f, landmarks_f, has_error=is_bad_form)

                # Symulacja licznika
                if state.is_tracking:
                    if frame_counter % 50 == 0: state.reps += 1

                errors_to_show = ["KOLANA DO SRODKA!"] if is_bad_form else []
                visualizer.draw_panel(frame_f, state.reps, state.last_spoken_word, errors=errors_to_show)

            # 3. OBSŁUGA DRUGIEJ KAMERY
            if single_mode:
                frame_s = frame_f.copy() if frame_f is not None else None
                status_s = status_f
            else:
                frame_s = manager.get_frame('side', resize_width=640)
                status_s = manager.get_status('side')
                if frame_s is not None and pose_detector is not None:
                    lm_s = pose_detector.detect(frame_s)
                    visualizer.draw_skeleton(frame_s, lm_s, has_error=False)

            # 4. WYŚWIETLANIE
            display_frame(ph_front, frame_f, status_f)
            display_frame(ph_side, frame_s, status_s)

            time.sleep(0.01) if frame_f is not None else time.sleep(0.1)
        else:
            time.sleep(0.5)

except Exception as e:
    ph_msg.error(f"Pętla przerwana: {e}")
    try:
        if pose_detector: pose_detector.close()
    except:
        pass