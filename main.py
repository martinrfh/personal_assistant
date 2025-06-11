import speech_recognition as sr
from modules.weather import get_weather
from modules.TelegramMusicUploader import main as upload_music
from datetime import datetime
import pyttsx3
import asyncio


def greet():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


def speak(text):
    print(f"Assistant: {text}")
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Speech output not supported in Colab.{e}")


def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        query = recognizer.recognize_google(audio)
        print(f"You said: {query}")
        return query
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return ""


def assistant():
    greet_text = greet()
    speak(f"{greet_text}, sir! How can I assist you today?")

    while True:
        command = listen()
        if "exit" in command or "quit" in command:
            speak("Goodbye!")
            break
        if "weather" in command:
            day = next((word for word in command.lower().split()
                       if word in ["today", "tomorrow"]), None)
            if day:
                weather_info = get_weather(day)
                for info, value in weather_info.items():
                    speak(f"The {info} is {value}")
            else:
                speak("Invalid target time. Use 'today' or 'tomorrow'.")
        if "telegram channel" in command:
            asyncio.run(upload_music())


if __name__ == "__main__":
    assistant()
