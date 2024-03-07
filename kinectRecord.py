import cv2
import subprocess
import time
import datetime
import os
import pyudev
import threading


is_recording = False

def find_camera_vendor_product(vendor_id, product_id):
    context = pyudev.Context()
    video_devices = [device for device in context.list_devices(subsystem='video4linux') 
                     if 'ID_VENDOR_ID' in device.properties and 'ID_MODEL_ID' in device.properties
                     and device.properties['ID_VENDOR_ID'] == vendor_id and device.properties['ID_MODEL_ID'] == product_id]

    if not video_devices:
        return -1  
    min_index = min(int(device.device_node.rpartition('/')[-1][len('video'):]) for device in video_devices)
    return min_index

def motion_detection(device_idx, time):
    global is_recording
    cap = cv2.VideoCapture(device_idx)
    background_subtractor = cv2.createBackgroundSubtractorMOG2(history=120, varThreshold=150)
    true_count = 0
    while True:
        if is_recording:  
            time.sleep(1)  
            continue

        now = datetime.datetime.now()
        ret, frame = cap.read()
        if not ret:
            break
        fg_mask = background_subtractor.apply(frame)
        fg_mask = cv2.erode(fg_mask, None, iterations=1)
        fg_mask = cv2.dilate(fg_mask, None, iterations=3)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < 3000:
                continue
            motion_detected = True
            break
        
        if motion_detected and 0 <= now.hour <= 24:
            true_count += 1
            if true_count >= 20:  
                print("True - Motion Detected")
                print('--------Start Record----------')
                is_recording = True
                cap.release()
                record(time, lambda: set_recording_state(False))  
                cap = cv2.VideoCapture(device_idx)
        else:
            true_count = 0  

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def set_recording_state(state):
    global is_recording
    is_recording = state
    print(f"Recording state set to {is_recording}")



def wait_and_reconnect(camera_delay):
    print(f"Waiting for {camera_delay} seconds to allow camera reconnection...")
    time.sleep(camera_delay)
    print("Attempting to reconnect camera...")

def record(timeout_seconds, device_idx, camera_delay=5):
    global is_recording
    file_path = f"/mnt/myexternaldrive/video-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.mkv"
    print(f"Starting recording to {file_path}")
    command = [
        'k4arecorder',
        '-d', 'WFOV_UNBINNED',
        '-r', '15',
        '-c', '720p',
        '-l', str(timeout_seconds),
        '--imu', 'OFF',
        file_path
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("Recording process started.")

    def callback():
        print("Recording timeout reached. Executing callback.")
        process.wait(timeout = 10)
        set_recording_state(False)
        wait_and_reconnect(camera_delay)

    timer = threading.Timer(timeout_seconds, callback)
    timer.start()
    is_recording = True
    timer.join()  
    print("Callback and timer finished.")


if __name__ == "__main__":
    idx = find_camera_vendor_product('045e', '097d')
    print(idx)
    motion_detection(idx, 30)
