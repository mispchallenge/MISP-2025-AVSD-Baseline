import numpy as np
from scipy.io import wavfile
import codecs
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import argparse

def pcm2numpy(pcm_file, channel=8, bit=32):
    with codecs.open(pcm_file, 'rb') as pcm_handle:
        pcm_frames = pcm_handle.read()
    if len(pcm_frames) % 2 != 0:
        pcm_frames = pcm_frames[:-1]
    np_array = np.frombuffer(pcm_frames, dtype='int{}'.format(bit), offset=0)
    return np_array.reshape((-1, channel))

def save_channel_to_wav(np_array, subdir, sample_rate, output_dir, channel_index):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Extract the channel data
    channel_data = np_array[:, channel_index]

    # Save the single channel data as a WAV file
    wavfile.write(os.path.join(output_dir, f"{subdir}_{channel_index + 1}.wav"), sample_rate, channel_data)

def process_single_pcm_file(pcm_file, subdir, output_subdir, num_channels, bit_depth, sample_rate):
    # Convert PCM to NumPy array
    numpy_array = pcm2numpy(pcm_file, channel=num_channels, bit=bit_depth)
    # Save each channel to a separate WAV file
    for channel_index in range(num_channels):
        save_channel_to_wav(numpy_array, subdir, sample_rate, output_subdir, channel_index)
    print(f"Processed {pcm_file} and saved {num_channels} WAV files to {output_subdir}")

def process_pcm_files(input_dir, output_dir, num_channels=8, bit_depth=32, sample_rate=16000, max_workers=4):
    tasks = []
    pcm_files = []

    # Collect all PCM files and their output directories
    for subdir in os.listdir(input_dir):
        subdir_path = os.path.join(input_dir, subdir)
        if os.path.isdir(subdir_path):
            for sub_subdir in os.listdir(subdir_path):
                if sub_subdir.endswith('-CSOBx3'):
                    pcm_dir = os.path.join(subdir_path, sub_subdir)
                    for file in os.listdir(pcm_dir):
                        if file.endswith('.pcm'):
                            pcm_file = os.path.join(pcm_dir, file)
                            output_subdir = os.path.join(output_dir, subdir)
                            pcm_files.append((pcm_file, subdir, output_subdir))

    # Process PCM files with a progress bar
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_pcm_file, pcm_file, subdir, output_subdir, num_channels, bit_depth, sample_rate) for pcm_file, subdir, output_subdir in pcm_files]
        with tqdm(total=len(futures), desc="Processing PCM files") as pbar:
            for future in as_completed(futures):
                future.result()
                pbar.update(1)

parser = argparse.ArgumentParser()
parser.add_argument("--input_audio_dir")
parser.add_argument("--output_audio_dir")
args = parser.parse_args()

input_directory = args.input_audio_dir
output_directory = args.output_audio_dir
num_channels = 8  # For 8-channel audio
bit_depth = 32  # Bit depth of the audio
sample_rate = 16000  # Example sample rate, adjust as needed

process_pcm_files(input_directory, output_directory, num_channels, bit_depth, sample_rate, max_workers=16)
