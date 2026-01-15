import streamlit as st
# Import funkcji z modułu ui/layout.py
from src.ui.dashboard import render_sidebar, render_main_layout

# Konfiguracja strony
st.set_page_config(
    page_title="Cyber Trener",
    layout="wide",  # Pozwala zmieścić dwie kamery obok siebie
    initial_sidebar_state="expanded" 
)

def init_session_state():
    """
    Inicjalizuje zmienne stanu potrzebne dla logiki.
    """
    if 'reps' not in st.session_state:
        st.session_state['reps'] = 0
    if 'current_exercise' not in st.session_state:
        st.session_state['current_exercise'] = None
    if 'voice_command' not in st.session_state:
        st.session_state['voice_command'] = ""
    if 'errors' not in st.session_state:
        st.session_state['errors'] = []
    if 'voice_enabled' not in st.session_state:
        st.session_state['voice_enabled'] = True
    if 'tts_enabled' not in st.session_state:
        st.session_state['tts_enabled'] = True


init_session_state()

# Panel boczny
render_sidebar()
    
# 2. Główny dashboard (dwie kolumny)
# Dwie kamery placeholdery
ph_front, ph_side, ph_msg = render_main_layout()