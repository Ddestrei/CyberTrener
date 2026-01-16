import streamlit as st
import cv2
import time
import numpy as np

# Importy modułów projektu
from src.ui.dashboard import render_sidebar, render_main_layout
from src.processor.camera import VideoThread

# --- [FRONTEND] KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="Cyber Trener",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- SHARED STATE ---
# !!!!!!!!!!!!!!!!!
# To dla was drużyna
# !!!!!!!!!!!!!!!!!
def init_session_state():
    # 1. Licznik powtórzeń
    if 'reps' not in st.session_state: st.session_state['reps'] = 0
    
    # 2. Aktualne ćwiczenie
    if 'current_exercise' not in st.session_state: st.session_state['current_exercise'] = None
    
    # 3. Komendy głosowe
    if 'voice_command' not in st.session_state: st.session_state['voice_command'] = ""
    
    # 4. Błędy techniczne (Feedback)
    if 'errors' not in st.session_state: st.session_state['errors'] = []
    
    # 5. Flagi systemowe
    if 'voice_enabled' not in st.session_state: st.session_state['voice_enabled'] = True
    if 'tts_enabled' not in st.session_state: st.session_state['tts_enabled'] = True
    if 'is_running' not in st.session_state: st.session_state['is_running'] = True

init_session_state()

# Helper: Konwersja inputu z sidebaru
def parse_source(src_input):
    src_input = str(src_input).strip()
    if src_input.isdigit(): return int(src_input)
    return src_input

# --- RENDERING UI ---
render_sidebar()
ph_front, ph_side, ph_msg = render_main_layout()

# Pobranie konfiguracji kamer
raw_front = st.session_state.get('cam_front', '0')
raw_side = st.session_state.get('cam_side', '0')
src_front = parse_source(raw_front)
src_side = parse_source(raw_side)

# Wykrycie czy ta sama kamera w obu oknach
single_camera_mode = (src_front == src_side) and isinstance(src_front, int)

# --- [CORE] START WĄTKÓW ---
cam_front_thread = None
cam_side_thread = None

if single_camera_mode:
    ph_msg.info(f"[INFO] Tryb Laptopa: Kamera {src_front} obsługuje oba widoki.")
    cam_front_thread = VideoThread(src=src_front)
    cam_front_thread.start()
else:
    ph_msg.info(f"[INFO] Tryb Dual: Przód={src_front}, Bok={src_side}")
    cam_front_thread = VideoThread(src=src_front)
    cam_side_thread = VideoThread(src=src_side)
    cam_front_thread.start()
    cam_side_thread.start()

# Zmienne do liczenia FPS
p_time = 0

# --- [CORE] GŁÓWNA PĘTLA APLIKACJI ---
try:
    while True:
        # 1. POBIERANIE DANYCH
        raw_frame_f = cam_front_thread.get_frame()
        
        if raw_frame_f is not None:
            frame_f = raw_frame_f.copy()
        else:
            frame_f = None

        # Obsługa drugiej kamery
        if single_camera_mode:
            frame_s = frame_f # Wskazuje na tę samą kopię
        else:
            raw_frame_s = cam_side_thread.get_frame()
            frame_s = raw_frame_s.copy() if raw_frame_s is not None else None

        # 2. PRZETWARZANIE AI (LOGIC LAYER) - [MIEJSCE DLA BACKENDU]
        # -----------------------------------------------------------
        # TODO: Tutaj dodaje się logikę MediaPipe.
        # -----------------------------------------------------------

        # 3. LICZNIK FPS (Diagnostyka)
        c_time = time.time()
        diff = c_time - p_time
        fps = 1 / diff if diff > 0 else 0
        p_time = c_time
        
        # Rysujemy FPS na naszej kopii klatki
        if frame_f is not None:
             cv2.putText(frame_f, f"FPS: {int(fps)}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 4. OPTYMALIZACJA WYŚWIETLANIA
        # Opcjonalne zmniejszanie obrazu dla słabszych komputerów
        if st.session_state.get('low_perf_mode', False):
            if frame_f is not None: frame_f = cv2.resize(frame_f, (320, 240))
            if frame_s is not None and not single_camera_mode: 
                frame_s = cv2.resize(frame_s, (320, 240))

        # 5. WYŚWIETLANIE (OUTPUT LAYER)
        # Konwersja BGR (OpenCV) -> RGB (Streamlit)
        if frame_f is not None:
            display_f = cv2.cvtColor(frame_f, cv2.COLOR_BGR2RGB)
            ph_front.image(display_f, channels="RGB", width="stretch")
            
            # W trybie laptopa dublujemy obraz
            if single_camera_mode:
                ph_side.image(display_f, channels="RGB", width="stretch")
        
        if not single_camera_mode and frame_s is not None:
            display_s = cv2.cvtColor(frame_s, cv2.COLOR_BGR2RGB)
            ph_side.image(display_s, channels="RGB", width="stretch")

except Exception as e:
    ph_msg.error(f"Błąd pętli głównej: {e}")

finally:
    # Sprzątanie zasobów
    if cam_front_thread: cam_front_thread.stop()
    if cam_side_thread: cam_side_thread.stop()