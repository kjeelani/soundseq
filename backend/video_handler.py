import os
import tempfile
from typing import List
from moviepy.editor import VideoFileClip
from PIL import Image
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector

from image_analyzer import get_semantic_image_desc
import json
import numpy as np

class Scene():

    def __init__(self, start, end, captions=[]):
        self.start = start
        self.end = end
        self.captions = captions
    
    def __repr__(self):
        return f"Scene(start={self.start}, end={self.end}, caption={self.captions})"
    
    def to_dict(self):
        """
        Converts the Scene object to a dictionary.
        """
        return {
            "start": self.start,
            "end": self.end,
            "captions": self.captions
        }

    @classmethod
    def from_dict(cls, scene_dict):
        """
        Creates a Scene object from a dictionary.
        """
        start = scene_dict.get("start")
        end = scene_dict.get("end")
        captions = scene_dict.get("captions", [])
        return cls(start, end, captions)


class VideoHandler():
    CACHE_ENABLED = True

    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cache_file = (
            f"cache/{os.path.splitext(os.path.basename(video_path))[0]}.json" if self.CACHE_ENABLED else 
            f"cache/{len(os.listdir('cache')) + 1}.json"
        )

        self.video = VideoFileClip(video_path)
        self.scenes = self.load_cache()
        if not self.scenes:
            self.scenes = self.generate_scenes()
            self.store_cache()
            

    def find_scenes(self) -> List[Scene]:
        '''
            Generates list of Scenes based on
            intelligent PySceneDetect
        '''
        video_manager = VideoManager([self.video_path])
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector())

        video_manager.set_duration()  
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)

        scene_list = [
            Scene(scene[0].get_seconds(), scene[1].get_seconds()) 
            for scene in scene_manager.get_scene_list()
        ]
        return scene_list

    def compose_images(self, images, i=0):
        '''
            Composes images into two x two grid
        '''
        # Create a new blank image with space for 2x2 images
        img_width, img_height = images[0].size
        grid_width = 2 * img_width
        grid_height = 2 * img_height
        grid_image = Image.new("RGB", (grid_width, grid_height))

        # Paste images into the grid (right-to-left, top-to-bottom)
        grid_image.paste(images[0], (0, 0)) # TL
        grid_image.paste(images[1], (img_width, 0)) # TR
        grid_image.paste(images[2], (0, img_height)) # BL
        grid_image.paste(images[3], (img_width, img_height)) # BR

        grid_image.save(f"test_images/test{i}.png")
        return grid_image

    def analyze_scene(self, scene: Scene, kf_per_scene: int, i = 0):
        scene_clip = self.video.subclip(scene.start, scene.end)
        duration, fps = scene_clip.duration, scene_clip.fps
        total_frames = int(duration * fps)

        # Get images
        images = []
        with tempfile.TemporaryDirectory() as temp_dir:
            for fn in np.linspace(0, total_frames - 1, kf_per_scene, dtype=int):
                frame = self.video.get_frame(scene.start + fn / fps)
                img = Image.fromarray(frame)
                images.append(img)

            # Process multiple panels per scene.
            scene_descrip = []
            for panel_idx in range(len(images) // 4):
                # Make images in a 2x2 grid
                grid_img = self.compose_images(images[panel_idx * 4: (panel_idx + 1) * 4], i=i + panel_idx)
                img_path = f"{temp_dir}/temp.png"
                grid_img.save(img_path)
                scene_descrip.append(get_semantic_image_desc(img_path))
            scene.captions = scene_descrip

        scene_clip.close()
        
    def generate_scenes(self, keyframe_per_scene=8) -> List[Scene]:
        """
        Extracts frames intelligently using pyscene to split up video into scenes
        and finding the main action of the scene
        """           
        scenes: List[Scene] = self.find_scenes()
        for i, scene in enumerate(scenes):
            self.analyze_scene(scene, keyframe_per_scene, i = 2 * i)
        return scenes
    
    def store_cache(self):
        '''
            Cache scenes to not overuse Vision Model
        '''
        scene_dicts = [scene.to_dict() for scene in self.scenes]
        with open(self.cache_file, 'w') as f:
            json.dump(scene_dicts, f, indent=3)
    
    def load_cache(self):
        """
        Loads scenes from a cache file if it exists.
        
        Args:
        - cache_file: Path to the cache file.
        
        Returns:
        - List of Scene objects or None if cache file does not exist.
        """
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                scene_dicts = json.load(f)
            return [Scene.from_dict(scene) for scene in scene_dicts]
        return None

