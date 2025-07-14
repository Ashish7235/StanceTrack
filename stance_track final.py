import tkinter as tk
from tkinter import messagebox
from threading import Thread
from PIL import Image, ImageTk
import cv2
import mediapipe as mp
import math
import random
import os
import pyttsx3
from playsound import playsound
from datetime import datetime
import csv
from fpdf import FPDF

class PostureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STANCE TRACK - Posture Detection")
        self.root.configure(bg="#f0f0f0")

        os.makedirs("snapshots", exist_ok=True)

        try:
            logo_image = Image.open("stance_track_logo.png")
            logo_image = logo_image.resize((150, 150))
            self.logo = ImageTk.PhotoImage(logo_image)
            self.logo_label = tk.Label(root, image=self.logo, bg="#f0f0f0")
            self.logo_label.pack(pady=5)
        except Exception as e:
            messagebox.showwarning("Logo Missing", "Could not load logo image: stance_track_logo.png")

        header = tk.Label(root, text="STANCE TRACK", font=("Helvetica", 22, "bold"), fg="#333", bg="#f0f0f0")
        header.pack(pady=5)

        self.video_frame = tk.Label(root)
        self.video_frame.pack()

        self.status_label = tk.Label(root, text="Status: Not started", font=("Helvetica", 14, "bold"), fg="blue", bg="#f0f0f0")
        self.status_label.pack(pady=5)

        self.tip_label = tk.Label(root, text="", font=("Arial", 12, "italic"), fg="#555", bg="#f0f0f0")
        self.tip_label.pack(pady=5)

        self.score_label = tk.Label(root, text="Score: 0", font=("Arial", 12), fg="black", bg="#f0f0f0")
        self.score_label.pack(pady=5)

        self.stats_label = tk.Label(root, text="Good: 0 | Bad: 0", font=("Arial", 12), bg="#f0f0f0")
        self.stats_label.pack(pady=5)

        self.good_posture_img = tk.Label(root, text="Good Posture", bg="#d0f0c0", width=150, height=150)
        self.good_posture_img.pack(pady=5)

        self.bad_posture_img = tk.Label(root, text="Bad Posture", bg="#f0c0c0", width=150, height=150)
        self.bad_posture_img.pack(pady=5)

        self.start_button = tk.Button(root, text="Start Detection", command=self.start_detection)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.pause_button = tk.Button(root, text="Pause/Resume", command=self.toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_button = tk.Button(root, text="Stop Detection", command=self.stop_detection)
        self.stop_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.running = False
        self.paused = False
        self.alert_playing = False
        self.score = 0

        self.suggestions = [
            "Sit up straight!",
            "Align your back with the chair.",
            "Keep your head level.",
            "Avoid slouching!",
            "Roll your shoulders back.",
            "Keep your neck tall and aligned.",
            "Straighten your spine!",
            "Balance your weight evenly."
        ]

        self.quotes = [
            "Posture is a reflection of your mindset.",
            "Stand tall, feel confident.",
            "Good posture = Good energy.",
            "Your spine deserves better!",
            "A straight back leads to a strong day."
        ]

    def update_posture_frame(self, image, is_good=True):
        img = Image.fromarray(image)
        img = img.resize((150, 150))
        imgtk = ImageTk.PhotoImage(image=img)
        if is_good:
            self.good_posture_img.config(image=imgtk)
            self.good_posture_img.image = imgtk
        else:
            self.bad_posture_img.config(image=imgtk)
            self.bad_posture_img.image = imgtk

    def start_detection(self):
        self.running = True
        self.paused = False
        self.score = 0
        self.status_label.config(text="Status: Detection Started ✅", fg="green")
        self.thread = Thread(target=self.detect_posture)
        self.thread.start()

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.status_label.config(text="Status: Paused ⏸️", fg="blue")
        else:
            self.status_label.config(text="Status: Resumed ▶️", fg="green")

    def stop_detection(self):
        self.running = False
        self.alert_playing = False
        self.status_label.config(text="Status: Detection Stopped ❌", fg="red")
        self.tip_label.config(text="")
        if hasattr(self, 'good_frames') and hasattr(self, 'bad_frames'):
            self.save_log()
            try:
                self.generate_pdf_report()
                messagebox.showinfo("Session Summary", f"Good Posture Frames: {self.good_frames}\nBad Posture Frames: {self.bad_frames}\nPosture Score: {self.score}\nPDF Report saved as posture_report.pdf")
            except Exception as e:
                messagebox.showerror("PDF Error", f"Could not generate PDF report. Error: {e}")

    def play_alert(self):
        if not self.alert_playing and os.path.exists('alert.mp3'):
            self.alert_playing = True
            try:
                playsound('alert.mp3')
            except Exception as e:
                print(f"Sound alert failed: {e}")
            self.alert_playing = False

    def speak_alert(self, message):
        try:
            engine = pyttsx3.init()
            engine.say(message)
            engine.runAndWait()
        except Exception as e:
            print(f"Text-to-speech failed: {e}")

    def save_log(self):
        with open("posture_log.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.good_frames, self.bad_frames, self.score])

    def take_snapshot(self, image):
        try:
            filename = datetime.now().strftime("snapshots/bad_posture_%Y%m%d_%H%M%S.png")
            snapshot = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, snapshot)
        except Exception as e:
            print(f"Snapshot failed: {e}")

    def generate_pdf_report(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="Posture Session Report", ln=True, align='C')

        pdf.set_font("Arial", size=12)
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(200, 10, txt=f"Good Posture Frames: {self.good_frames}", ln=True)
        pdf.cell(200, 10, txt=f"Bad Posture Frames: {self.bad_frames}", ln=True)
        pdf.cell(200, 10, txt=f"Posture Score: {self.score}", ln=True)

        pdf.output("posture_report.pdf")

    def detect_posture(self):
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6)
        mp_drawing = mp.solutions.drawing_utils
        cap = cv2.VideoCapture(0)

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        good_frames = 0
        bad_frames = 0

        def find_distance(x1, y1, x2, y2):
            return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        def find_angle(x1, y1, x2, y2, x3, y3):
            a = find_distance(x2, y2, x3, y3)
            b = find_distance(x1, y1, x3, y3)
            c = find_distance(x1, y1, x2, y2)
            return math.degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))

        while self.running and cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            if results.pose_landmarks:
                if self.paused:
                    continue

                landmarks = results.pose_landmarks.landmark
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR]
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]

                l_shldr_x, l_shldr_y = int(left_shoulder.x * width), int(left_shoulder.y * height)
                l_ear_x, l_ear_y = int(left_ear.x * width), int(left_ear.y * height)
                l_hip_x, l_hip_y = int(left_hip.x * width), int(left_hip.y * height)

                neck_angle = find_angle(l_shldr_x, l_shldr_y, l_ear_x, l_ear_y, l_shldr_x, 0)
                torso_angle = find_angle(l_hip_x, l_hip_y, l_shldr_x, l_shldr_y, l_hip_x, 0)

                if neck_angle > 40 or torso_angle > 10:
                    bad_frames += 1
                    good_frames = 0
                    self.status_label.config(text="Status: Bad Posture 😟", fg="red")
                    suggestion = random.choice(self.suggestions)
                    self.tip_label.config(text=f"💡 {suggestion}")
                    self.speak_alert(suggestion)
                    Thread(target=self.play_alert).start()
                    self.take_snapshot(image)
                    self.update_posture_frame(image, is_good=False)
                    self.score -= 2
                else:
                    good_frames += 1
                    bad_frames = 0
                    self.status_label.config(text="Status: Good Posture 😊", fg="green")
                    quote = random.choice(self.quotes)
                    self.tip_label.config(text=f"✅ {quote}")
                    self.update_posture_frame(image, is_good=True)
                    self.score += 1

                self.stats_label.config(text=f"Good: {good_frames} | Bad: {bad_frames}")
                self.score_label.config(text=f"Score: {self.score}")
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            img = Image.fromarray(image)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_frame.imgtk = imgtk
            self.video_frame.config(image=imgtk)

            self.good_frames = good_frames
            self.bad_frames = bad_frames

        cap.release()

if __name__ == "__main__":
    root = tk.Tk()
    app = PostureApp(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_detection)
    root.mainloop()
