# pip install SpeechRecognition
# pip install PyAudio # Wymagane do nagrywania mikrofonu
# pip install librosa
# pip install gTTS
# pip install playsound


import speech_recognition as sr
import asyncio
import edge_tts
from pygame import mixer  # Load the popular external library


def nasluchuj_komende():
    """
    Nasłuchuje komendy głosowej z mikrofonu i zwraca rozpoznany tekst.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        # Ustawienie wrażliwości na hałas otoczenia
        r.adjust_for_ambient_noise(source, duration=5)

        try:
            print("System nasłuchuje... Mów teraz:")
            audio = r.listen(source)
            print("Rozpoznaję komendę...")


            komenda = r.recognize_google(audio, language="pl-PL")
            print(f"Rozpoznano: '{komenda}'")
            return komenda.lower()

        except sr.UnknownValueError:
            print("Nie rozumiem mowy.")
            return None
        except sr.RequestError:
            print("Brak połączenia z Internetem lub problem z API.")
            return None


def klasyfikuj_tekstowa(tekst):
    """
    Prosta klasyfikacja komendy na podstawie słów kluczowych.
    """
    if tekst is None:
        return "ERROR"

    if "zacznij serię" in tekst or "rozpocznij trening" in tekst:
        return "START_SERIES"
    elif "stop" in tekst or "zatrzymaj" in tekst or "koniec" in tekst:
        return "STOP_SERIES"
    elif "ile" in tekst and ("powtórzeń" in tekst or "błędów" in tekst):
        return "QUERY_STATUS"
    else:
        return "UNKNOWN_COMMAND"

async def speach(text):
    tts = edge_tts.Communicate(text, "pl-PL-MarekNeural")
    await tts.save("test.mp3")

    mixer.init()
    mixer.music.load('test.mp3')
    mixer.music.play()


# --- Główny Program ---
print("--- TEST ROZPOZNAWANIA I KLASYFIKACJI KOMEND ---")
komenda_tekstowa = nasluchuj_komende()

if komenda_tekstowa:
    wynik_klasyfikacji = klasyfikuj_tekstowa(komenda_tekstowa)
    print(f"\nKLASYFIKACJA SYSTEMU: {wynik_klasyfikacji}")

    if wynik_klasyfikacji == "START_SERIES":
        print("Akcja: System rozpoczyna monitorowanie serii ćwiczeń.")
        asyncio.run(speach("Poczatek wykonywania ćwiczenia"))
    elif wynik_klasyfikacji == "STOP_SERIES":
        print("Akcja: System zatrzymuje bieżącą serię i wyświetla podsumowanie.")
        asyncio.run(speach("Koniec wykonywania ćwiczenia"))
    elif wynik_klasyfikacji == "QUERY_STATUS":
        print("Akcja: System odpowiada na pytanie o status.")
        asyncio.run(speach("Zrobileś 10 potórzeń"))
    else:
        print("Akcja: Oczekuję na ponowną komendę.")
        asyncio.run(speach("Nie rozpoznało komendy"))