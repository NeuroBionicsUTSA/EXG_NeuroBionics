import numpy as np
import time
import pylsl
from itertools import combinations
import threading

class FingerPromptStreamer(threading.Thread):
    def __init__(self, prompt_switch_interval=5, use_custom_sequence=False):
        super().__init__()
        self.prompt_switch_interval = prompt_switch_interval
        self.prompt_labels = ['thumb', 'index', 'middle', 'ring', 'pinky']
        self.prompt_labels_idx = {label: i for i, label in enumerate(self.prompt_labels)}
        self.prompt_groups = ['thumb', 'index', 'middle', ['ring', 'pinky']]
        
        if use_custom_sequence:
            self.prompt_lists = self.generate_custom_sequence()
        else:
            self.prompt_lists = self.generate_prompt_lists()
        
        self.prompt_index = 0
        self.running = False

        # LSL setup
        self.prompt_info = pylsl.StreamInfo(
            'finger_prompt', 'Markers', len(self.prompt_labels),
            1 / self.prompt_switch_interval, 'int8', 'finger_prompt')

        channels = self.prompt_info.desc().append_child("channels")
        for name in self.prompt_labels:
            channels.append_child("channel").append_child_value("label", name)

        self.prompt_outlet = pylsl.StreamOutlet(self.prompt_info)
        
        print("Labels:", self.prompt_labels)

    def generate_prompt_lists(self):
        result = []
        num_groups = len(self.prompt_groups)

        for num_true in range(num_groups + 1):
            for combo in combinations(range(num_groups), num_true):
                prompt = [False] * len(self.prompt_labels)
                for group_index in combo:
                    group = self.prompt_groups[group_index]
                    if isinstance(group, list):
                        for label in group:
                            prompt[self.prompt_labels_idx[label]] = True
                    else:
                        prompt[self.prompt_labels_idx[group]] = True
                result.append(prompt)
        return result

    def generate_custom_sequence(self):
        """
        Generate a custom, predictable sequence for experiments.
        Modify this method to define your specific experimental sequence.
        """
        # Example: Start with rest, then individual fingers, then combinations
        custom_sequence = [
            [False, False, False, False, False],  # Rest position
            [True, False, False, False, False],   # Thumb only
            [False, True, False, False, False],   # Index only
            [False, False, True, False, False],   # Middle only
            [False, False, False, True, False],   # Ring only
            [False, False, False, False, True],   # Pinky only
            [True, True, False, False, False],    # Thumb + Index
            [False, True, True, False, False],    # Index + Middle
            [False, False, True, True, False],    # Middle + Ring
            [False, False, False, True, True],    # Ring + Pinky
            [True, False, False, False, True],    # Thumb + Pinky
            [True, False, True, False, False],  # Thumb + Middle
            [False, True, False, False, True],    # Index + pinky
            [True, True, True, True, True],       # All fingers
        ]
        return custom_sequence

    def run(self):
        self.running = True
        current_prompt = self.prompt_lists[0] if self.prompt_lists else [False] * 5

        while self.running:
            prompt_int = [int(prompt) for prompt in current_prompt]
            self.prompt_outlet.push_sample(prompt_int)
            print(f"Sent prompt list: {prompt_int}")

            time.sleep(self.prompt_switch_interval)

            self.prompt_index = (self.prompt_index + 1) % len(self.prompt_lists)
            # Removed random shuffling for predictable experiment sequence
            current_prompt = self.prompt_lists[self.prompt_index]


    def stop(self):
        self.running = False

if __name__ == "__main__":
    # Set use_custom_sequence=True for predictable experimental sequence
    # Set use_custom_sequence=False for original combination-based prompts
    streamer = FingerPromptStreamer(use_custom_sequence=True)
    streamer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping FingerPromptStreamer...")
        streamer.stop()
        streamer.join()
