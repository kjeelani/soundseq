from openai import OpenAI
from video_handler import VideoHandler
from moviepy.editor import AudioFileClip, CompositeAudioClip
from time import sleep
import numpy as np
from pathlib import Path
import voyageai
import faiss
import json
import os
import re

"""
input: action text, timestamp, duration
> distill action to sound effects
> convert sound effects to embeddings
> vector search for matching tagged audio file
> place audio file in video at right timestamp w/ given duration (if loopable, otherwise min(sfx_length, duration))
"""

# Endpoints
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
vo = voyageai.Client(api_key=VOYAGE_API_KEY)

def extract_sound(actions, batch):
    """
    Distill Action to relevant SFX.
    >>> extract_sound("A brawny man leaps barefoot off the hardwood floor, snarling.") 
    >>> ["hardwood creaking", "air whoosh"]
    """

    if not batch:

        ACTION_TO_SOUND_SYSTEM_PROMPT = "For the given action, what FOLEY should be in the scene? \
            Provide a comma separated list with at most three entries. Example: [thud, air whoosh, distant chatter]"

        completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ACTION_TO_SOUND_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{actions}"
            }
        ]
        )
        response = completion.choices[0].message.content
        list_match = re.search(r'\[(.*?)\]', response)
        return [sound.strip() for sound in list_match.group(1).split(',')] if list_match else []
    
    # Batch process 
    ACTION_TO_SOUND_SYSTEM_PROMPT_BATCH = "For each scene description, what FOLEY should be in the scene? \
        Generate a comma separated list with at most three entries. Example: [thud, air whoosh, distant chatter]. \
        Put all those lists in a master comma separated list in the order of the corresponding input scenes. \
        Example input: [[\"A frustrated, brawny man leaps barefoot off the hardwood floor, snarling.\"], \
            [\"A muscular man punches a bamboo wall and collapses to the floor.\"]]. \
        Example output: [[thud, air whoosh, wood creaking], [concrete slap, fabric rustling]]"
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": ACTION_TO_SOUND_SYSTEM_PROMPT_BATCH},
            {
                "role": "user",
                "content": f"{actions}"
            }
        ]
        )
    
    response = completion.choices[0].message.content
    list_matches = re.findall(r'\[(.*?)\]', response)
    sound_lists = []
    for match in list_matches:
        sounds = [sound.strip() for sound in match.split(',')]
        sound_lists.append(sounds)
    return sound_lists

def rag_sfx(index, embeddings, sfx_tags, audio_files, threshold=np.inf):
    distances, indices = index.search(np.array(embeddings, dtype='float32'), 1)
    return [audio_files[sfx_tags[idx[0]]] for dist, idx in zip(distances, indices) if dist[0] < threshold]

def place_audio(video_handler, audio_file_path, start_time, scene_duration):
    """
    Places the audio file in the video at the given start time for min(scene_duration, audio_file_length).
    """
    audio = AudioFileClip(audio_file_path)
    audio_duration = min(audio.duration, scene_duration)
    audio = audio.subclip(0, audio_duration)
    
    # Avoid overwrting audio. 
    if video_handler.video.audio:
        current_audio = video_handler.video.audio
        composite_audio = CompositeAudioClip([current_audio, audio.set_start(start_time)])
        video_with_audio = video_handler.video.set_audio(composite_audio)
    else:
        video_with_audio = video_handler.video.set_audio(audio.set_start(start_time))
    
    return video_with_audio

def generate_sfx(filepath):
    video_handler = VideoHandler(filepath)
    scenes = video_handler.scenes
    scene_sounds = extract_sound([scene.caption for scene in scenes], batch=True)

    # File Metadata
    SFX_FOLDER_PATH = 'SFX'
    with open(f'{SFX_FOLDER_PATH}/metadata.json', 'r') as f:
        tag_data = json.load(f)
    sfx_tags = [entry['tag'] for entry in tag_data]
    audio_files = {entry['tag']: entry['audio_file'] for entry in tag_data}
    sfx_emb = np.array(vo.embed(sfx_tags, model="voyage-3").embeddings)

    # Setup RAG
    dimension = sfx_emb.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(sfx_emb)

    # Scene Descriptions -> Embeddings
    for idx, sounds in enumerate(scene_sounds):
        sounds_emb = np.array(vo.embed(sounds, model="voyage-3").embeddings)
        closest_audio_files = rag_sfx(index, sounds_emb, sfx_tags, audio_files, threshold=1.3)
    
        # Rate limiting to avoid API issues
        sleep(0.3)

        # Print the list of closest SFX files for the current scene
        print(f"{scenes[idx].caption}: {sounds}: {closest_audio_files}")

        # Place sounds
        for audio_file in closest_audio_files:
            video_handler.video = place_audio(video_handler, f"{SFX_FOLDER_PATH}/{audio_file}", scenes[idx].start, scenes[idx].end - scenes[idx].start)

    out_name = f"video/output/processed_{Path(filepath).stem}.mp4"
    video_handler.video.write_videofile(out_name, codec="libx264", audio_codec="aac")
