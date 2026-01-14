# CyberTrener

## Installation 

1. Clone the repo.
2. In the project folder, create virtual environment ```python -m venv venv```
3. Activate the environment   
Windows ```venv\Scripts\activate```   
Linux ```source venv/bin/activate```
4. Install required libraries ```pip install -r requirements.txt```
5. Run the main app.

## Notes for collaborators
When creating branches, name them accordingly (feat, fix, ui) and specify which issue you are referring (e.g. feat-1-core-logic, ui-3-chat-implementation).   
You can also refer to issues in your commit messages (git commit -m "feat (#2): implemented something") - in this case it links this commit to issue #2.

## Planned structure of the project 

```
CyberTrener/
├── media/                     # Assets for testing and debugging
│   └── test_videos/           # MP4 files (Bicep curl, plank) for logic verification (Pre-Streamlit phase)
│
├── src/                       # Main source code directory
│   ├── audio/                 # Voice Interaction Module
│   │   ├── listener.py        # Background thread for Speech Recognition (Voice Commands)
│   │   └── speaker.py         # Text-to-Speech (TTS) engine for audio feedback
│   │
│   ├── exercises/             # Logic & Exercise Rules
│   │   ├── base.py            # Abstract Base Class: State Machine (Waiting/Down/Up) & Counters
│   │   ├── plank.py           
│   │   ├── sit_ups.py         
│   │   ├── bicep_curl.py      
│   │   ├── jumping_jack.py    
│   │   └── ohp.py             
│   │
│   ├── processor/             # Core Engine
│   │   ├── camera.py          # Multi-threaded webcam capture (prevents UI lag)
│   │   └── pose.py            # MediaPipe Pose wrapper for landmark extraction
│   │
│   ├── ui/                    # User Interface Components
│   │   ├── dashboard.py       # Streamlit layout helpers
│   │   └── visualizer.py      # OpenCV drawing tools (Skeleton overlay)
│   │
│   └── utils/                 # General Helper Functions
│       ├── geometry.py        # Math: Angle calculations (2D/3D), Distances
│       └── smoothing.py       # Data: Signal filtering to reduce landmark jitter
│
├── tests/                     # Unit Tests
│   ├── test_geometry.py       # Testing angle calculations
│   └── test_exercises.py      # Testing logic against mock data/videos
│
├── main.py                    # Main app - runs the Streamlit application
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```
