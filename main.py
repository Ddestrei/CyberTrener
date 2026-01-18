import streamlit as st
import time

# Importy wewnętrzne
from src.processor.camera import CameraManager
from src.ui.dashboard import (
    render_sidebar, 
    render_camera_controls, 
    render_video_layout, 
    display_frame
)

# --- KONFIGURACJA STRONY ---
st.set_page_config(layout="wide", page_title="Cyber Trener")

# --- SINGLETON CAMERA MANAGER ---
# Używamy cache_resource, aby Manager był tworzony tylko raz
# i nie resetował połączenia z kamerami przy każdym kliknięciu w UI.
@st.cache_resource
def get_manager():
    return CameraManager()

manager = get_manager()

# --- STAN SESJI (SESSION STATE) ---
# Inicjalizacja zmiennych przechowujących stan między przeładowaniami.
if 'devices' not in st.session_state:
    st.session_state['devices'] = manager.passive_scan()
if 'last_scan' not in st.session_state:
    st.session_state['last_scan'] = "Nigdy"
if 'shown_errors' not in st.session_state:
    st.session_state['shown_errors'] = set()

# --- BUDOWANIE INTERFEJSU (UI ASSEMBLY) ---
# 1. Nagłówek panelu bocznego
render_sidebar()

# 2. Kontrolki sterowania (zwracają wybór użytkownika)
camera_active, sel_front, sel_side = render_camera_controls(manager)

# 3. Przygotowanie miejsca na wideo
ph_front, ph_side, ph_msg = render_video_layout()

# --- LOGIKA STEROWANIA SPRZĘTEM ---
single_mode = (sel_front == sel_side)

if camera_active:
    try:
        # Uruchomienie kamery przedniej
        manager.start_camera('front', sel_front)
        
        if not single_mode:
            # Tryb Dual-Cam: Uruchomienie drugiej kamery
            manager.start_camera('side', sel_side)
        else:
            # Tryb Mirror (Oszczędność): Zatrzymanie drugiej kamery
            manager.stop_role('side')
            st.sidebar.success("✅ Tryb jednej kamery (Mirror)")
            
    except Exception as e:
        st.error(f"Krytyczny błąd startu: {e}")
else:
    # Zatrzymanie wszystkich wątków wideo
    manager.stop_all()

# --- GŁÓWNA PĘTLA APLIKACJI (RUN LOOP) ---
try:
    while True:
        if camera_active:
            # [OPTIMIZATION] Pobieramy klatki przeskalowane do 480px.
            # Mniejsze obrazy = szybsze przesyłanie przez przeglądarkę = wyższy FPS.
            frame_f = manager.get_frame('front', resize_width=480)
            status_f = manager.get_status('front')

            if single_mode:
                # W trybie Mirror kopiujemy klatkę cyfrowo
                frame_s = frame_f.copy() if frame_f is not None else None
                status_s = status_f
            else:
                frame_s = manager.get_frame('side', resize_width=480)
                status_s = manager.get_status('side')

            # Wyświetlanie (delegowane do dashboard.py)
            display_frame(ph_front, frame_f, f"CAM {sel_front}", status_f)
            display_frame(ph_side, frame_s, f"CAM {sel_side}", status_s)
            
            # Jeśli brak sygnału z obu kamer, czekamy chwilę (oszczędność CPU)
            if frame_f is None and frame_s is None:
                time.sleep(0.1)
        else:
            # Tryb czuwania (Standby)
            time.sleep(0.5)

except Exception as e:
    ph_msg.error(f"Pętla aplikacji przerwana: {e}")