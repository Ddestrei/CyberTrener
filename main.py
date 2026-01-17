import streamlit as st
import cv2
import time
import numpy as np
import os

# Importy modułów projektu
from src.ui.dashboard import render_sidebar, render_main_layout
from src.processor.camera import VideoThread
from src.ui.visualizer import Visualizer
# Importujemy NOWY silnik (Tasks API)
from src.processor.pose_engine import PoseEngineV2

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Cyber Trener",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. SZYNA DANYCH (SESSION STATE) ---
def init_session_state():
    if 'reps' not in st.session_state: st.session_state['reps'] = 0
    if 'current_exercise' not in st.session_state: st.session_state['current_exercise'] = "AI Active"
    if 'voice_command' not in st.session_state: st.session_state['voice_command'] = ""
    if 'errors' not in st.session_state: st.session_state['errors'] = []
    if 'voice_enabled' not in st.session_state: st.session_state['voice_enabled'] = True
    if 'tts_enabled' not in st.session_state: st.session_state['tts_enabled'] = True
    if 'is_running' not in st.session_state: st.session_state['is_running'] = True

init_session_state()

# Helper
def parse_source(src_input):
    src_input = str(src_input).strip()
    if src_input.isdigit(): return int(src_input)
    return src_input

# --- 3. RENDERING UI (Przywrócone) ---
render_sidebar()
ph_front, ph_side, ph_msg = render_main_layout()

# --- 4. INICJALIZACJA AI (Nowy Silnik) ---
engine = None
model_path = 'pose_landmarker.task'

if os.path.exists(model_path):
    try:
        engine = PoseEngineV2(model_path=model_path)
        ph_msg.success(f"Silnik AI (MediaPipe Tasks) załadowany! Model: {model_path}")
    except Exception as e:
        ph_msg.error(f"Błąd ładowania silnika AI: {e}")
else:
    ph_msg.error(f"BRAK PLIKU MODELU: {model_path}. Pobierz go komendą wget!")

# Wizualizer
viz = Visualizer()

# --- 5. KONFIGURACJA KAMER ---
raw_front = st.session_state.get('cam_front', '0')
raw_side = st.session_state.get('cam_side', '0')
src_front = parse_source(raw_front)
src_side = parse_source(raw_side)

single_camera_mode = (src_front == src_side) and isinstance(src_front, int)

cam_front_thread = None
cam_side_thread = None

# Start wątków wideo
if single_camera_mode:
    cam_front_thread = VideoThread(src=src_front)
    cam_front_thread.start()
    ph_msg.info(f"Tryb Laptopa: Kamera {src_front}")
else:
    cam_front_thread = VideoThread(src=src_front)
    cam_side_thread = VideoThread(src=src_side)
    cam_front_thread.start()
    cam_side_thread.start()
    ph_msg.info(f"Tryb Dual: {src_front} + {src_side}")

# Zmienne pętli
p_time = 0

# --- 6. GŁÓWNA PĘTLA APLIKACJI ---
try:
    while True:
        # A. POBIERANIE DANYCH
        raw_frame_f = cam_front_thread.get_frame()
        if raw_frame_f is not None:
            frame_f = raw_frame_f.copy()
        else:
            frame_f = None

        if single_camera_mode:
            frame_s = frame_f
        else:
            raw_frame_s = cam_side_thread.get_frame()
            frame_s = raw_frame_s.copy() if raw_frame_s is not None else None

        # B. PRZETWARZANIE AI (Tylko jeśli mamy klatkę i silnik)
        ai_result = None
        if frame_f is not None and engine:
            try:
                # Nowy silnik przetwarza klatkę
                ai_result = engine.process_frame(frame_f)
            except Exception as e:
                print(f"AI Error: {e}")

        # C. WIZUALIZACJA (Overlay)
        if frame_f is not None:
            # Rysowanie szkieletu (Nowy wizualizer obsługuje wynik z Tasks)
            if ai_result:
                has_error = len(st.session_state['errors']) > 0
                viz.draw_skeleton(frame_f, ai_result, has_error)

            # Rysowanie panelu HUD (Licznik, Ćwiczenie)
            viz.draw_panel(frame_f, 
                          st.session_state['reps'], 
                          st.session_state['current_exercise'], 
                          st.session_state['errors'])

            # Licznik FPS
            c_time = time.time()
            fps = 1 / (c_time - p_time) if (c_time - p_time) > 0 else 0
            p_time = c_time
            
            cv2.putText(frame_f, f"FPS: {int(fps)}", (frame_f.shape[1]-120, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # D. WYŚWIETLANIE
        if frame_f is not None:
            display_f = cv2.cvtColor(frame_f, cv2.COLOR_BGR2RGB)
            ph_front.image(display_f, channels="RGB", width="stretch")
            
            if single_camera_mode:
                ph_side.image(display_f, channels="RGB", width="stretch")
        
        if not single_camera_mode and frame_s is not None:
            display_s = cv2.cvtColor(frame_s, cv2.COLOR_BGR2RGB)
            ph_side.image(display_s, channels="RGB", width="stretch")
        
        # Krótki sleep, żeby nie spalić CPU jeśli nie ma klatki
        if frame_f is None:
            time.sleep(0.01)

except Exception as e:
    ph_msg.error(f"Krytyczny błąd pętli: {e}")

finally:
    # Sprzątanie
    if cam_front_thread: cam_front_thread.stop()
    if cam_side_thread: cam_side_thread.stop()
    if engine: engine.close()