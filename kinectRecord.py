import cv2
import subprocess
import time
import datetime
import os
import pyudev
import threading
import signal
import errno
import tempfile


RECORDER_MODEL = 0
FIX_MODEL = 1
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

def set_highest_priority():
    try:
        os.nice(-20)
    except OSError as e:
        if e.errno == errno.EPERM:  
            print("Error: Setting highest priority requires elevated permissions.")


def motion_detection(time_seconds,file_path):
    global is_recording
    fix_record()
    device_idx = find_camera_vendor_product('045e', '097d')
    print(f"The device_idx is {device_idx}")
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
        try:
            if motion_detected and 0 <= now.hour <= 24:
                true_count += 1
                if true_count >= 20:  
                    print("True - Motion Detected")
                    print('--------Start Record----------')
                    is_recording = True
                    cap.release()
                    record(time_seconds,file_path)  
                    cap = cv2.VideoCapture(device_idx)
                    true_count = 0
            else:
                true_count = 0  
        except Exception as e:
            print('------Restart recorder-------')
            fix_record()
            device_idx = find_camera_vendor_product('045e', '097d')
            print(f"The device_idx is {device_idx}")
            continue

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def fix_record():
     fd, temp_path = tempfile.mkstemp(suffix='.mkv')
     os.close(fd) 
     record(5,temp_path,stop_model=FIX_MODEL)
     os.remove(temp_path)


def set_recording_state(state):
    global is_recording
    is_recording = state
    print(f"Recording state set to {is_recording}")



def wait_and_reconnect(camera_delay):
    print(f"Waiting for {camera_delay} seconds to allow camera reconnection...")
    time.sleep(camera_delay)
    print("Attempting to reconnect camera...")

def record(timeout_seconds,file_path, camera_delay=10,stop_model = RECORDER_MODEL):
    global is_recording
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
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=set_highest_priority)
    if stop_model == RECORDER_MODEL:
        print("Recording process started.")
    elif stop_model == FIX_MODEL:
        print("Try to restart Camera")
    def callback():
        print("Recording timeout reached. Executing callback.")
        if stop_model == RECORDER_MODEL:
            process.send_signal(signal.SIGINT)
        process.wait()
        set_recording_state(False)
        wait_and_reconnect(camera_delay)

    timer = threading.Timer(timeout_seconds, callback)
    timer.start()
    is_recording = True
    timer.join()  
    print("Callback and timer finished.")


if __name__ == "__main__":
    idx = find_camera_vendor_product('045e', '097d')
    file_path = f"/mnt/myexternaldrive/video-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.mkv"
    motion_detection(30,file_path)
