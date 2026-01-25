import streamlit as st
import cv2
import datetime
import numpy as np

"""
Moduł Dashboard: Odpowiada wyłącznie za wygląd aplikacji (UI).
Nie zawiera logiki biznesowej ani obsługi sprzętu.
"""

def render_sidebar():
    """Renderuje logo i nagłówek panelu bocznego."""
    st.sidebar.title("Cyber Trener")
    st.sidebar.markdown("---")

def render_camera_controls(manager):
    """
    Renderuje panel sterowania kamerami.
    Zwraca: (czy_aktywne, id_przod, id_bok).
    """
    st.sidebar.subheader("Panel Sterowania Kamerami")

    # Przycisk wymuszający ponowne skanowanie urządzeń
    if st.sidebar.button("Skanuj i Resetuj"):
        st.session_state['devices'] = manager.passive_scan()
        st.session_state['last_scan'] = datetime.datetime.now().strftime("%H:%M:%S")
        st.session_state['shown_errors'] = set()
        st.rerun()

    st.sidebar.caption(f"Ostatni skan: {st.session_state.get('last_scan', 'Nigdy')}")

    # Dynamiczna lista urządzeń z sesji
    devices = st.session_state.get('devices', [])
    options = {d: f"Kamera {d}" for d in devices}
    
    if not options:
        st.sidebar.error("Nie wykryto kamer!")
        options[0] = "Force ID 0"
    
    sorted_ids = sorted(list(options.keys()))

    # Selectbox: Wybór Kamery Przedniej
    sel_front = st.sidebar.selectbox(
        "Kamera Przednia (Front):", sorted_ids, 
        format_func=lambda x: options.get(x, str(x)), index=0, key='sf'
    )
    
    # Selectbox: Wybór Kamery Bocznej
    def_side = len(sorted_ids) - 1 if len(sorted_ids) > 0 else 0
    sel_side = st.sidebar.selectbox(
        "Kamera Boczna (Side):", sorted_ids,
        format_func=lambda x: options.get(x, str(x)), index=def_side, key='ss'
    )

    st.sidebar.markdown("---")

    # Główny przełącznik systemu
    active = st.sidebar.toggle("Aktywuj System Wideo", value=True)
    return active, sel_front, sel_side

def render_video_layout():
    """
    Przygotowuje układ strony (kolumny wideo).
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Przod (Front)")
        ph_front = st.empty()
        
    with col2:
        st.markdown("### Bok (Side)")
        ph_side = st.empty()
        
    ph_msg = st.empty() # Placeholder na komunikaty o błędach
    
    return ph_front, ph_side, ph_msg

def display_frame(placeholder, frame, status_msg=None):
    """
    Wyświetla pojedynczą klatkę wideo.
    """
    if frame is not None:
        disp = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        placeholder.image(disp, channels="RGB", width=400)
            
    elif status_msg:
        blk = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(blk, "NO SIGNAL", (200, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        placeholder.image(blk, channels="RGB", width=400)