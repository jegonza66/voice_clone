from speaker_encoder.voice_encoder import SpeakerEncoder
import torch
import librosa
import numpy as np

smodel = SpeakerEncoder('speaker_encoder/ckpt/pretrained_bak_5805000.pt')

def get_spk_emb(wav_path, device="cpu"):
    wav, _ = librosa.load(wav_path, sr=16000)
    wav, _ = librosa.effects.trim(wav, top_db=20)
    emb = smodel.embed_utterance(wav)
    return torch.from_numpy(emb).unsqueeze(0).to(device)

embeddings = []

data_file = "filelists/train.txt"

with open(data_file, "r") as file:
    lines = file.readlines()

# Strip newline characters from each line
lines = [line.strip() for line in lines]

for fname in lines:
    embeddings.append(get_spk_emb(fname))

# Average the embeddings
embeddings_tensor = torch.stack(embeddings, dim=0)
mean_embedding_tensor = torch.mean(embeddings_tensor, dim=0).unsqueeze(0)
np.save("spk_emb.npy", mean_embedding_tensor.numpy())