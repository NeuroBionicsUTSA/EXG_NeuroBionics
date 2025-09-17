import os
import pandas as pd
import numpy as np
from pathlib import Path

def create_compressed_sensing_dataset():
    # Define paths
    base_path = Path(os.path.dirname(os.path.dirname(__file__)))
    data_path = base_path / 'data' / 's_05_01_25'
    output_path = base_path / 'compressed_sensing_data'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Initialize a dictionary to store data from all runs
    combined_exg = {}
    
    # First, read all EXG data
    for run in range(7):
        run_path = data_path / f'r_{run}'
        exg_df = pd.read_csv(run_path / 'exg.csv')
        
        # Rename the columns to include the run number
        rename_dict = {}
        for i in range(1, 9):  # 8 channels per run
            rename_dict[f'exg_{i}'] = f'exg_run{run}_ch{i}'
        exg_df = exg_df.rename(columns=rename_dict)
        
        # Store in dictionary with timestamp as key
        combined_exg[run] = exg_df

    # Find the minimum length across all runs
    min_length = min(len(df) for df in combined_exg.values())
    print(f"Using minimum length across all runs: {min_length} samples")
    
    # Create the final dataframe with the timestamps from the first run
    final_df = pd.DataFrame({'timestamp': combined_exg[0]['timestamp'].iloc[:min_length]})
    
    # Add all EXG channels from each run
    for run in range(7):
        # Get the EXG data for this run
        run_data = combined_exg[run].iloc[:min_length]  # Trim to minimum length
        
        # Add all channels from this run
        for col in run_data.columns:
            if col != 'timestamp':  # Skip the timestamp column
                final_df[col] = run_data[col].values
    
    # Save the EXG dataset
    exg_output_file = output_path / 'compressed_sensing_exg.csv'
    final_df.to_csv(exg_output_file, index=False)
    print(f"\nEXG dataset created successfully at {exg_output_file}")
    print(f"EXG dataset shape: {final_df.shape}")
    print(f"Number of samples: {len(final_df)}")
    print(f"Number of channels: {sum('exg' in col for col in final_df.columns)}")
    
    # Save the prompt data separately (using prompt from r_0 since they're the same)
    prompt_df = pd.read_csv(data_path / 'r_0' / 'prompt.csv')
    prompt_output_file = output_path / 'compressed_sensing_prompt.csv'
    prompt_df.to_csv(prompt_output_file, index=False)
    print(f"\nPrompt dataset created successfully at {prompt_output_file}")
    print(f"Prompt dataset shape: {prompt_df.shape}")
    
    print("\nColumns in EXG dataset:", final_df.columns.tolist())
    print("Columns in prompt dataset:", prompt_df.columns.tolist())

if __name__ == "__main__":
    create_compressed_sensing_dataset()
