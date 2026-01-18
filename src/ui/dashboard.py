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
    Zwraca tuple z wyborem użytkownika: (czy_aktywne, id_przod, id_bok).
    """
    st.sidebar.subheader("🎥 Panel Sterowania Kamerami")

    # 1. Przycisk Skanowania / Resetu
    # Wymusza odświeżenie listy urządzeń (Cross-Platform).
    if st.sidebar.button("🔄 Skanuj i Resetuj"):
        st.session_state['devices'] = manager.passive_scan()
        st.session_state['last_scan'] = datetime.datetime.now().strftime("%H:%M:%S")
        st.session_state['shown_errors'] = set() # Reset powiadomień
        st.rerun()

    st.sidebar.caption(f"Ostatni skan: {st.session_state.get('last_scan', 'Nigdy')}")

    # 2. Lista dostępnych urządzeń
    devices = st.session_state.get('devices', [])
    options = {d: f"Kamera {d}" for d in devices}
    
    if not options:
        st.sidebar.error("⚠️ Nie wykryto kamer!")
        options[0] = "Force ID 0"
    
    sorted_ids = sorted(list(options.keys()))

    # Wybór Kamery Przedniej
    sel_front = st.sidebar.selectbox(
        "Kamera Przednia (Front):", sorted_ids, 
        format_func=lambda x: options.get(x, str(x)), index=0, key='sf'
    )
    
    # Wybór Kamery Bocznej (Inteligentny wybór domyślny)
    def_side = len(sorted_ids) - 1 if len(sorted_ids) > 0 else 0
    sel_side = st.sidebar.selectbox(
        "Kamera Boczna (Side):", sorted_ids,
        format_func=lambda x: options.get(x, str(x)), index=def_side, key='ss'
    )

    st.sidebar.markdown("---")

    # 3. Główny włącznik
    # Domyślnie TRUE, aby system wstawał automatycznie po restarcie/skanowaniu.
    active = st.sidebar.toggle("🟢 Aktywuj System Wideo", value=True)
    
    return active, sel_front, sel_side

def render_video_layout():
    """Przygotowuje układ strony (kolumny) i zwraca puste kontenery na wideo."""
    st.title("Cyber Trener")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📷 Przód (Front)")
        ph_front = st.empty()
        
    with col2:
        st.markdown("### 📹 Bok (Side)")
        ph_side = st.empty()
        
    ph_msg = st.empty() # Placeholder na krytyczne błędy
    
    return ph_front, ph_side, ph_msg

def display_frame(placeholder, frame, label, error_msg=None):
    """
    Wyświetla klatkę wideo w interfejsie Streamlit.
    Zawiera obsługę błędów (Graceful Degradation) - pokazuje czarny ekran zamiast crasha.
    """
    if frame is not None:
        # Nakładanie tekstu (Label)
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Konwersja BGR (OpenCV) -> RGB (Streamlit)
        disp = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # [RESPONSIVENESS] width="stretch" dopasowuje obraz do szerokości okna
        placeholder.image(disp, channels="RGB", width="stretch")
        
        # Usunięcie błędu z historii, jeśli obraz powrócił
        if 'shown_errors' in st.session_state and label in st.session_state['shown_errors']:
            st.session_state['shown_errors'].remove(label)
            
    elif error_msg:
        # Renderowanie ekranu błędu
        blk = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(blk, "NO SIGNAL", (200, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(blk, "Sprawdz kamere", (210, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        placeholder.image(blk, channels="RGB", width="stretch")
        
        # Wyświetlenie powiadomienia (Toast) tylko raz na sesję
        if 'shown_errors' in st.session_state and label not in st.session_state['shown_errors']:
            st.toast(f"Błąd {label}: {error_msg}", icon="⚠️")
            st.session_state['shown_errors'].add(label)