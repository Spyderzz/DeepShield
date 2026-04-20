import nbformat as nbf
import os

nb = nbf.v4.new_notebook()

text = """\
# DeepShield: FaceForensics++ ViT Training 
Run this entirely in Google Colab.
**Before running**:
1. Go to `Runtime` -> `Change runtime type` -> select **T4 GPU**.
2. Run the cells below sequentially.
"""

code_install = """\
!pip install timm transformers datasets accelerate evaluate opencv-python
"""

code_ffpp = """\
# We create the download script inside the Colab environment
download_script = '''#!/usr/bin/env python
import argparse
import os
import urllib.request
import tempfile
import time
import sys
import json
from tqdm import tqdm
from os.path import join

FILELIST_URL = 'misc/filelist.json'
DEEPFEAKES_DETECTION_URL = 'misc/deepfake_detection_filenames.json'
DEEPFAKES_MODEL_NAMES = ['decoder_A.h5', 'decoder_B.h5', 'encoder.h5',]
DATASETS = {
    'original': 'original_sequences/youtube',
    'Deepfakes': 'manipulated_sequences/Deepfakes',
    'Face2Face': 'manipulated_sequences/Face2Face',
    'FaceShifter': 'manipulated_sequences/FaceShifter',
    'FaceSwap': 'manipulated_sequences/FaceSwap',
    'NeuralTextures': 'manipulated_sequences/NeuralTextures'
}
ALL_DATASETS = ['original', 'Deepfakes', 'Face2Face', 'FaceShifter', 'FaceSwap', 'NeuralTextures']
COMPRESSION = ['raw', 'c23', 'c40']
TYPE = ['videos']

def download_file(url, out_file):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    if not os.path.isfile(out_file):
        urllib.request.urlretrieve(url, out_file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_path', type=str)
    parser.add_argument('-d', '--dataset', type=str, default='all')
    parser.add_argument('-c', '--compression', type=str, default='c40')
    parser.add_argument('-t', '--type', type=str, default='videos')
    parser.add_argument('-n', '--num_videos', type=int, default=50) # Small amount for tutorial
    args = parser.parse_args()
    
    base_url = 'http://kaldir.vc.in.tum.de/faceforensics/v3/'
    
    datasets = [args.dataset] if args.dataset != 'all' else ALL_DATASETS
    for dataset in datasets:
        dataset_path = DATASETS[dataset]
        print(f'Downloading {args.compression} of {dataset}')
        
        file_pairs = json.loads(urllib.request.urlopen(base_url + FILELIST_URL).read().decode("utf-8"))
        filelist = []
        if 'original' in dataset_path:
            for pair in file_pairs:
                filelist += pair
        else:
            for pair in file_pairs:
                filelist.append('_'.join(pair))
                filelist.append('_'.join(pair[::-1]))
            
        filelist = filelist[:args.num_videos]
        dataset_videos_url = base_url + f'{dataset_path}/{args.compression}/{args.type}/'
        dataset_output_path = join(args.output_path, dataset_path, args.compression, args.type)
        
        for filename in tqdm(filelist):
            download_file(dataset_videos_url + filename + ".mp4", join(dataset_output_path, filename + ".mp4"))

if __name__ == "__main__":
    main()
'''

with open("download_ffpp.py", "w") as f:
    f.write(download_script)

!python download_ffpp.py ./data -d all -c c40 -t videos -n 50
"""

code_extract = """\
import cv2
import os
import glob
from tqdm import tqdm

def extract_frames(video_folder, output_folder, label, max_frames=4):
    os.makedirs(output_folder, exist_ok=True)
    videos = glob.glob(os.path.join(video_folder, "*.mp4"))
    
    for vid_path in tqdm(videos, desc=f"Extracting {label}"):
        vid_name = os.path.basename(vid_path).replace('.mp4','')
        cap = cv2.VideoCapture(vid_path)
        count = 0
        while cap.isOpened() and count < max_frames:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.resize(frame, (224, 224))
            out_path = os.path.join(output_folder, f"{vid_name}_f{count}.jpg")
            cv2.imwrite(out_path, frame)
            count += 1
        cap.release()

# Extract Real
extract_frames('./data/original_sequences/youtube/c40/videos', './dataset/real', 'real')

# Extract Fakes
fakes = ['Deepfakes', 'Face2Face', 'FaceSwap', 'NeuralTextures']
for f in fakes:
    extract_frames(f'./data/manipulated_sequences/{f}/c40/videos', './dataset/fake', 'fake')
"""

code_train = """\
import numpy as np
from datasets import load_dataset
from transformers import ViTImageProcessor, ViTForImageClassification, TrainingArguments, Trainer
import torch

# 1. Load Dataset
dataset = load_dataset('imagefolder', data_dir='./dataset')
# Split into train/validation
dataset = dataset['train'].train_test_split(test_size=0.1)

# 2. Preprocessor
model_name_or_path = 'google/vit-base-patch16-224-in21k'
processor = ViTImageProcessor.from_pretrained(model_name_or_path)

def transform(example_batch):
    # Take a list of PIL images and turn them to pixel values
    inputs = processor([x.convert("RGB") for x in example_batch['image']], return_tensors='pt')
    inputs['labels'] = example_batch['label']
    return inputs

prepared_ds = dataset.with_transform(transform)

def collate_fn(batch):
    return {
        'pixel_values': torch.stack([x['pixel_values'] for x in batch]),
        'labels': torch.tensor([x['labels'] for x in batch])
    }

# 3. Load Model
labels = dataset['train'].features['label'].names
model = ViTForImageClassification.from_pretrained(
    model_name_or_path,
    num_labels=len(labels),
    id2label={str(i): c for i, c in enumerate(labels)},
    label2id={c: str(i) for i, c in enumerate(labels)}
)

training_args = TrainingArguments(
    output_dir="./vit-deepshield",
    per_device_train_batch_size=16,
    eval_strategy="steps",
    num_train_epochs=3,
    fp16=True, # Mixed precision for speed
    save_steps=100,
    eval_steps=100,
    logging_steps=10,
    learning_rate=2e-4,
    save_total_limit=2,
    remove_unused_columns=False,
    push_to_hub=False,
    load_best_model_at_end=True,
)

import evaluate
metric = evaluate.load("accuracy")
def compute_metrics(p):
    return metric.compute(predictions=np.argmax(p.predictions, axis=1), references=p.label_ids)

trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=collate_fn,
    compute_metrics=compute_metrics,
    train_dataset=prepared_ds["train"],
    eval_dataset=prepared_ds["test"],
)

# 4. Train
train_results = trainer.train()
trainer.save_model("deepshield_vit_model")
processor.save_pretrained("deepshield_vit_model")
trainer.log_metrics("train", train_results.metrics)
trainer.save_metrics("train", train_results.metrics)
trainer.save_state()
print("Training Complete! The model is saved to ./deepshield_vit_model")
"""

nb['cells'] = [
    nbf.v4.new_markdown_cell(text),
    nbf.v4.new_code_cell(code_install),
    nbf.v4.new_code_cell(code_ffpp),
    nbf.v4.new_code_cell(code_extract),
    nbf.v4.new_code_cell(code_train)
]

with open(r'c:\Users\athar\Desktop\minor2\backend\training\Colab_ViT_Training.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
