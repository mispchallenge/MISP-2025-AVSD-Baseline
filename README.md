# MISP-2025-AVSD-Baseline

![image](https://user-images.githubusercontent.com/117905504/201367602-b1165b6e-f274-473f-917a-34de27dd8602.png)
Fig.1. The illustration of network structure

### Some details in the code are being improved and modified. You can start with data processing and other operations

## Data preparation

- **Lip ROI extraction**

In the dataset, we provide the position detection results of the face and lips, which can be used to extract the ROI of the face or lips (only the lips are used here). The extracted lip ROI size is 96 × 96 (*W × H*) .

We provide shoulder and lip detection results in  <a href="https://pan.baidu.com/s/1Xtis2q6xkYrqZoudJ4DDTA?pwd=bhyd" title="video_shoulder_lip_detection">video_shoulder_lip_detection</a> (password: bhyd). Please note that the detection results we provide are based on video segments that have been aligned through timestamp cropping (not from the original video). Due to algorithmic detection errors, we do not guarantee the accuracy of the detection results.

You can run `data_prepare.sh` to perform this step.

## Visual embedding module
The visual embedding module is illustrated in the top row of Fig.1. On the basis of the original [lipreading model](https://github.com/mpc001/Lipreading_using_Temporal_Convolutional_Networks), we add three conformer blocks with 256 encoder dims, 4 attention heads, 32 conv kernel size and a 256-cell BLSTM to compute the visual embedding for speakers. The whole network can be regarded as visual voice activity detection (V-VAD) module. After pre-training the visual network as a V-VAD task, V-embeddings are equipped with capability that represent the states of speaking or silent. By feeding the embedding into the fully connected layers, we can get the probability of whether a speaker speaks in each frame. Combining the results of each speaker, we will get the initial diarization results.
## Audio embedding module
The audio embedding module is illustrated in the bottom row of Fig.1. We firstly use the NARA-WPE method to dereverberate the original audio signals. Then, We extracted 40-dimensional FBANKs with 25 ms frame length and 10 ms frame shift. We extract the audio embedding from FBANKS through 4 layers 2D CNN. Then, a fully connected layer projects high dimensional CNNs output to low dimensional A-embeddings. Unlike visual network, we don’t pre-train audio network on any other tasks and directly optimize it with audio-visual decoding network.
## Speaker embedding module
The speaker embedding module is illustrated in the middle row of Fig.1. To reduce the impact of the unreliable visual embedding, we use 100-dimensional i-vector extractor which was trained on Cn-celeb to get the i-vectors as the speaker embedding. We compute i-vectors through the oracle labels for each speaker in the training stage. And in the inference stage, we compute i-vectors through the initial diarization results from the visual embedding extraction module.
## Decoder module
We firstly repeat the three embeddings for different times to solve the problem of different frame shift between audio and video. Then, we combine them to get the total embedding. In the decoding block, we use 2-layer BLSTM with projection to further extract the features. Finally, we use a 1-layer BLSTM with projection and the fully connected layer to get the speech or non-speech probabilities for each speaker respectively. All of BLSTM layers contained 896 cells. In the post-processing stage, we first perform thresholding with the probabilities to produce a preliminary result and adopt the same approaches in [previous work](https://ieeexplore.ieee.org/document/9747067). Furthermore, [DOVER-Lap](https://github.com/desh2608/dover-lap) is used to fuse the results of 8-channels audio.
## Training process
First, we use the parameters of the pre-trained lipreading and train the V-VAD model with a learning rate of 10<sup>−4</sup>. Then, we freeze the visual network
parameters and train the audio network and audio-visual decoding block on synchronized middle-ﬁeld audio and video with a learning rate of 10<sup>−4</sup>. Finally,we unfreeze the visual network parameters and train the whole network jointly on synchronized middle-ﬁeld audio and video with a learning rate of 10<sup>−5</sup>.

# Quick start


- **Add file execution permissions**
```
chmod +x -R /misp2025_baseline/track1_AVSD/  # (Your code path)
```
- **Data prepare**
```
bash data_prepare.sh   # (Please change your file path in the script.)
```
- **Setting kaldi**
```
--- cmd.sh ---
export train_cmd=run.pl
export decode_cmd=run.pl
export cmd=run.pl

--- path.sh ---
export KALDI_ROOT=`pwd`/../../..        # Defining Kaldi root directory
#[ -f $KALDI_ROOT/tools/env.sh ] && . $KALDI_ROOT/tools/env.sh
export PATH=$PWD/utils/:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/tools/irstlm/bin/:$PWD:$PATH
[ ! -f $KALDI_ROOT/tools/config/common_path.sh ] && echo >&2 "The standard file $KALDI_ROOT/tools/config/common_path.sh is not present -> Exit!" && exit 1
. $KALDI_ROOT/tools/config/common_path.sh
export LC_ALL=C
```

- **Pre-trained model**


Lipreading_LRW.pt is the pre-trained model of lipreading. The training process will use it. Therefore, if you want to conduct the training process, you must download this model. And if you use this model, please cite the paper at the bottom of this link: https://github.com/mpc001/Lipreading_using_Temporal_Convolutional_Networks

You can download these models in this link of Google drive: [https://drive.google.com/drive/folders/1kh40NNBW84kODM0PrWvYLwDCjuqpKqj7?usp=sharing](https://drive.google.com/file/d/1k7WwUp6NTfudNMV3CqtM9rbBprHiZoyP/view?usp=sharing)

Please put the downloaded model into model/pretrained/

- **Training**
```
bash run.sh 
# options:
		   --stage 1
# change the number to start from different training stage
```
Please change some file paths in the script to your own path.

- **Decoding**
```
bash run.sh 
# options:
		   --stage 6
# change the number to start from different training stage
(stage 6 ~ 10 are the decoding process using single channel audio; stage 11 ~ 12 are the decoding process fusing 6-channels audio)
```
The lip ROI and ivector of the training set will be used in the decoding process. So you need to use stage2 of `data_prepare.sh` to extract the lip ROI of the training set, and use stage 3 of `run.sh` to extract the ivector of the training set. We have prepared the [ivector](./exp/nnet3_cnceleb_ivector/ivectors_misp_train/) of the training set. You can directly use it.

- **Evaluation script**

The method of calculating DER has been integrated in `run.sh`

If you only need to evaluate, you can execute the following command
```
bash local/analysis_diarization.sh AVSD Evaluation dev ref.rttm sys.rttm | grep ALL
(The ref.rttm is the oracle rttm file and the sys.rttm is your result)
```

## **Requirments**

- Kaldi
- pytorch
- Python Package:
  
  nbformat
  
  argparse
  
  numpy
  
  tqdm
  
  opencv-python
  
  einops
  
  scipy
  
  prefetch_generator
  
- [Dover-lap](https://github.com/desh2608/dover-lap)
- [Lipreading using Temporal Convolutional Networks](https://github.com/mpc001/Lipreading_using_Temporal_Convolutional_Networks)
# Citation

If you find this code useful in your research, please consider to cite the following papers:

```bibtex
@inproceedings{he2022,
  title={End-to-End Audio-Visual Neural Speaker Diarization},
  author={He, Mao-kui and Du, Jun and Lee, Chin-Hui},
  booktitle={Proc. Interspeech 2022},
  pages={1461--1465},
  year={2022}
}

```

## License

It is noted that the code can only be used for comparative or benchmarking purposes. Users can only use code supplied under a [License](./LICENSE) for non-commercial purposes.
