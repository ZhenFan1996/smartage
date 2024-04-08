import os
import shutil

def get_directory_info(directory):
    
    file_count = sum(len(files) for _, _, files in os.walk(directory))
    print(f"Total number of files in {directory}: {file_count}")

    total, used, free = shutil.disk_usage(directory)
    print(f"Total size of disk: {total / (1024**3):.2f} GB")
    print(f"Used disk space: {used / (1024**3):.2f} GB")
    print(f"Free disk space: {free / (1024**3):.2f} GB")

if __name__ == "__main__":
    directory = '/mnt/myexternaldrive'
    get_directory_info(directory)