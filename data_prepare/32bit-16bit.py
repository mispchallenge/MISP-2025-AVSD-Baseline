
import os
from pydub import AudioSegment
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_audio_dir")
parser.add_argument("--output_audio_dir")
args = parser.parse_args()

source_folder = args.input_audio_dir
target_folder = args.output_audio_dir

def convert_audio(source_file_path, target_file_path):

    audio = AudioSegment.from_file(source_file_path)
    audio = audio.set_sample_width(2) 
    

    audio.export(target_file_path, format="wav") 


with ThreadPoolExecutor(max_workers=16) as executor:
    futures = []
    for root, dirs, files in os.walk(source_folder):
        for file in files:
           
            if file.endswith(".wav"):
     
                source_file_path = os.path.join(root, file)
                target_file_path = os.path.join(target_folder, os.path.relpath(root, source_folder), file)
                
            
                os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                
               
                future = executor.submit(convert_audio, source_file_path, target_file_path)
                futures.append(future)
                

    with tqdm(total=len(futures)) as pbar:
        for future in futures:
            future.result()  
            pbar.update()  
