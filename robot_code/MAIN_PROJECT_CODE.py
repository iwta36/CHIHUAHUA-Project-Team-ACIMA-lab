# -*- coding: utf-8 -*-
"""
Raspberry Pi Final Integrated Control Script - WaveGo Robot & Medical Companion
Includes Voice Alert on Fall Detection, Terminal Reminders & High FPS Camera Loop
"""

import os
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import sys
import cv2
import time
import json
import wave
import math
import struct
import serial
import threading
import datetime
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from flask import Flask, Response, request, jsonify
from twilio.rest import Client
from gtts import gTTS
from ultralytics import YOLO
from picamera2 import Picamera2
import pygame

# Αρχικοποίηση Pygame Mixer
try:
    pygame.mixer.init()
    print("[Audio] Το Pygame mixer ξεκίνησε επιτυχώς!", flush=True)
except Exception as e:
    print(f"[Audio Warning] Δεν ήταν δυνατή η εκκίνηση του ήχου: {e}", flush=True)

app = Flask(__name__)

# --- CONFIGURATION ---
TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID_HERE"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN_HERE"
TWILIO_PHONE_NUMBER = "YOUR_TWILIO_PHONE_NUMBER_HERE"

# Ασφαλής Αρχικοποίηση Σειριακής Θύρας (UART) για τον ESP32
ser = None
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.5, write_timeout=0.5)
    time.sleep(1)
    print("[UART] Ο ESP32 συνδέθηκε επιτυχώς!", flush=True)
except Exception as e:
    ser = None
    print(f"[UART Warning] Δεν βρέθηκε ο ESP32 (Συνεχίζουμε σε Safe Mode): {e}", flush=True)

# --- WAVEGO MOTION DRIVER ---
WAVEGO_RPI_DIR = "/home/ratchet66/WAVEGO/RPi"
if WAVEGO_RPI_DIR not in sys.path:
    sys.path.insert(0, WAVEGO_RPI_DIR)

try:
    import robot
    ROBOT_MOTION_READY = True
    print("[ROBOT] WAVEGO motion driver loaded successfully.")
except Exception as e:
    robot = None
    ROBOT_MOTION_READY = False
    print(f"[ROBOT Warning] Motion driver unavailable: {e}")

DEFAULT_MESSAGE = "Ώρα για το χάπι σου!"

caretaker_phone_number = None  
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- GLOBAL STATES ---
output_frame = None
lock = threading.Lock()
fall_detected = False
follow_started = False
alarm_active = False

active_reminder_times = []
reminder_custom_message = DEFAULT_MESSAGE

last_motion_command = None
last_motion_time = 0.0
MOTION_MIN_INTERVAL = 0.15

eridian_dictionary = {
    "time": [523, 659],
    "medicine": [659, 784],
    "now": [784, 1046],
    "χάπι": [659, 784],
    "ώρα": [523, 659],
    "τώρα": [784, 1046]
}

def send_to_esp32(command):
    if ser and ser.is_open:
        try:
            ser.write((command + "\n").encode('utf-8'))
            print(f"[UART] Sent: {command}")
        except Exception as e:
            print(f"[UART Error] Failed to send command: {e}")
    else:
        print(f"[UART Mock] Would send: {command}")

def send_motion(command):
    global last_motion_command, last_motion_time
    now = time.monotonic()
    if command == last_motion_command:  
        return
    if command != "stop" and now - last_motion_time < MOTION_MIN_INTERVAL:
        return

    if not ROBOT_MOTION_READY:
        print(f"[ROBOT MOCK] Would execute: {command}")
        return

    try:
        if command == "forward":
            robot.stopLR()
            robot.forward()
        elif command == "left":
            robot.stopFB()
            robot.left()
        elif command == "right":
            robot.stopFB()
            robot.right()
        elif command == "stop":
            robot.stopFB()
            robot.stopLR()
        last_motion_command = command
        last_motion_time = now
    except Exception as e:
        print(f"[ROBOT Error] {e}")

# --- AUDIO & REMINDERS ---
def format_time_for_speech(time_str):
    try:
        parts = time_str.split(":")
        hours, minutes = int(parts[0]), int(parts[1])
        period = "το πρωί" if 5 <= hours < 12 else ("το μεσημέρι" if 12 <= hours < 17 else ("το απόγευμα" if 17 <= hours < 21 else "το βράδυ"))
        speech_hours = 12 if hours % 12 == 0 else hours % 12
        return f"{speech_hours} {period}" if minutes == 0 else f"{speech_hours} και {minutes} {period}"
    except Exception:
        return time_str

def generate_eridian_audio(message_text, output_file):
    sample_rate = 24000
    duration_per_word = 0.25
    pause_duration = 0.08
    words = message_text.lower().split()
    audio_samples = []
    for word in words:
        freqs = eridian_dictionary.get(word, [523, 659])
        num_samples = int(sample_rate * duration_per_word)
        for i in range(num_samples):
            t = float(i) / sample_rate
            val = (math.sin(2.0 * math.pi * freqs[0] * t) + math.sin(2.0 * math.pi * freqs[1] * t)) / 2.0
            envelope = min(i / 400, (num_samples - i) / 400, 1.0)
            audio_samples.append(int(val * 16384 * envelope))
        audio_samples.extend([0] * int(sample_rate * pause_duration))

    with wave.open(output_file, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for s in audio_samples:
            wav_file.writeframes(struct.pack('<h', s))

def play_sound_file(filepath):
    if not os.path.exists(filepath):
        return
    try:
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"⚠️ Σφάλμα αναπαραγωγής: {e}")

def speak_text(text_message):
    """Εκφωνεί ένα κείμενο στα Ελληνικά χρησιμοποιώντας gTTS"""
    timestamp = int(time.time())
    speech_file = f"/tmp/fall_speech_{timestamp}.mp3"
    try:
        tts = gTTS(text=text_message, lang='el')
        tts.save(speech_file)
        play_sound_file(speech_file)
    except Exception as e:
        print(f"[Audio Error] Σφάλμα φωνητικής ειδοποίησης: {e}")
    finally:
        if os.path.exists(speech_file):
            try: os.remove(speech_file)
            except: pass

def speak_for_one_minute(time_str, message):
    global alarm_active
    full_text = f"Είναι {format_time_for_speech(time_str)}. {message}"
    timestamp = int(time.time())
    eridian_file, speech_file = f"/tmp/eridian_{timestamp}.wav", f"/tmp/speech_{timestamp}.mp3"
    try:
        send_to_esp32(f"ALERT:{message}")
        generate_eridian_audio("time medicine now", eridian_file)
        tts = gTTS(text=full_text, lang='el')
        tts.save(speech_file)
        start_time = time.time()
        while alarm_active and (time.time() - start_time < 60):
            play_sound_file(eridian_file)
            time.sleep(0.2)
            play_sound_file(speech_file)
            time.sleep(0.5)
    finally:
        for f in [eridian_file, speech_file]:
            if os.path.exists(f):
                try: os.remove(f)
                except: pass

def schedule_checker():
    global alarm_active, active_reminder_times, reminder_custom_message
    triggered_time = ""
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        if now in active_reminder_times:
            if triggered_time != now:
                triggered_time = now
                alarm_active = True
                speak_for_one_minute(now, reminder_custom_message)
                alarm_active = False
        else:
            triggered_time = ""
        time.sleep(1)

def handle_fall_event():
    """Ενέργειες όταν εντοπιστεί πτώση: Αποστολή SMS & Φωνητική προειδοποίηση"""
    print("[FALL] Εντοπίστηκε πτώση! Ειδοποίηση...")
    # Φωνητική ειδοποίηση από το ηχείο του ρομπότ
    threading.Thread(target=speak_text, args=("Προσοχή! Εντοπίστηκε πιθανή πτώση ασθενούς!",), daemon=True).start()
    # Αποστολή SMS μέσω Twilio
    notify_fall_with_twilio()

def notify_fall_with_twilio():
    global caretaker_phone_number
    if not caretaker_phone_number:
        print("[Twilio Error] No caretaker phone registered.")
        return
    try:
        message = twilio_client.messages.create(
            body="🚨 ΠΡΟΕΙΔΟΠΟΙΗΣΗ: Το ρομπότ εντόπισε πιθανή πτώση του ασθενή!",
            from_=TWILIO_PHONE_NUMBER,
            to=caretaker_phone_number
        )
        print(f"[Twilio] SMS sent. SID: {message.sid}")
    except Exception as e:
        print(f"[Twilio Error] {e}")

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360.0 - angle if angle > 180.0 else angle

# --- OPTIMIZED CAMERA PROCESSING LOOP ---
def camera_processing_loop():
    global output_frame, fall_detected, follow_started

    print("[AI] Φόρτωση μοντέλου ML πτώσης...")
    MODEL_PATH = Path("/home/ratchet66/Documents/fall_datasets/fall_classifier_model.pkl")
    if not MODEL_PATH.exists():
        classifier = None
    else:
        classifier = joblib.load(MODEL_PATH)
        print("[SUCCESS] Το μοντέλο ML φορτώθηκε επιτυχώς!")

    print("[AI] Φόρτωση YOLOv8-Pose...", flush=True)
    pose_model = YOLO('yolov8n-pose.pt')
    print("[SUCCESS] Το YOLOv8-Pose φορτώθηκε επιτυχώς!", flush=True)

    print("[AI] Εκκίνηση Picamera2 σε ανάλυση 320x240...", flush=True)
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (320, 240), "format": "RGB888"}))
    picam2.start()
    time.sleep(2)
    print("[SUCCESS] Η κάμερα ξεκίνησε επιτυχώς μέσω Picamera2!", flush=True)

    current_locked_target_id = None
    prev_shoulder_y, prev_hip_y, prev_vertical_dist = None, None, None
    FALL_THRESHOLD, PRE_FALL_THRESHOLD = 0.55, 0.32

    last_person_seen = time.monotonic()
    search_started_since = None
    SEARCH_DELAY = 0.6
    SEARCH_TIMEOUT = 4.0

    frame_count = 0
    results = []

    while True:
        frame = picam2.capture_array()
        if frame is None:
            time.sleep(0.01)
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        h, w, _ = frame.shape

        frame_count += 1
        if frame_count % 3 == 0:
            results = pose_model.track(frame, persist=True, verbose=False)

        annotated_frame = frame.copy()
        target_found = False
        wave_detected_id = None

        if results and len(results) > 0:
            res = results[0]
            boxes = res.boxes.xyxy.cpu().numpy() if res.boxes.xyxy is not None else []
            track_ids = res.boxes.id.cpu().numpy() if res.boxes.id is not None else [None] * len(boxes)
            keypoints_all = res.keypoints.xy.cpu().numpy() if res.keypoints is not None and res.keypoints.xy is not None else []

            for i, (box, track_id) in enumerate(zip(boxes, track_ids)):
                if track_id is None or i >= len(keypoints_all):
                    continue
                person_id = int(track_id)
                person_pts = keypoints_all[i]
                if len(person_pts) <= 10:
                    continue
                left_shoulder, right_shoulder = person_pts[5], person_pts[6]
                left_wrist, right_wrist = person_pts[9], person_pts[10]
                if left_shoulder[0] > 0 and right_shoulder[0] > 0:
                    if (left_wrist[1] < left_shoulder[1]) or (right_wrist[1] < right_shoulder[1]):
                        wave_detected_id = person_id

            if wave_detected_id is not None:
                current_locked_target_id = wave_detected_id
                print(f"[WAVE] Νέος κλειδωμένος στόχος (ID: {current_locked_target_id})")
                if not follow_started:
                    send_to_esp32("start_follow")
                    follow_started = True

            for i, (box, track_id) in enumerate(zip(boxes, track_ids)):
                if track_id is None:
                    continue
                person_id = int(track_id)
                if current_locked_target_id is None:
                    current_locked_target_id = person_id
                if person_id != current_locked_target_id:
                    continue

                target_found = True
                last_person_seen = time.monotonic()
                search_started_since = None

                x1, y1, x2, y2 = map(int, box)
                person_pts = keypoints_all[i]
                left_shoulder, right_shoulder = person_pts[5], person_pts[6]
                left_hip, right_hip = person_pts[11], person_pts[12]
                left_knee = person_pts[13] if len(person_pts) > 13 else None

                if left_shoulder[0] > 0 and right_shoulder[0] > 0:
                    shoulder_y = float((left_shoulder[1] + right_shoulder[1]) / 2 / h)
                    shoulder_x = float((left_shoulder[0] + right_shoulder[0]) / 2)
                    hip_y = float((left_hip[1] + right_hip[1]) / 2 / h) if left_hip[0] > 0 and right_hip[0] > 0 else shoulder_y + 0.2
                    hip_x = float((left_hip[0] + right_hip[0]) / 2) if left_hip[0] > 0 and right_hip[0] > 0 else shoulder_x

                    vertical_dist = float(abs(hip_y - shoulder_y))
                    torso_angle = 90.0
                    if left_knee is not None and left_knee[0] > 0:
                        torso_angle = calculate_angle((shoulder_x, shoulder_y * h), (hip_x, hip_y * h), (left_knee[0], left_knee[1]))

                    shoulder_y_delta = (shoulder_y - prev_shoulder_y) if prev_shoulder_y is not None else 0.0
                    hip_y_delta = (hip_y - prev_hip_y) if prev_hip_y is not None else 0.0
                    vertical_dist_delta = (vertical_dist - prev_vertical_dist) if prev_vertical_dist is not None else 0.0

                    prev_shoulder_y, prev_hip_y, prev_vertical_dist = shoulder_y, hip_y, vertical_dist

                    state_type = 0
                    if classifier is not None:
                        X_live = pd.DataFrame([[shoulder_y, hip_y, vertical_dist, shoulder_y_delta, hip_y_delta, vertical_dist_delta]],
                                              columns=['shoulder_y', 'hip_y', 'vertical_dist', 'shoulder_y_delta', 'hip_y_delta', 'vertical_dist_delta'])
                        fall_prob = float(classifier.predict_proba(X_live)[0][1])
                    else:
                        fall_prob = 0.0

                    is_rapid_drop = shoulder_y_delta > 0.035
                    is_body_low = (vertical_dist < 0.20) or (torso_angle < 55.0)

                    if fall_prob >= FALL_THRESHOLD or (is_body_low and is_rapid_drop):
                        state_type = 2
                    elif fall_prob >= PRE_FALL_THRESHOLD or is_rapid_drop:
                        state_type = 1

                    if state_type == 2 and not fall_detected:
                        cv2.putText(annotated_frame, "!!! FALL DETECTED !!!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        send_motion("stop")
                        send_to_esp32("fall_detected")
                        # Κλήση της συνάρτησης για φωνητική ειδοποίηση και SMS
                        threading.Thread(target=handle_fall_event, daemon=True).start()
                        fall_detected = True
                    elif state_type == 0 and fall_detected:
                        fall_detected = False

                    if follow_started and not fall_detected:
                        center_x = shoulder_x / w
                        if center_x < 0.40:
                            send_motion("left")
                        elif center_x > 0.60:
                            send_motion("right")
                        elif vertical_dist < 0.30:
                            send_motion("forward")
                        else:
                            send_motion("stop")

                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated_frame, f"ID:{person_id} (Prob:{fall_prob:.2f})", 
                                (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

            if not target_found and current_locked_target_id is not None:
                if follow_started and not fall_detected:
                    send_motion("stop")
                    lost_time = time.monotonic() - last_person_seen
                    if lost_time > SEARCH_DELAY:
                        if search_started_since is None:
                            search_started_since = time.monotonic()
                        if time.monotonic() - search_started_since < SEARCH_TIMEOUT:
                            send_motion("left")  
                        else:
                            send_motion("stop")
                            follow_started = False
                            current_locked_target_id = None
                            search_started_since = None

        ret, buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 35])
        if ret:
            with lock:
                output_frame = buffer.tobytes()

        time.sleep(0.01)

    picam2.stop()

def generate_frames():
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                continue
            frame_data = output_frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        time.sleep(0.04)

# --- FLASK API ---
@app.route('/')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_caretaker_phone', methods=['POST'])
def set_caretaker_phone():
    global caretaker_phone_number
    data = request.get_json(force=True, silent=True)
    if data and 'phone' in data:
        caretaker_phone_number = data.get('phone')
        return jsonify({"status": "success", "registered_phone": caretaker_phone_number}), 200
    return jsonify({"status": "error", "message": "Missing phone number"}), 400

@app.route('/stop_alarm', methods=['POST'])
@app.route('/stop', methods=['POST'])
@app.route('/clear_display', methods=['POST'])
def stop_alarm():
    global alarm_active
    alarm_active = False
    send_to_esp32("CLEAR_ALERT")
    return jsonify({"status": "success", "message": "Alarm stopped"}), 200

# --- TERMINAL CONFIGURATION FOR REMINDERS ---
def configure_reminders_from_terminal():
    global active_reminder_times, reminder_custom_message
    print("\n" + "="*50)
    print(" 💊 ΡΥΘΜΙΣΗ ΥΠΕΝΘΥΜΙΣΕΩΝ ΧΑΠΙΩΝ ΑΠΟ ΤΟ TERMINAL")
    print("="*50)
    
    times_input = input("Δώσε τις ώρες για τα χαπια σε μορφή HH:MM (π.χ. 09:00, 14:30, 21:00 ή Enter για καμία): ").strip()
    if times_input:
        active_reminder_times = [t.strip() for t in times_input.split(",") if t.strip()]
        print(f"[INFO] Οι υπενθυμίσεις ορίστηκαν για τις: {active_reminder_times}")
    else:
        print("[INFO] Καμία υπενθύμιση δεν ορίστηκε.")

    msg_input = input(f"Δώσε μήνυμα υπενθύμισης (πατήστε Enter για προεπιλογή: '{DEFAULT_MESSAGE}'): ").strip()
    if msg_input:
        reminder_custom_message = msg_input
    print(f"[INFO] Μήνυμα υπενθύμισης: '{reminder_custom_message}'")
    print("="*50 + "\n")

if __name__ == '__main__':
    configure_reminders_from_terminal()

    threading.Thread(target=camera_processing_loop, daemon=True).start()
    threading.Thread(target=schedule_checker, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)