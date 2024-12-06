#!/usr/bin/env python
# _*_ coding: UTF-8 _*_
import os
import textgrid
import logging

# 设置路径
input_dir = '/train33/sppro/permanent/hangchen2/pandora/egs/misp2024-mmmt/data/MISP-Meeting/training_transcription_rename/'
rttm_dir = '/train33/sppro/permanent/hangchen2/pandora/egs/misp2024-mmmt/data/MISP-Meeting/training_rttm/'
rttm_combined = '/train33/sppro/permanent/hangchen2/pandora/egs/misp2024-mmmt/data/MISP-Meeting/training_rttm_combined/'
vad_dir = '/train33/sppro/permanent/hangchen2/pandora/egs/misp2024-mmmt/data/MISP-Meeting/training_vad/'

# 创建目标目录
os.makedirs(rttm_dir, exist_ok=True)
os.makedirs(vad_dir, exist_ok=True)

def convert_textgrid_to_rttm(textgrid_path, session_name, speaker_id, rttm_dir):
    tg = textgrid.TextGrid()
    tg.read(textgrid_path)
    
    rttm_path = os.path.join(rttm_dir, f"{session_name}_{speaker_id}.rttm")
    with open(rttm_path, "w") as rttm_file:
        for tier in tg.tiers:
            if tier.name == "角色层":
                for interval in tier.intervals:
                    if interval.mark == "<主说话人>" or interval.mark == "<OVERCLEAR>" or interval.mark == " <OVERCLEAR>":
                        start_time = format(interval.minTime, ".2f")
                        duration = format(interval.maxTime - interval.minTime, ".2f")
                        rttm_line = f"SPEAKER {session_name} 1 {start_time} {duration} <NA> <NA> {speaker_id} <NA> <NA>\n"
                        rttm_file.write(rttm_line)

def merge_rttm_files(session_name, rttm_combined, session_rttm_dir):
    session_rttm_path = os.path.join(rttm_combined, f"{session_name}.rttm")
    with open(session_rttm_path, "w") as session_rttm_file:
        for speaker_rttm_file in os.listdir(session_rttm_dir):
            if speaker_rttm_file.endswith(".rttm") and not speaker_rttm_file == f"{session_name}.rttm":
                speaker_rttm_path = os.path.join(session_rttm_dir, speaker_rttm_file)
                with open(speaker_rttm_path, "r") as file:
                    session_rttm_file.write(file.read())

def generate_vad_from_rttm(session_rttm_path, vad_path):
    segments = []
    with open(session_rttm_path, "r") as rttm_file:
        for line in rttm_file:
            parts = line.strip().split()
            start = float(parts[3])
            duration = float(parts[4])
            end = start + duration
            segments.append([start, end])

    if not segments:
        return

    segments.sort()
    merged = [segments[0]]
    for k in segments[1:]:
        if k[0] <= merged[-1][1]:
            merged[-1][1] = max(k[1], merged[-1][1])
        else:
            merged.append(k)

    with open(vad_path, "w") as vad_file:
        for segment in merged:
            start = format(segment[0], ".2f")
            end = format(segment[1], ".2f")
            vad_file.write(f"{start} {end} speech\n")

# 遍历输入目录中的所有 TextGrid 文件
for file in os.listdir(input_dir):
    if file.endswith(".TextGrid"):
        textgrid_path = os.path.join(input_dir, file)
        
        # 提取 session_name 和 speaker_id
        parts = file.split('_')
        session_name = parts[0]  # A213_S219220 作为 session 名字
        speaker_id = parts[4].replace(".TextGrid", "")  # 作为 speaker ID
        
        # 创建对应的 RTTM 和 VAD 目录
        session_rttm_dir = os.path.join(rttm_dir, session_name)
        session_vad_dir = os.path.join(vad_dir, session_name)
        os.makedirs(session_rttm_dir, exist_ok=True)
        os.makedirs(session_vad_dir, exist_ok=True)

        # 转换 TextGrid 为 RTTM
        convert_textgrid_to_rttm(textgrid_path, session_name, speaker_id, session_rttm_dir)

    # 合并 RTTM 文件
    os.makedirs(rttm_combined, exist_ok=True)
    session_rttm_path = os.path.join(rttm_combined, f"{session_name}.rttm")
    merge_rttm_files(session_name, rttm_combined, session_rttm_dir)

    # 生成 VAD 文件
    vad_path = os.path.join(session_vad_dir, f"{session_name}.vad")
    generate_vad_from_rttm(session_rttm_path, vad_path)

print("转换和合并完成！")

