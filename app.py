import asyncio
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from PIL.Image import Resampling
import cv2 as cv
import mediapipe as mp
import pyautogui as pg
from pywizlight import wizlight, PilotBuilder, discovery
import subprocess
import RPi.GPIO as GPIO
import time

LED_PIN = 21  

GPIO.setmode(GPIO.BCM)  # Use BCM numbering
GPIO.setup(LED_PIN, GPIO.OUT) 


light=None
async def initialize_bulbs():
    bulbs = await discovery.discover_lights(broadcast_space="192.168.1.255")
    if not bulbs:
        print("No bulbs found.")
        return None

    light = wizlight(bulbs[0].ip)
    print(f"Connected to bulb at IP: {bulbs[0].ip}")
    return light
light=asyncio.run(initialize_bulbs())

def run_wizlight_command(ip):
    
    command = ["wizlight", "on", "--ip", ip, "--k", str(3000), "--brightness", str(128)]

    try:
        # Run the command and capture the output
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except FileNotFoundError:
        return "Error: 'wizlight' command not found. Make sure it is installed and available in your PATH."

def stop_wizlight_command(ip):
    
    command = ["wizlight", "off", "--ip", ip]

    try:
        # Run the command and capture the output
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except FileNotFoundError:
        return "Error: 'wizlight' command not found. Make sure it is installed and available in your PATH."

# # Example usage
# if __name__ == "__main__":
#     ip = "192.168.0.101"
#     kelvin = 3000
#     brightness = 128

#     output = run_wizlight_command(ip, kelvin, brightness)
#     print(output)
pg.FAILSAFE = False

# Function to handle button toggle
def toggle_button(button, state, label):
    if state[0] == "OFF":
        button.config(bg="green")
        state[0] = "ON"
        run_wizlight_command(light.ip)
        
    else:
        button.config(bg="red")
        state[0] = "OFF"
        stop_wizlight_command(light.ip)

def toggle_button_2(button, state, label):
    if state[0] == "OFF":
        button.config(bg="green")
        state[0] = "ON"
        GPIO.output(LED_PIN, GPIO.HIGH)
        
    else:
        button.config(bg="red")
        state[0] = "OFF"
        GPIO.output(LED_PIN, GPIO.LOW)

# Tkinter window setup
root = tk.Tk()
root.title("Control Panel with Face Detection")
root.geometry("600x400")

# Background Image
bg_image = Image.open("images.jpeg").resize((600, 400), Resampling.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)
bg_label = tk.Label(root, image=bg_photo)
bg_label.place(relwidth=1, relheight=1)

# Load button images
fan_logo_image = Image.open("fan.png").resize((50, 50), Resampling.LANCZOS)
fan_logo = ImageTk.PhotoImage(fan_logo_image)

light_logo_image = Image.open("light.png").resize((50, 50), Resampling.LANCZOS)
light_logo = ImageTk.PhotoImage(light_logo_image)

# Button states
states = {"FAN": ["OFF"], "LIGHT 1": ["OFF"], "LIGHT 2": ["OFF"]}

# Header (Control Panel Title)
label = tk.Label(
    root,
    text="Control Panel",
    font=("Arial", 20, "bold"),
    bg="#333333",
    fg="white"
)
label.place(relx=0.5, rely=0.1, anchor="center")

# Create button frame
button_frame = tk.Frame(root)
button_frame.place(relx=0.5, rely=0.5, anchor="center")

# FAN Button
fan_button = tk.Button(
    button_frame,
    image=fan_logo,
    bg="red",
    bd=0,
    highlightthickness=0,
    activebackground="lightgray",
    width=100,
    height=80,
    command=lambda: toggle_button(fan_button, states["FAN"], "FAN"),
)
fan_button.grid(row=0, column=0, padx=10)

# LIGHT 1 Button
light1_button = tk.Button(
    button_frame,
    image=light_logo,
    bg="red",
    bd=0,
    highlightthickness=0,
    activebackground="lightgray",
    width=100,
    height=80,
    command=lambda: toggle_button(light1_button, states["LIGHT 1"], "LIGHT 1"),
)
light1_button.grid(row=0, column=1, padx=10)

# LIGHT 2 Button
light2_button = tk.Button(
    button_frame,
    image=light_logo,
    bg="red",
    bd=0,
    highlightthickness=0,
    activebackground="lightgray",
    width=100,
    height=80,
    command=lambda: toggle_button_2(light2_button, states["LIGHT 2"], "LIGHT 2"),
)
light2_button.grid(row=0, column=2, padx=10)

# Small labels for button numbers
tk.Label(button_frame, text="1", font=("Arial", 12, "bold"), fg="white", bg="#333333").grid(row=1, column=1)
tk.Label(button_frame, text="2", font=("Arial", 12, "bold"), fg="white", bg="#333333").grid(row=1, column=2)

# Start the Tkinter window in a separate thread
root.update_idletasks()
root.update()

# Eye-tracking and face detection setup
cap = cv.VideoCapture(1)
success, img = cap.read()
height, width, _ = img.shape
scw, sch = pg.size()
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
mp_face_detection = mp.solutions.face_detection.FaceDetection(min_detection_confidence=0.5)

while success:
    success, img = cap.read()
    img = cv.flip(img, 1)
    rgb_frame = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    op = face_mesh.process(rgb_frame)
    landmark_points = op.multi_face_landmarks

    if landmark_points:
        landmarks = landmark_points[0].landmark
        for id, landmark in enumerate(landmarks[474:478]):
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            cv.circle(img, (x, y), 3, (128, 0, 128))

            # Move mouse cursor
            if id == 1:
                screen_x = scw / width * x
                screen_y = sch / height * y
                pg.moveTo(screen_x, screen_y)

        left_eye = [landmarks[145], landmarks[159]]
        for landmark in left_eye:
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            cv.circle(img, (x, y), 3, (255, 255, 0))

        if (left_eye[0].y - left_eye[1].y) < 0.01:
            pg.click()
            print('Click detected')
            pg.sleep(1)

        cv.putText(img, "Algorithm In Work", (20, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    else:
        cv.putText(img, "Algorithm Not In Work", (20, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # cv.imshow("Eye Tracker", img)
    root.update_idletasks()
    root.update()

    if cv.waitKey(10) & 0xFF == 27:  # Escape to exit
        break

cap.release()
cv.destroyAllWindows()
root.destroy()
