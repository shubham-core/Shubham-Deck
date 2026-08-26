import cv2
import sys

# Using the exact IP from your phone screen
CAMERA_URL = "http://10.124.165.12:8080/video"

print(f"Attempting to connect to {CAMERA_URL}...")
cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print("Failed to connect. Check the IP and Wi-Fi connection.")
    sys.exit()

print("Connection successful! Press 'q' in the video window to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Lost the stream connection.")
        break
        
    cv2.imshow("V5 Vision Test", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
