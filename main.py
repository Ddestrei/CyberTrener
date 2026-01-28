"""
CyberTrener - AI-powered workout coach with real-time pose detection.
Optimized for performance with Frame Skipping.
"""

import streamlit as st
import cv2
import numpy as np
import time

# --- IMPORTS ---
from src.controller import WorkoutController, EXERCISE_REGISTRY
from src.ui.visualizer import Visualizer
from src.audio.speaker import TextToSpeechManager
from src.audio.listener import ExerciseListener

# --- 1. PAGE CONFIG ---
st.set_page_config(
    layout="wide",
    page_title="CyberTrener AI",
    page_icon="🏋️"
)


# =============================================================================
# SINGLETON INITIALIZATION
# =============================================================================

@st.cache_resource
def get_tts_manager():
    return TextToSpeechManager()


@st.cache_resource
def get_command_queue():
    import queue
    return queue.Queue()


@st.cache_resource
def get_voice_listener(_command_queue):
    listener = ExerciseListener(_command_queue)
    #listener.start()
    return listener


@st.cache_resource
def get_workout_controller(_tts_manager, _command_queue):
    return WorkoutController(
        tts_manager=_tts_manager,
        command_queue=_command_queue,
    )


@st.cache_resource
def get_visualizer():
    return Visualizer()


# Initialize Singletons
tts_manager = get_tts_manager()
command_queue = get_command_queue()
voice_listener = get_voice_listener(command_queue)
controller = get_workout_controller(tts_manager, command_queue)
visualizer = get_visualizer()


# =============================================================================
# UI HELPER FUNCTIONS
# =============================================================================

def create_placeholder_frame(text: str = "NO SIGNAL", width: int = 640, height: int = 480) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1.0, 2)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    cv2.putText(frame, text, (text_x, text_y), font, 1.0, (100, 100, 100), 2)
    return frame


def render_frame_with_overlay(frame: np.ndarray, landmarks: list, stats: object, vis: Visualizer,
                              show_skeleton: bool = True) -> np.ndarray:
    if frame is None:
        return create_placeholder_frame("NO CAMERA")

    # Rysuj szkielet tylko jeśli są dane
    if show_skeleton and landmarks:
        has_error = len(stats.errors) > 0 if stats else False
        vis.draw_skeleton(frame, landmarks, has_error=has_error)

    # Rysuj panel statystyk
    if stats:
        vis.draw_panel(frame, reps=stats.reps, exercise_name=stats.exercise_name, errors=stats.errors)

    return frame


# =============================================================================
# SIDEBAR UI
# =============================================================================

st.sidebar.title("🏋️ CyberTrener")
st.sidebar.markdown("---")

# --- Camera Setup ---
st.sidebar.subheader("📷 Camera Setup")
if 'available_cams' not in st.session_state:
    st.session_state['available_cams'] = controller.camera_manager.passive_scan()

cam_options = st.session_state['available_cams']

front_cam_idx = st.sidebar.selectbox("Front Camera", options=cam_options, index=0)
side_cam_idx = st.sidebar.selectbox("Side Camera", options=cam_options, index=min(1, len(cam_options) - 1))

col_start, col_stop = st.sidebar.columns(2)
with col_start:
    if st.button("▶️ START", width="stretch", type="primary"):
        controller.start_cameras(front_id=front_cam_idx, side_id=side_cam_idx)
        st.session_state['app_active'] = True
        st.rerun()

with col_stop:
    if st.button("⏹️ STOP", width="stretch"):
        controller.stop_cameras()
        st.session_state['app_active'] = False
        st.rerun()

if st.sidebar.button("🔄 Rescan Cameras"):
    st.session_state['available_cams'] = controller.camera_manager.passive_scan()
    st.rerun()

st.sidebar.markdown("---")

# --- Exercise Selection ---
st.sidebar.subheader("🎯 Exercise")
exercise_options = ["None"] + list(EXERCISE_REGISTRY.keys())
current_exercise = controller._current_exercise_name if controller._current_exercise_name != "None" else "None"
try:
    current_index = exercise_options.index(current_exercise)
except ValueError:
    current_index = 0

selected_exercise = st.sidebar.selectbox("Select Exercise", options=exercise_options, index=current_index)
if selected_exercise != "None" and selected_exercise != current_exercise:
    controller.inject_command(selected_exercise)

st.sidebar.markdown("---")

# --- Controls ---
st.sidebar.subheader("🎮 Controls")
c1, c2, c3 = st.sidebar.columns(3)
if c1.button("▶️ Start", width="stretch"): controller.inject_command("start")
if c2.button("⏸️ Stop", width="stretch"): controller.inject_command("end")
if c3.button("🔄 Reset", width="stretch"): controller.inject_command("reset")

# =============================================================================
# MAIN CONTENT AREA
# =============================================================================

st.title("CyberTrener AI")
col_front, col_side = st.columns(2)

with col_front:
    st.subheader("📷 Front View")
    front_placeholder = st.empty()

with col_side:
    st.subheader("📷 Side View")
    side_placeholder = st.empty()

stats_cols = st.columns(4)
stat_exercise = stats_cols[0].empty()
stat_reps = stats_cols[1].empty()
stat_state = stats_cols[2].empty()
stat_errors = stats_cols[3].empty()

# =============================================================================
# MAIN LOOP (OPTIMIZED)
# =============================================================================

if st.session_state.get('app_active', False):

    # PARAMETRY OPTYMALIZACJI
    DISPLAY_W, DISPLAY_H = 480, 360  # Jeszcze mniejsza rozdzielczość dla UI (płynniej)
    UI_UPDATE_DIVIDER = 3  # Aktualizuj UI co 3 klatkę (Logika co 1 klatkę)
    frame_counter = 0

    while True:
        # 1. LOGIKA - ZAWSZE (Dla precyzji wykrywania ruchu)
        result = controller.process_frame()
        stats = result['stats']

        # 2. UI - TYLKO CO 'N' KLATEK (Dla wydajności przeglądarki)
        if frame_counter % UI_UPDATE_DIVIDER == 0:

            # --- Update Texts (Metryki też obciążają, więc robimy rzadziej) ---
            stat_exercise.metric("Exercise", stats.exercise_name.title())
            stat_reps.metric("Reps", stats.reps)
            stat_state.metric("Phase", stats.exercise_state)

            if stats.errors:
                stat_errors.error(f"⚠️ {stats.errors[0]}")
            else:
                stat_errors.success("✅ OK")

            # --- Render Front Camera ---
            if result['front'].is_available and result['front'].frame is not None:
                # Klonujemy klatkę i nakładamy rysunki
                disp_frame = result['front'].frame.copy()
                disp_frame = render_frame_with_overlay(disp_frame, result['front'].landmarks, stats, visualizer)

                # Resize + Convert
                disp_frame = cv2.resize(disp_frame, (DISPLAY_W, DISPLAY_H))
                disp_frame = cv2.cvtColor(disp_frame, cv2.COLOR_BGR2RGB)
                front_placeholder.image(disp_frame, width="stretch")

            # --- Render Side Camera ---
            if result['side'].is_available and result['side'].frame is not None:
                disp_frame = result['side'].frame.copy()
                if result['side'].landmarks:
                    visualizer.draw_skeleton(disp_frame, result['side'].landmarks, has_error=False)

                disp_frame = cv2.resize(disp_frame, (DISPLAY_W, DISPLAY_H))
                disp_frame = cv2.cvtColor(disp_frame, cv2.COLOR_BGR2RGB)
                side_placeholder.image(disp_frame, width="stretch")

            # Mały sleep tylko w klatce renderowania UI, żeby dać oddech przeglądarce
            time.sleep(0.01)

        # Inkrementacja licznika
        frame_counter += 1

else:
    front_placeholder.info("Press START")
    side_placeholder.info("Press START")