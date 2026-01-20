import streamlit as st
import numpy as np

def render_sidebar():
    """
    Renderuje panel boczny z pełnym zestawem kontrolek dla przyszłych modułów.
    """
    with st.sidebar:
        st.title("⚙️ Panel Sterowania")
        
        # --- Konfiguracja Wideo ---
        st.header("1. Wideo")
        with st.expander("Ustawienia Kamer", expanded=True):
            st.text_input("ID Kamery Przedniej", value="0", key="cam_front", help="Dla widoku z przodu")
            st.text_input("ID Kamery Bocznej", value="1", key="cam_side", help="Dla analizy kręgosłupa")
            st.checkbox("Tryb niskiej wydajności (Resize)", value=False, key="low_perf_mode")

        # --- Trening ---
        st.header("2. Trening")
        # Lista ćwiczeń z nowej listy issues
        exercise_options = [
            "Wybierz ćwiczenie...",
            "Bicep Curl (Issue 7)",
            "Plank (Issue 5)",
            "Sit-ups (Issue 6)",
            "Overhead Press (Issue 8/9)"
        ]
        # Selectbox pozwala na ręcznie zmienianie logiki
        selected_exercise = st.selectbox(
            "Aktualne ćwiczenie", 
            options=exercise_options,
            key="manual_exercise_select"
        )
        
        # Konsola logów głosowych
        st.text_area("Log komend głosowych", value="Oczekiwanie...", height=70, disabled=True, key="voice_log")

        st.markdown("---")
        
        # --- Przyciski Sterujące ---
        col_start, col_stop = st.columns(2)
        with col_start:
            st.button("START", type="primary", use_container_width=True)
        with col_stop:
            st.button("STOP", type="secondary", use_container_width=True)

def render_stats_panel():
    """
    Wyświetla pasek statystyk nad wideo (Reps, Errors, State).
    """
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Powtórzenia", "0", help="Poprawne powtórzenia")
        c2.metric("Błędy", "0", delta_color="inverse", help="Wykryte błędy techniczne")
        c3.metric("Faza", "CZEKAM", help="Eccentric / Concentric / Isometric")
        c4.metric("Jakość", "100%", help="Ocena techniki")

def render_main_layout():
    """
    Renderuje główny dashboard z wideo i komunikatami zwrotnymi.
    Zwraca: (placeholder_front, placeholder_side, placeholder_feedback)
    """
    st.title("Cyber Trener")
    
    # Statystyki
    render_stats_panel()
    
    st.markdown("---")

    # 2. Układ 2-kolumnowy Wideo
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 Przód (Front)")
        placeholder_front = st.empty()
        placeholder_front.image(
            np.zeros((480, 640, 3), dtype=np.uint8), 
            caption="Oczekiwanie na kamerę...", channels="RGB", use_container_width=True
        )

    with col2:
        st.subheader("📷 Bok (Side)")
        placeholder_side = st.empty()
        placeholder_side.image(
            np.zeros((480, 640, 3), dtype=np.uint8), 
            caption="Oczekiwanie na kamerę...", channels="RGB", use_container_width=True
        )

    # Panel Komunikacji z Użytkownikiem
    st.markdown("### 📢 Komunikaty Trenera (Testowanie działania glosu)")
    placeholder_feedback = st.empty()
    placeholder_feedback.info("System gotowy. Powiedz 'Start', aby rozpocząć.")

    return placeholder_front, placeholder_side, placeholder_feedback
