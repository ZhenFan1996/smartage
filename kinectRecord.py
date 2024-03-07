import cv2
import subprocess
import time
import datetime
import os
import pyudev

def find_camera_vendor_product(vendor_id, product_id):
    context = pyudev.Context()
    video_devices = [device for device in context.list_devices(subsystem='video4linux') 
                     if 'ID_VENDOR_ID' in device.properties and 'ID_MODEL_ID' in device.properties
                     and device.properties['ID_VENDOR_ID'] == vendor_id and device.properties['ID_MODEL_ID'] == product_id]

    if not video_devices:
        return -1  
    min_index = min(int(device.device_node.rpartition('/')[-1][len('video'):]) for device in video_devices)
    return min_index

def motion_detection(device_idx):
    cap = cv2.VideoCapture(index)
    background_subtractor = cv2.createBackgroundSubtractorMOG2(history=120, varThreshold=150)
    while True:
        now = datetime.datetime.now()
        hour= now.hour
        ret, frame = cap.read()
        if not ret:
            break
        fg_mask = background_subtractor.apply(frame)
        fg_mask = cv2.erode(fg_mask, None, iterations=1)
        fg_mask = cv2.dilate(fg_mask, None, iterations=3)
        cnt = 0

        if motion_detected and now.hour >= 6 and now.hour <= 22:
            true_count += 1
            if true_count >= 20:  
                print("True - Motion Detected")
                print('--------Start Record----------')
                record(200)
                cap.release()
        else:
            true_count = 0  

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def kill_process(p):
    p.terminate()  
    p.wait()  

def record(time_out_seconds):
    file_path = f"/mnt/myexternaldrive/video-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.mkv"
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

    timer = threading.Timer(timeout_seconds, kill_process, [process])
    timer.start()