import numpy as np
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier

if not os.path.exists('gait_data.csv'):
    print("Error: gait_data.csv not found!")
    exit()

print("Training supervised gait classifier using Label 1 (You) and Label 0 (Stranger)...")
df = pd.read_csv('gait_data.csv')

data = df.iloc[:, :-1].values
labels = df['label'].values

X = []
y = []
window_size = 30
joint_indices = list(range(23, 33))

for i in range(len(data) - window_size):
    window_data = data[i:i+window_size]
    window_labels = labels[i:i+window_size]
    
    # Ensure the entire 30-frame window belongs to the same person/label to avoid mixing
    if window_labels[0] != window_labels[-1] or len(np.unique(window_labels)) > 1:
        continue
        
    current_label = window_labels[0]
    window_tensors = []
    
    for row in window_data:
        frame_joints = []
        for j in joint_indices:
            offset = (j - 23) * 3
            h_offset_l = (23 - 23) * 3
            h_offset_r = (24 - 23) * 3
            hip_center = np.array([row[h_offset_l], row[h_offset_l+1], row[h_offset_l+2]]) + \
                         np.array([row[h_offset_r], row[h_offset_r+1], row[h_offset_r+2]]) / 2.0
            
            pt = np.array([row[offset], row[offset+1], row[offset+2]]) - hip_center
            frame_joints.append(pt)
        
        window_tensors.append(frame_joints)
    
    # Flatten the 3D tensor [30 frames, 10 joints, 3 coordinates] into a 1D feature vector
    flat_vector = np.array(window_tensors).flatten()
    X.append(flat_vector)
    y.append(current_label)

X = np.array(X)
y = np.array(y)

if len(np.unique(y)) < 2:
    print("Warning: Your CSV file only contains one label class (e.g., only 1s or only 0s).")
    print("You should record data for both yourself (1) and a stranger (0) for best classification results!")

# Train a Random Forest classifier
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X, y)

# Save the trained classifier model
with open('gait_model.pkl', 'wb') as f:
    pickle.dump(clf, f)

print("Success! Supervised classifier model saved to gait_model.pkl.")