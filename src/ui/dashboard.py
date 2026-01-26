import streamlit as st
import cv2
import datetime
import numpy as np

"""
Dashboard Module: Responsible solely for the UI appearance.
Contains no business logic or hardware handling.
"""

def render_sidebar():
    """Renders the logo and sidebar header."""
    st.sidebar.title("Cyber Trainer")
    st.sidebar.markdown("---")

def render_camera_controls(manager):
    """
    Renders the camera control panel.
    Returns: (is_active, front_id, side_id).
    """
    st.sidebar.subheader("Camera Controls")

    # Button to force device rescan
    if st.sidebar.button("Scan and Reset"):
        st.session_state['devices'] = manager.passive_scan()
        st.session_state['last_scan'] = datetime.datetime.now().strftime("%H:%M:%S")
        st.session_state['shown_errors'] = set()
        st.rerun()

    st.sidebar.caption(f"Last scan: {st.session_state.get('last_scan', 'Never')}")

    # Dynamic device list from session
    devices = st.session_state.get('devices', [])
    options = {d: f"Camera {d}" for d in devices}
    
    if not options:
        st.sidebar.error("No cameras detected!")
        options[0] = "Force ID 0"
    
    sorted_ids = sorted(list(options.keys()))

    # Selectbox: Front Camera
    sel_front = st.sidebar.selectbox(
        "Front Camera:", sorted_ids, 
        format_func=lambda x: options.get(x, str(x)), index=0, key='sf'
    )
    
    # Selectbox: Side Camera
    def_side = len(sorted_ids) - 1 if len(sorted_ids) > 0 else 0
    sel_side = st.sidebar.selectbox(
        "Side Camera:", sorted_ids,
        format_func=lambda x: options.get(x, str(x)), index=def_side, key='ss'
    )

    st.sidebar.markdown("---")

    # Main system toggle
    active = st.sidebar.toggle("Activate Video System", value=True)
    return active, sel_front, sel_side

def render_video_layout():
    """
    Prepares the page layout (video columns).
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Front View")
        ph_front = st.empty()
        
    with col2:
        st.markdown("### Side View")
        ph_side = st.empty()
        
    ph_msg = st.empty() # Placeholder for error messages
    
    return ph_front, ph_side, ph_msg

def display_frame(placeholder, frame, status_msg=None):
    """
    Displays a single video frame.
    [FIX] Updated to width="stretch" to stop Streamlit warnings.
    """
    if frame is not None:
        # Convert BGR (OpenCV) to RGB (Streamlit)
        disp = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        placeholder.image(disp, channels="RGB", width="stretch")
            
    elif status_msg:
        # Display error message on a black background
        blk = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(blk, str(status_msg), (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        placeholder.image(blk, channels="RGB", width="stretch")
    
    # Implicit return None
    return