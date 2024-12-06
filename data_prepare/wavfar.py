import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse
from pydub import AudioSegment

def parse_timestamp(timestamp_file):
    with open(timestamp_file, 'r') as f:
        lines = f.readlines()
        if len(lines) == 0:
            return None, None
        elif len(lines) == 1:
            timestamp = lines[0].strip()
            parts = list(map(float, timestamp.split(':')))
            if len(parts) == 3:
                h, m, s = parts
            elif len(parts) == 2:
                h, m = 0, parts[0]
                s = parts[1]
            elif len(parts) == 1:
                h, m = 0, 0
                s = parts[0]
            total_seconds = h * 3600 + m * 60 + s
            #if total_seconds < 10:
            return timestamp, "end"
            #else:
                #return "0:00.000", timestamp
        else:
            start_time = lines[0].strip()
            end_time = lines[1].strip()
            return start_time, end_time

def convert_to_milliseconds(timestamp):
    parts = list(map(float, timestamp.split(':')))
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m = 0, parts[0]
        s = parts[1]
    elif len(parts) == 1:
        h, m = 0, 0
        s = parts[0]
    milliseconds = int((h * 3600 + m * 60 + s) * 1000)
    return milliseconds

def process_wav_file(wav_file, start_time, end_time, output_path):
    audio = AudioSegment.from_wav(wav_file)
    start_ms = convert_to_milliseconds(start_time) if start_time != "0:00.000" else 0
    end_ms = convert_to_milliseconds(end_time) if end_time != "end" else len(audio)
    cropped_audio = audio[start_ms:end_ms]
    cropped_audio.export(output_path, format="wav")

def process_folder(folder, far_dir, target_dir, log_file):
    subfolder_name = os.path.basename(folder)
    center_folder_path = os.path.join(folder, f"{subfolder_name}-CSOBx3")
    if not os.path.exists(center_folder_path):
        return

    timestamp_file = os.path.join(center_folder_path, "timestamp.txt")
    if not os.path.exists(timestamp_file):
        log_file.write(f"{timestamp_file} has no timestamp file.\n")
        return

    start_time, end_time = parse_timestamp(timestamp_file)
    if start_time is None and end_time is None:
        log_file.write(f"{timestamp_file} has no timestamps.\n")
    elif start_time is not None and end_time == "end":
        log_file.write(f"{timestamp_file} has only one short timestamp: {start_time}.\n")
    elif start_time == "0:00.000" and end_time is not None:
        log_file.write(f"{timestamp_file} has only one long timestamp: {end_time}.\n")

    target_subfolder = os.path.join(target_dir, subfolder_name)
    os.makedirs(target_subfolder, exist_ok=True)

    far_subfolder = os.path.join(far_dir, subfolder_name)
    if not os.path.exists(far_subfolder):
        log_file.write(f"{far_subfolder} does not exist.\n")
        return

    for wav_file in os.listdir(far_subfolder):
        if wav_file.endswith(".wav"):
            wav_file_path = os.path.join(far_subfolder, wav_file)
            output_wav_path = os.path.join(target_subfolder, wav_file)
            process_wav_file(wav_file_path, start_time, end_time, output_wav_path)

def process_pcm_files(input_dir, far_dir, target_dir, max_workers=8):
    all_folders = [os.path.join(input_dir, d) for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
    
    with open("log.txt", "w") as log_file:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_folder, folder, far_dir, target_dir, log_file) for folder in all_folders]
            with tqdm(total=len(futures), desc="Processing folders") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)

parser = argparse.ArgumentParser()
parser.add_argument("--timestape_dir")
parser.add_argument("--input_audio_dir")
parser.add_argument("--output_audio_dir")
args = parser.parse_args()

input_directory = args.timestape_dir
far_directory = args.input_audio_dir
output_directory = args.output_audio_dir

process_pcm_files(input_directory, far_directory, output_directory, max_workers=16)
