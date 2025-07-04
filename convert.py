import os
import argparse
import torch
import librosa
import time
from scipy.io.wavfile import write
from tqdm import tqdm
import numpy as np
import utils
from models import SynthesizerTrn
from mel_processing import mel_spectrogram_torch
from wavlm import WavLM, WavLMConfig
from speaker_encoder.voice_encoder import SpeakerEncoder
import logging
logging.getLogger('numba').setLevel(logging.WARNING)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    parser = argparse.ArgumentParser()
    parser.add_argument("--hpfile", type=str, default="configs/freevc.json", help="path to json config file")
    parser.add_argument("--ptfile", type=str, default="checkpoints/freevc.pth", help="path to pth file")
    parser.add_argument("--txtpath", type=str, default="convert.txt", help="path to txt file")
    parser.add_argument("--outdir", type=str, default="output/freevc", help="path to output dir")
    parser.add_argument("--use_timestamp", default=False, action="store_true")
    parser.add_argument("--saved_embedding", type=str, default=None, help="path to saved embedding (.npy or .pt)")
    parser.add_argument("--input_audio", type=str, default=None, help="path to input audio file for direct processing")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    hps = utils.get_hparams_from_file(args.hpfile)

    print("Loading model...")
    net_g = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        **hps.model).to(device)
    _ = net_g.eval()
    _ = utils.load_checkpoint(args.ptfile, net_g, None, True)

    print("Loading WavLM for content...")
    cmodel = utils.get_cmodel(0)
    # Process input audio directly if provided
    if args.input_audio:
        print(f"Processing input audio: {args.input_audio}")
        src = args.input_audio
        tgt = args.saved_embedding  # Use the saved embedding for the target voice
        title = os.path.basename(src).split('.')[0] + "_transformed"

        # Load saved embedding if provided
        saved_g_tgt = None
        if args.saved_embedding and hps.model.use_spk:
            print(f"Loading saved embedding from {args.saved_embedding}")
            if args.saved_embedding.endswith('.npy'):
                saved_g_tgt = torch.from_numpy(np.load(args.saved_embedding)).unsqueeze(0).to(device)
            elif args.saved_embedding.endswith('.pt'):
                saved_g_tgt = torch.load(args.saved_embedding).to(device)

            while saved_g_tgt.dim() > 2:
                saved_g_tgt = saved_g_tgt.squeeze()

            if saved_g_tgt.dim() == 1:
                saved_g_tgt = saved_g_tgt.unsqueeze(0)

            print(f"Loaded embedding shape: {saved_g_tgt.shape}")

        with torch.no_grad():
            # Process source audio
            print("Loading source audio...")
            wav_src, _ = librosa.load(src, sr=hps.data.sampling_rate)

            if wav_src.size == 0:
                raise ValueError("Input audio is empty or invalid.")

            wav_src = torch.from_numpy(wav_src).unsqueeze(0).to(device)
            c = utils.get_content(cmodel, wav_src)

            if hps.model.use_spk:
                audio = net_g.infer(c, g=saved_g_tgt)
            else:
                raise ValueError("Target audio or embedding is required for voice conversion.")

            audio = audio[0][0].data.cpu().float().numpy()
            if args.use_timestamp:
                timestamp = time.strftime("%m-%d_%H-%M", time.localtime())
                write(os.path.join(args.outdir, f"{timestamp}_{title}.wav"), hps.data.sampling_rate, audio)
            else:
                write(os.path.join(args.outdir, f"{title}.wav"), hps.data.sampling_rate, audio)

    else:
        print("Processing text...")
        titles, srcs, tgts = [], [], []
        with open(args.txtpath, "r") as f:
            for rawline in f.readlines():
                src, tgt = rawline.strip().split("|")
                title = f"{src.split('/')[-1]}_{tgt.split('/')[-1]}"
                titles.append(title)
                srcs.append(src)
                tgts.append(tgt)

        print("Synthesizing...")
        # Load saved embedding if provided
        saved_g_tgt = None
        if args.saved_embedding and hps.model.use_spk:
            print(f"Loading saved embedding from {args.saved_embedding}")
            if args.saved_embedding.endswith('.npy'):
                saved_g_tgt = torch.from_numpy(np.load(args.saved_embedding)).unsqueeze(0).to(device)
            elif args.saved_embedding.endswith('.pt'):
                saved_g_tgt = torch.load(args.saved_embedding).to(device)

            # Ensure the embedding has the correct shape: [batch_size, embedding_dim]
            # Remove all extra dimensions first, then add batch dimension if needed
            while saved_g_tgt.dim() > 2:
                saved_g_tgt = saved_g_tgt.squeeze()

            if saved_g_tgt.dim() == 1:
                saved_g_tgt = saved_g_tgt.unsqueeze(0)  # Add batch dimension

            print(f"Loaded embedding shape: {saved_g_tgt.shape}")


        with torch.no_grad():
            for line in tqdm(zip(titles, srcs, tgts)):
                title, src, tgt = line

                if hps.model.use_spk:
                    if saved_g_tgt is not None:
                        # Use the saved embedding
                        g_tgt = saved_g_tgt
                    else:
                        print("Loading speaker encoder...")
                        smodel = SpeakerEncoder('speaker_encoder/ckpt/pretrained_bak_5805000.pt')

                        # Compute embedding from target audio (original behavior)
                        wav_tgt, _ = librosa.load(tgt, sr=hps.data.sampling_rate)
                        wav_tgt, _ = librosa.effects.trim(wav_tgt, top_db=20)
                        g_tgt = smodel.embed_utterance(wav_tgt)
                        g_tgt = torch.from_numpy(g_tgt).unsqueeze(0).to(device)
                else:
                # Original mel spectrogram behavior
                    wav_tgt, _ = librosa.load(tgt, sr=hps.data.sampling_rate)
                    wav_tgt, _ = librosa.effects.trim(wav_tgt, top_db=20)
                    wav_tgt = torch.from_numpy(wav_tgt).unsqueeze(0).to(device)
                    mel_tgt = mel_spectrogram_torch(
                        wav_tgt,
                        hps.data.filter_length,
                        hps.data.n_mel_channels,
                        hps.data.sampling_rate,
                        hps.data.hop_length,
                        hps.data.win_length,
                        hps.data.mel_fmin,
                        hps.data.mel_fmax
                    )

                # src
                wav_src, _ = librosa.load(src, sr=hps.data.sampling_rate)
                wav_src = torch.from_numpy(wav_src).unsqueeze(0).to(device)
                c = utils.get_content(cmodel, wav_src)

                if hps.model.use_spk:
                    audio = net_g.infer(c, g=g_tgt)
                else:
                    audio = net_g.infer(c, mel=mel_tgt)
                audio = audio[0][0].data.cpu().float().numpy()
                if args.use_timestamp:
                    timestamp = time.strftime("%m-%d_%H-%M", time.localtime())
                    write(os.path.join(args.outdir, f"{timestamp}_{title}.wav"), hps.data.sampling_rate, audio)
                else:
                    write(os.path.join(args.outdir, f"{title}.wav"), hps.data.sampling_rate, audio)

