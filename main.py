import streamlit as st
import time
import cv2

# Importy modułów projektu
from src.processor.camera import CameraManager
from src.processor.pose import PoseDetector
from src.ui.visualizer import Visualizer
from src.ui.dashboard import (
    render_sidebar, 
    render_camera_controls, 
    render_video_layout, 
    display_frame
)

# Konfiguracja strony Streamlit
st.set_page_config(layout="wide", page_title="Cyber Trener")

# --- SINGLETONY (Zasoby ładowane raz) ---
@st.cache_resource
def get_manager():
    return CameraManager()

@st.cache_resource
def get_pose_detector():
    # Inicjalizacja detektora MediaPipe
    return PoseDetector(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

@st.cache_resource
def get_visualizer():
    # Klasa odpowiedzialna za rysowanie po klatkach
    return Visualizer()

# Inicjalizacja obiektów
manager = get_manager()
pose_detector = get_pose_detector()
visualizer = get_visualizer()

# --- STATE (Stan sesji) ---
if 'devices' not in st.session_state:
    st.session_state['devices'] = manager.passive_scan()
if 'last_scan' not in st.session_state:
    st.session_state['last_scan'] = "Nigdy"
if 'shown_errors' not in st.session_state:
    st.session_state['shown_errors'] = set()

# --- UI ASSEMBLY (Budowanie interfejsu) ---
# Ważne: Kolejność wywołań tutaj definiuje układ strony.
render_sidebar()
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

# --- GŁÓWNA PĘTLA APLIKACJI ---
try:
    # Zmienne tymczasowe (mock) do czasu implementacji logiki ćwiczeń
    reps_count = 0
    current_exercise = "Squat"
    is_bad_form = False 

    while True:
        if camera_active:
            # 1. POBRANIE KLATKI
            # Resize 640px optymalizuje wydajność detekcji AI
            frame_f = manager.get_frame('front', resize_width=640)
            status_f = manager.get_status('front')

            # 2. PRZETWARZANIE AI & WIZUALIZACJA (Tylko na kamerze Front)
            if frame_f is not None and pose_detector is not None:
                # Detekcja punktów ciała
                landmarks = pose_detector.detect(frame_f)
                
                # Rysowanie szkieletu
                # Parametr has_error steruje kolorem (zielony/czerwony)
                visualizer.draw_skeleton(frame_f, landmarks, has_error=is_bad_form)
                
                # Panel informacyjny (Licznik)
                # Zakomentowane na życzenie - odkomentuj, aby widzieć panel "REPS"
                # visualizer.draw_panel(frame_f, reps_count, current_exercise, errors=[])

            # 3. DRUGA KAMERA (Boczna)
            if single_mode:
                # W trybie jednej kamery kopiujemy obraz na drugi widok
                frame_s = frame_f.copy() if frame_f is not None else None
                status_s = status_f
            else:
                frame_s = manager.get_frame('side', resize_width=640)
                status_s = manager.get_status('side')

            # 4. WYŚWIETLANIE (Render do Streamlit)
            display_frame(ph_front, frame_f, status_f)
            display_frame(ph_side, frame_s, status_s)
            
            # Krótki sleep tylko gdy brak obrazu
            if frame_f is None and frame_s is None:
                time.sleep(0.1)
        else:
            # Sleep gdy system wyłączony przyciskiem
            time.sleep(0.5)

except Exception as e:
    ph_msg.error(f"Pętla przerwana: {e}")
    # Bezpieczne zwolnienie zasobów w razie crasha
    if pose_detector:
        pose_detector.close()