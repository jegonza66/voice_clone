import librosa
import os
import soundfile as sf

# Define the directory containing the audio segments
save_dir = "dataset/messi/"
os.makedirs(save_dir, exist_ok=True)
segments_dir = "training_audios/segments/"

# Walk through the directory
for root, folder, files in os.walk(segments_dir):
    for file in files:
        print(root, folder, file)
        # Construct the relative path
        relative_path = os.path.relpath(os.path.join(root, file)).replace("\\", "/")  # Ensure forward slashes for compatibility
        # Downsample
        y, sr = librosa.load(relative_path, sr=16000)  # This loads and resamples audio to 16kHz
        # Define save path
        folder = root.split('/')[-1]
        new_path = os.path.join(save_dir, folder)
        os.makedirs(new_path, exist_ok=True)
        save_path = os.path.join(new_path, file)
        # Save
        sf.write(save_path, y, sr)