import numpy as np
import pylsl
import time
import os
import csv
import re
import json

SESSION_DIR = "data/s_05_01_25"

class LSLRecorder:
    """
    Records arbitrary named LSL streams directly to CSV files as data arrives.
    Each session is saved to a subdirectory 'r_<n>' under the base directory, where n increments from 0.
    """
    def __init__(
        self,
        streams: dict[str, str],
        session_dir: str,
        update_interval: float = 0.1,
    ):
        """
        :param streams: Mapping from key names to LSL stream names.
        :param session_dir: Base directory for saving CSVs.
        :param update_interval: Sleep interval between pulls.
        """
        self.session_dir = session_dir
        self.update_interval = update_interval
        self._proc_flags = (
            pylsl.proc_clocksync |
            pylsl.proc_dejitter |
            pylsl.proc_monotonize
        )

        self.streams = streams

        # Ensure base directory exists
        os.makedirs(self.session_dir, exist_ok=True)
        # Determine next session index
        existing = [d for d in os.listdir(self.session_dir)
                    if os.path.isdir(os.path.join(self.session_dir, d))]
        indices = []
        for d in existing:
            m = re.match(r"r_(\d+)$", d)
            if m:
                indices.append(int(m.group(1)))
        next_idx = max(indices) + 1 if indices else 0
        recording_dir = os.path.join(self.session_dir, f"r_{next_idx}")
        os.makedirs(recording_dir, exist_ok=True)

        self._configs = {}
        
        freq_info = {}

        for key, name in self.streams.items():
            # Resolve and open LSL inlet
            found = pylsl.resolve_byprop('name', name, timeout=5)
            if not found:
                raise RuntimeError(f"No LSL stream named '{name}' found.")
            inlet = pylsl.StreamInlet(
                found[0], max_buflen=1024, processing_flags=self._proc_flags
            )
            info = inlet.info()
            nch = info.channel_count()
            freq_info[f'{key}_fs'] = info.nominal_srate()

            # Prepare CSV file and writer in the session directory
            fname = os.path.join(recording_dir, f"{key}.csv")
            f = open(fname, 'w', newline='')
            writer = csv.writer(f)

            # Write header row
            desc = info.desc().child('channels').child('channel')
            labels = []
            while not desc.empty():
                labels.append(desc.child_value('label'))
                desc = desc.next_sibling()
            if not labels:
                labels = [f"{key}_{i+1}" for i in range(nch)]
            writer.writerow(['timestamp'] + labels)

            self._configs[key] = {'inlet': inlet, 'writer': writer, 'file': f}
            print(f"[{key}] writing to {fname} with channels {labels}")
            
        # Write recording info to json file
        info_fname = os.path.join(session_dir, "frequency_info.json")
        # If the file already exists, load existing data
        if os.path.exists(info_fname):
            with open(info_fname, 'r') as f:
                freq_info = json.load(f)
                # Compare the new data with the existing data, if they are different, raise an error
                if freq_info != freq_info:
                    raise RuntimeError(f"Frequency info file {info_fname} already exists and is different from the new data.")
            print(f"Frequency info file {info_fname} already exists.")
        else:
            # If the file does not exist, create it
            with open(info_fname, 'w') as f:
                json.dump(freq_info, f, indent=4)
            print(f"Frequency info file {info_fname} created.")

    def update(self):
        """Pull new chunks and write to CSV immediately."""
        for cfg in self._configs.values():
            data, stamps = cfg['inlet'].pull_chunk(timeout=0.0)
            if data:
                arr = np.array(data)
                for sample, stamp in zip(arr, stamps):
                    ts_ms = int(round(stamp * 1000))
                    row = [ts_ms] + sample.tolist()
                    cfg['writer'].writerow(row)
                cfg['file'].flush()

    def collect_and_close(self):
        """Continuously update until interrupted, then close files."""
        print("Start recording. Press Ctrl+C to stop.")
        try:
            while True:
                self.update()
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            print("\nStopping and closing files...")
            for cfg in self._configs.values():
                cfg['file'].close()
            print("All files closed.")


def main():
    recorder = LSLRecorder(
        streams={
            'exg': "raw_exg",
            'prompt': "finger_prompt"
        },
        session_dir=SESSION_DIR
    )
    recorder.collect_and_close()


if __name__ == "__main__":
    main()
