import streamlit as st
import cv2
import time
import numpy as np

# --- IMPORTS ---
try:
    from State_Manager import StateManager
except ImportError:
    import sys
    import os

    sys.path.append(os.getcwd())
    from State_Manager import StateManager

from src.processor.camera import CameraManager
from src.processor.pose import PoseDetector
from src.ui.visualizer import Visualizer
# [FIX 1] Przywrócono import wygładzania
from src.utils.smoothing import LandmarkSmoother

from src.exercises.plank import Plank
from src.exercises.situp import SitUp
from src.exercises.bicep_curl import BicepCurl
from src.exercises.lateral_raise import LateralRaise
from src.exercises.overhead_press import OverheadPress

# --- 1. PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="CyberTrener AI")


# --- 2. SINGLETON INITIALIZATION ---
@st.cache_resource
def get_camera_manager(): return CameraManager()


# [FIX 3] Dodano parametr 'key', aby mieć osobne instancje dla Front i Side
@st.cache_resource
def get_pose_detector(key): return PoseDetector()


@st.cache_resource
def get_state_manager():
    manager = StateManager()
    manager.start()
    return manager


@st.cache_resource
def get_visualizer(): return Visualizer()


# [FIX 1] Singleton dla Smoothera z kluczem
@st.cache_resource
def get_smoother(key):
    return LandmarkSmoother(window_size=5, min_visibility=0.5)


camera_manager = get_camera_manager()
visualizer = get_visualizer()
state_manager = get_state_manager()

# Inicjalizacja osobnych instancji dla obu widoków
detector_front = get_pose_detector("front")
detector_side = get_pose_detector("side")
smoother_front = get_smoother("front")
smoother_side = get_smoother("side")

# --- 3. SIDEBAR ---
st.sidebar.title("CyberTrener Controls")
st.sidebar.subheader("Video Source")

if 'available_cams' not in st.session_state:
    try:
        st.session_state['available_cams'] = camera_manager.passive_scan()
    except AttributeError:
        st.session_state['available_cams'] = [0, 1, 2]

cam_options = st.session_state['available_cams']

front_cam_idx = st.sidebar.selectbox("Front Camera", options=cam_options, index=0)
side_cam_idx = st.sidebar.selectbox("Side Camera", options=cam_options, index=1 if len(cam_options) > 1 else 0)

# [FIX 2] Logika Single Mode (zapobieganie konfliktom kamer)
single_mode = (front_cam_idx == side_cam_idx)

col_start, col_stop = st.sidebar.columns(2)
if col_start.button("START SYSTEM"):
    # Jeśli kamery są te same, uruchamiamy tylko jedną rolę
    camera_manager.start_camera('front', front_cam_idx)
    if not single_mode:
        camera_manager.start_camera('side', side_cam_idx)
    else:
        # Ważne: Jeśli single mode, upewnij się, że rola side jest zatrzymana
        camera_manager.stop_role('side')

    st.session_state['app_active'] = True

if col_stop.button("STOP SYSTEM"):
    camera_manager.stop_all()
    st.session_state['app_active'] = False

st.sidebar.markdown("---")
st.sidebar.subheader("Voice Command Status")
status_text = st.sidebar.empty()
cmd_text = st.sidebar.empty()
reps_text = st.sidebar.empty()

# --- 4. MAIN LAYOUT ---
col_front, col_side = st.columns(2)
with col_front:
    st.header("Front View")
    front_placeholder = st.empty()

with col_side:
    st.header("Side View")
    side_placeholder = st.empty()


# --- 5. HELPERS ---
def get_current_exercise_logic(exercise_name):
    name = exercise_name.lower()
    if name == "plank": return Plank()
    if name == "sit ups": return SitUp()
    if name == "bicep curl": return BicepCurl()
    if name == "lateral raise": return LateralRaise()
    if name == "press": return OverheadPress()
    return None


def create_placeholder_frame(text="NO SIGNAL"):
    blk = np.zeros((480, 640, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (640 - text_size[0]) // 2
    text_y = (480 + text_size[1]) // 2
    cv2.putText(blk, text, (text_x, text_y), font, font_scale, (100, 100, 100), thickness)
    return blk


# --- 6. MAIN LOOP ---
if st.session_state.get('app_active', False):

    current_exercise_name = state_manager.last_spoken_word
    exercise_logic = get_current_exercise_logic(current_exercise_name)

    while True:
        # A. UI Updates
        status_icon = "🟢" if state_manager.is_tracking else "🔴"
        status_label = "Tracking" if state_manager.is_tracking else "Waiting"

        status_text.markdown(f"**Status:** {status_icon} {status_label}")
        cmd_text.markdown(f"**Exercise:** {state_manager.last_spoken_word}")
        reps_text.markdown(f"**Reps:** {state_manager.reps}")

        # B. Handle Reset Command
        if state_manager.is_reset:
            if exercise_logic:
                if hasattr(exercise_logic, 'reset_stats'):
                    exercise_logic.reset_stats()
                elif hasattr(exercise_logic, 'reset'):
                    exercise_logic.reset()
            state_manager.reps = 0
            state_manager.is_reset = 0

        # C. Logic Switching
        if state_manager.last_spoken_word != current_exercise_name:
            current_exercise_name = state_manager.last_spoken_word
            exercise_logic = get_current_exercise_logic(current_exercise_name)
            if exercise_logic:
                if hasattr(exercise_logic, 'reset_stats'):
                    exercise_logic.reset_stats()
                elif hasattr(exercise_logic, 'reset'):
                    exercise_logic.reset()

        # D. Get Frames
        frame_front = camera_manager.get_frame('front')

        # [FIX 2] Obsługa Single Mode dla klatek
        if single_mode:
            frame_side = frame_front.copy() if frame_front is not None else None
        else:
            frame_side = camera_manager.get_frame('side')

        # --- FRONT CAMERA HANDLING ---
        if frame_front is not None:
            landmarks = detector_front.detect(frame_front)

            # [FIX 1] Aplikacja wygładzania
            if landmarks:
                landmarks = smoother_front.update(landmarks)

            feedback = []
            if state_manager.is_tracking and exercise_logic and landmarks:
                exercise_logic.update(landmarks)
                state_manager.reps = exercise_logic.reps_count
                if hasattr(exercise_logic, 'errors'):
                    feedback = exercise_logic.errors

            _ = visualizer.draw_skeleton(frame_front, landmarks, has_error=bool(feedback))
            _ = visualizer.draw_panel(
                frame_front,
                reps=state_manager.reps,
                exercise_name=current_exercise_name,
                errors=feedback
            )
            front_placeholder.image(cv2.cvtColor(frame_front, cv2.COLOR_BGR2RGB), width="stretch")
        else:
            placeholder = create_placeholder_frame("NO CAMERA / LOADING...")
            front_placeholder.image(placeholder, width="stretch")

        # --- SIDE CAMERA HANDLING ---
        if frame_side is not None:
            # Używamy osobnego detektora dla boku
            lm_side = detector_side.detect(frame_side)

            # [FIX 1] Wygładzanie dla boku (osobna instancja)
            if lm_side:
                lm_side = smoother_side.update(lm_side)

            _ = visualizer.draw_skeleton(frame_side, lm_side, has_error=False)
            side_placeholder.image(cv2.cvtColor(frame_side, cv2.COLOR_BGR2RGB), width="stretch")
        else:
            placeholder_side = create_placeholder_frame("SIDE CAM OFF")
            side_placeholder.image(placeholder_side, width="stretch")

        # Prevent CPU hogging
        if frame_front is None and frame_side is None:
            time.sleep(0.1)

else:
    front_placeholder.info("System stopped. Press 'START SYSTEM' in the sidebar.")