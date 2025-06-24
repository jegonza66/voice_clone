from pyannote.audio import Pipeline
import os
from pydub import AudioSegment
from credentials import huggingface_token

audios_path = "G:/My Drive/Voice_Clone/training_audios/raw/"
segments_path = audios_path.replace("raw", "segments")
audios_names = os.listdir(audios_path)

pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1", use_auth_token=huggingface_token)

for audio_name in audios_names:
    # Load the diarization result
    diarization = pipeline(audios_path + audio_name)

    # Identify the speaker with longest total duration = likely your target
    durations = {}
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        durations[speaker] = durations.get(speaker, 0) + (turn.end - turn.start)

    target_speaker = max(durations, key=durations.get)
    print("Most likely target speaker:", target_speaker)

    # Save segments of that speaker
    audio = AudioSegment.from_wav(audios_path + audio_name)
    out_dir = segments_path + audio_name
    os.makedirs(out_dir, exist_ok=True)

    count = 0
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if speaker == target_speaker:
            start_ms = int(turn.start * 1000)
            end_ms = int(turn.end * 1000)
            chunk = audio[start_ms:end_ms]
            chunk.export(f"{out_dir}/target_{count:03d}.wav", format="wav")
            count += 1

    print(f"Saved {count} segments of target speaker to {out_dir}/")
