#!/usr/bin/env bash

# Prepare the far-field video, and extract ROI of face and lips
stage=1
set=training  # Defining the set: training, dev, or eval.

# MISP2025 Dataset Path
misp2025_corpus=/train33/sppro/permanent/hangchen2/pandora/egs/misp2024-mmmt/data/MISP-Meeting/ # your data path
# Python Path
python_path=/home4/intern/minggao5/anaconda3/envs/wenet/bin/ # your python environment path

##########################################################################
# Step1: 360->3x120
# ./xxx_video
##########################################################################
if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ]; then   
  for x in training dev eval; do
    in_video_path=${misp2025_corpus}/${x}
    out_video_path=${misp2025_corpus}/${x}_video
    ${python_path}python local/omini_camera_spliter.py ${in_video_path} ${out_video_path}
  done
fi

##########################################################################
# Step2: Video merge
# ./xxx_video_merge
##########################################################################
if [ ${stage} -le 2 ] && [ ${stop_stage} -ge 2 ]; then   
  for x in training dev eval; do
    in_video_path=${misp2025_corpus}/${x}_video
    out_video_path=${misp2025_corpus}/${x}_video_merge
    ${python_path}python local/merge.py ${in_video_path} ${out_video_path}
  done
fi

##########################################################################
# Step3: Cutoff with PSCx3 timestamp
# ./xxx_video_cutoff
##########################################################################
if [ ${stage} -le 3 ] && [ ${stop_stage} -ge 3 ]; then
  for x in training dev eval; do
    video_input_dir=${misp2025_corpus}/${x}_video_merge
    video_output_dir=${misp2025_corpus}/${x}_video_cutoff
    timestamp_dir=${misp2025_corpus}/${x}
    ${python_path}python local/wav_cutoff.py ${video_input_dir} ${video_output_dir} ${timestamp_dir}
  done
fi

##########################################################################
# Step4: Get the detection roi
##########################################################################

video_dir=${misp2025_corpus}/${set}_video_cutoff/
roi_json_dir=${misp2025_corpus}/${set}_video_shoulder_lip_json_global/ # Defining detection_results path
roi_store_dir=${misp2025_corpus}/MISP-2025-AVSD-Baseline-main/detection_roi/${set}/far  # Defining path to save face and lip ROIs

mkdir -p $roi_store_dir

if [ $stage -le 4 ]; then # lip and face ROI
    ${python_path}python data_prepare/prepare_far_video_roi_speaker_diarization.py \
      --set $set \
      --video_dir $video_dir \
      --roi_json_dir $roi_json_dir \
      --roi_store_dir $roi_store_dir
fi

##########################################################################
# Step5: Prepare far-field audio
##########################################################################

if [ $stage -le 5 ]; then # prepare audio
    input_audio_dir=${misp2025_corpus}/${set}
    output_audio_dir=${misp2025_corpus}/audio/${set}
    mkdir -p $output_audio_dir

    ${python_path}python data_prepare/pcm2wav.py \
      --input_audio_dir $input_audio_dir \
      --output_audio_dir $output_audio_dir
fi

##########################################################################
# Step6: Wav cutoff by CSOBx3 timestamps, and 32bit wav to 16bit wav
##########################################################################
if [ $stage -le 6 ]; then # prepare audio
    timestape_dir=${misp2025_corpus}/${set}
    input_audio_dir=${misp2025_corpus}/audio/${set}
    output_audio_dir=${misp2025_corpus}/audio/${set}_new
    mkdir -p $output_audio_dir

    ${python_path}python data_prepare/wavfar.py \
      --timestape_dir $timestape_dir
      --input_audio_dir $input_audio_dir \
      --output_audio_dir $output_audio_dir

    rm -rf "${misp2025_corpus}/audio/${set}"
    mv "${misp2025_corpus}/audio/${set}_new" "${misp2025_corpus}/audio/${set}"
    
    ${python_path}python data_prepare/32bit-16bit.py \
      --input_audio_dir $input_audio_dir \
      --output_audio_dir $output_audio_dir

    rm -rf "${misp2025_corpus}/audio/${set}"
    mv "${misp2025_corpus}/audio/${set}_new" "${misp2025_corpus}/audio/${set}"
fi
