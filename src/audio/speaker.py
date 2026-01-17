import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', '190')

def speak(text):
    engine.say(text)
    engine.runAndWait()