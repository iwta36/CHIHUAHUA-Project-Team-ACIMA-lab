import cv2
import mediapipe as mp
import csv
import urllib.request
import os

# Set your training label: 1 for You, 0 for Stranger
RECORD_LABEL = 0

model_path = 'pose_landmarker.task'
if not os.path.exists(model_path):
    url = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'
    urllib.request.urlretrieve(url, model_path)

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO
)

cap = cv2.VideoCapture(0)
file_exists = os.path.isfile('gait_data.csv')
f = open('gait_data.csv', mode='a', newline='')
writer = csv.writer(f)

if not file_exists:
    header = []
    for i in range(23, 33):
        header += [f'x{i}', f'y{i}', f'z{i}']
    header.append('label')
    writer.writerow(header)

# Lower body skeleton connections to draw on screen
lower_body_connections = [
    (23, 24), # Hips
    (23, 25), (25, 27), (27, 31), # Left leg
    (24, 26), (26, 28), (28, 32), # Right leg
    (27, 28)  # Ankles
]

label_text = "TARGET (You)" if RECORD_LABEL == 1 else "STRANGER (Other)"
print(f"Recording session for: {label_text}. Press 'q' to stop.")

frame_timestamp_ms = 0
with PoseLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        h, w, _ = frame.shape
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        frame_timestamp_ms += 33
        results = landmarker.detect_for_video(mp_image, frame_timestamp_ms)
        
        # Draw skeleton on recording window
        if results.pose_landmarks:
            landmarks = results.pose_landmarks[0]
            for conn in lower_body_connections:
                p1, p2 = landmarks[conn[0]], landmarks[conn[1]]
                px1, py1 = int(p1.x * w), int(p1.y * h)
                px2, py2 = int(p2.x * w), int(p2.y * h)
                cv2.line(frame, (px1, py1), (px2, py2), (255, 255, 0), 2)
            
            for j in range(23, 33):
                p = landmarks[j]
                px, py = int(p.x * w), int(p.y * h)
                cv2.circle(frame, (px, py), 4, (0, 255, 255), -1)

        # Save 3D world coordinates to CSV
        if results.pose_world_landmarks:
            lm = results.pose_world_landmarks[0]
            row = []
            for i in range(23, 33):
                row.extend([lm[i].x, lm[i].y, lm[i].z])
            row.append(RECORD_LABEL) 
            writer.writerow(row)
            
        cv2.putText(frame, f"Recording: {label_text}", (30, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if RECORD_LABEL == 1 else (0, 0, 255), 2)
        cv2.imshow('Recording Database', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
f.close()
cv2.destroyAllWindows()
print("Session saved to gait_data.csv!")