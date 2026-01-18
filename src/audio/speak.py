# Source - https://stackoverflow.com/a
# Posted by Sachin Hosmani
# Retrieved 2026-01-18, License - CC BY-SA 4.0

import sys
import pyttsx3

def init_engine():
    engine = pyttsx3.init()
    return engine

def say(s):
    engine.say(s)
    engine.runAndWait()  # Blocks

if __name__ == "__main__":
    engine = init_engine()
    say(str(sys.argv[1]))

