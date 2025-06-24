import os
import argparse
from tqdm import tqdm
from random import shuffle
import glob


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_list", type=str, default="./filelists/train.txt", help="path to train list")
    parser.add_argument("--val_list", type=str, default="./filelists/val.txt", help="path to val list")
    parser.add_argument("--test_list", type=str, default="./filelists/test.txt", help="path to test list")
    parser.add_argument("--source_dir", type=str, default="./dataset/messi/wavs", help="path to source dir")
    args = parser.parse_args()
    
    train = []
    val = []
    test = []
    idx = 0
    
    for speaker in tqdm(os.listdir(args.source_dir)):
        in_dir = os.path.join(args.source_dir, speaker)
        wavfile_paths = glob.glob(os.path.join(in_dir, '*.wav'))
        wavs = [(speaker, wav) for wav in os.listdir(in_dir)]  # Store folder and wav file as tuples
        shuffle(wavs)
        train += wavs[2:-10]
        val += wavs[:2]
        test += wavs[-10:]
        
    shuffle(train)
    shuffle(val)
    shuffle(test)

    print("Writing", args.train_list)
    with open(args.train_list, "w") as f:
        for (folder, fname) in tqdm(train):
            print((folder, fname))
            wavpath = os.path.join("dataset/messi/wavs", folder, fname)
            f.write(wavpath + "\n")
        
    print("Writing", args.val_list)
    with open(args.val_list, "w") as f:
        for (folder, fname) in tqdm(val):
            wavpath = os.path.join("dataset/messi/wavs", folder, fname)
            f.write(wavpath + "\n")
            
    print("Writing", args.test_list)
    with open(args.test_list, "w") as f:
        for (folder, fname) in tqdm(test):
            wavpath = os.path.join("dataset/messi/wavs", folder, fname)
            f.write(wavpath + "\n")
            