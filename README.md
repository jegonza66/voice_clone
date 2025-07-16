# Voice Clone Bot 🎙️

A Telegram bot for voice cloning that serves as a wrapper around the [FreeVC](https://github.com/OlaWod/FreeVC) repository, which contains the voice model training and inference code.

## About

This repository implements a user-friendly Telegram bot interface for voice conversion using the FreeVC model. FreeVC enables high-quality text-free one-shot voice conversion, allowing users to transform their voice to sound like different speakers.

### Built on FreeVC Technology

This bot leverages the [FreeVC](https://github.com/OlaWod/FreeVC) model, which:
- Adopts the end-to-end framework of [VITS](https://arxiv.org/abs/2106.06103) for high-quality waveform reconstruction
- Proposes strategies for clean content information extraction without text annotation
- Uses information bottleneck techniques with [WavLM](https://arxiv.org/abs/2110.13900) features
- Implements spectrogram-resize based data augmentation for improved content purity

For technical details, research paper, and audio samples, visit the [original FreeVC repository](https://github.com/OlaWod/FreeVC).

## Features

- 🤖 **Telegram Bot Interface**: Easy-to-use bot for voice conversion
- 🎵 **High-Quality Voice Conversion**: Powered by FreeVC's advanced neural networks
- 🚀 **One-Shot Conversion**: No training required for new voices
- 📱 **User-Friendly**: Simple audio upload and voice selection process
- 🔄 **Multiple Voice Models**: Support for different target voices

## How It Works

1. Send an audio file to the Telegram bot
2. Select a target voice from available options
3. Receive your transformed audio with the new voice
4. The bot uses FreeVC's inference pipeline under the hood

## Setup

### Prerequisites

1. **Clone this repository:**
   ```bash
   git clone https://github.com/jegonza66/voice_clone.git
   cd voice_clone
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download required models:**
   - Download [WavLM-Large](https://github.com/microsoft/unilm/tree/master/wavlm) and place it in the `wavlm/` directory
   - Download pretrained FreeVC models from the [original repository](https://github.com/OlaWod/FreeVC)

4. **Configure Telegram Bot:**
   - Create a Telegram bot using [@BotFather](https://t.me/botfather)
   - Create a `credentials.py` file with your bot token:
     ```python
     telegram_api_token = "YOUR_BOT_TOKEN_HERE"
     ```

5. **Prepare voice models:**
   - Place speaker embeddings in the `speaker_embeddings/` directory
   - Place model checkpoints in the `checkpoints/` directory
   - Update the `AVAILABLE_VOICES` dictionary in `voice_clone_bot.py`

### Running the Bot

```bash
python voice_clone_bot.py
```

## Bot Usage

1. Start a conversation with your bot on Telegram
2. Send `/start` to see the welcome message
3. Send an audio file (voice message or audio file)
4. Choose from available voice options
5. Wait for processing and receive your transformed audio

## Direct FreeVC Usage (Advanced)

If you want to use the FreeVC model directly without the Telegram bot interface, you can use the original inference and training scripts:

### Inference Example

Download the pretrained checkpoints and run:

```python
# inference with FreeVC
CUDA_VISIBLE_DEVICES=0 python convert.py --hpfile logs/freevc.json --ptfile checkpoints/freevc.pth --txtpath convert.txt --outdir outputs/freevc

# inference with FreeVC-s
CUDA_VISIBLE_DEVICES=0 python convert.py --hpfile logs/freevc-s.json --ptfile checkpoints/freevc-s.pth --txtpath convert.txt --outdir outputs/freevc-s
```

### Training Example

For training your own models, refer to the [original FreeVC repository](https://github.com/OlaWod/FreeVC) for detailed instructions on:
- Data preprocessing
- Training configuration
- Model fine-tuning

## Technical Details

This repository includes the complete FreeVC implementation with:
- Voice conversion models and training scripts
- WavLM-based content extraction
- HiFi-GAN vocoder integration
- Spectrogram-resize data augmentation
- Speaker embedding extraction

## Credits and References

This project is built upon the excellent work of:

**FreeVC**: [Towards High-Quality Text-Free One-Shot Voice Conversion](https://arxiv.org/abs/2210.15418)
- Original repository: https://github.com/OlaWod/FreeVC
- Paper: https://arxiv.org/abs/2210.15418
- Demo: https://olawod.github.io/FreeVC-demo/

### Referenced Projects

- https://github.com/jaywalnut310/vits
- https://github.com/microsoft/unilm/tree/master/wavlm
- https://github.com/jik876/hifi-gan
- https://github.com/liusongxiang/ppg-vc
