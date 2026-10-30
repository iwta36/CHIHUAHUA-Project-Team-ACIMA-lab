# CHIHUAHUA Robot

Cynoid Health Intelligence for Home Ubiquitous Assistance, Hazard Updates and Alert

CHIHUAHUA is an open-source, AI-powered bionic robot dog based on the WaveGo 12-DOF platform. Designed as an autonomous medical companion for the elderly and patients, it leverages a Raspberry Pi 4B and an ESP32 to provide real-time patient monitoring, fall detection, and medical assistance.

## Key Features

Real-Time Fall Detection: Uses YOLOv8-Pose for skeletal tracking and a custom trained Machine Learning ensemble model (Random Forest & LightGBM) to detect falls with high accuracy.

Patient Tracking: Identifies and follows the patient autonomously using computer vision.

Emergency SMS Alerts: Instantly notifies the caretaker via SMS (Twilio API) if a fall is detected.

Medication Reminders: Automated, scheduled voice alerts emitted directly from the robot to remind patients to take their medication.

Caretaker Android App: A dedicated mobile application for caretakers to set up reminders and receive status updates.

# Repository Structure

/robot_code: Main Python scripts running on the Raspberry Pi (Motion control, Camera feed, Flask server, and Main Loop).

/android_app: Source code for the Caretaker Android application.

/machine_learning: Datasets, training scripts, and the exported .pkl / .task models for fall detection and pose tracking.

/docs: Technical documentation, hardware specifications, and machine learning model details.

# Hardware Requirements

Robot Chassis: WAVEGO 12-DOF bionic dog (Waveshare)

Controllers: Raspberry Pi 4 Model B (Host) & ESP32 (Sub-controller)

Vision: Raspberry Pi Camera Module v2 (Sony IMX219, 8MP)

Audio: Waveshare 8Ω 5W Speaker + Adafruit MAX98357 I2S Class-D Amplifier

Power: 2x 18650 Batteries (5200mAh)

Quick Start (Raspberry Pi Setup)

Clone the repository:

git clone https://github.com/YourUsername/CHIHUAHUA-Robot.git
cd CHIHUAHUA-Robot


# Install dependencies:

pip install -r requirements.txt


Note: Ensure picamera2 is installed and configured on your Raspberry Pi OS.

# Configure API Keys:
Open robot_code/MAIN_PROJECT_CODE.py and replace the Twilio placeholder strings with your actual credentials:

TWILIO_ACCOUNT_SID = "YOUR_TWILIO_ACCOUNT_SID_HERE"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN_HERE"
TWILIO_PHONE_NUMBER = "YOUR_TWILIO_PHONE_NUMBER_HERE"


# Run the System:

python robot_code/MAIN_PROJECT_CODE.py


You can access the live video feed by navigating to http://<RASPBERRY_PI_IP>:5000/ on any web browser.

# Android App Setup

Navigate to the /android_app directory and open the project using Android Studio. Sync the Gradle files and deploy the app to your Android device to manage the robot's medication schedule remotely.

Developed for Open Source Presentation.
