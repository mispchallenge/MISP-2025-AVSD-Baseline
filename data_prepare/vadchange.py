import os

# 输出的汇总文件
output_file = '/train33/sppro/permanent/hangchen2/pandora/egs/misp1/misp2022_baseline-main/track1_AVSD/scp_dir/eval_far_timestamp.lab'

# 清空输出文件（如果存在的话）
with open(output_file, 'w') as f:
    pass  # 不写入任何内容，直接清空文件

# 遍历所有文件夹
root_dir = '/train33/sppro/permanent/hangchen2/pandora/egs/misp2024-mmmt/data/MISP-Meeting/eval_vad/'  # 请替换成你实际的文件夹路径

for folder_name in os.listdir(root_dir):
    folder_path = os.path.join(root_dir, folder_name)
    
    # 确保是文件夹
    if os.path.isdir(folder_path):
        # 查找每个文件夹中的 .vad 文件
        for filename in os.listdir(folder_path):
            if filename.endswith('.vad'):
                file_path = os.path.join(folder_path, filename)
                
                # 获取文件夹名作为文件名
                folder_id = os.path.basename(folder_path)
                
                # 读取 .vad 文件并写入到汇总文件
                with open(file_path, 'r') as file:
                    with open(output_file, 'a') as output:
                        for line in file:
                            # 去除行尾的 "speech" 词语
                            line = line.strip()
                            if line.endswith('speech'):
                                line = line[:-len('speech')].strip()  # 去掉 "speech" 后的空格
                            
                            # 将文件夹名和修改后的行内容写入汇总文件
                            output.write(f"{folder_id} {line}\n")

print(f"汇总完成，结果保存在 {output_file}")
