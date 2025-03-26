import numpy as np 
import pandas as pd
import torch
from torch.utils.data import DataLoader
from sklearn.preprocessing import MinMaxScaler
def create_sequences(data, seq_length=5):
    '''
    Convert Dataset into Seq Data:
    data: datain np format
    seq: Number of timesteps needed for prediction for the next step
    seq default = 5
    means: t1,t2,t3..t5 used for prediction for t6...
    '''

    sequences = []
    for i in range(len(data) - seq_length):
        sequences.append(data[i:i + seq_length])
    return np.array(sequences)


def process_new_data(model, file_path, columns_to_drop, scaler, batch_size, global_threshold, device):
    df2 = pd.read_csv(file_path, sep = ';')
    # Convert timestamp to datetime (optional, useful for visualization)
    df2['time_stamp'] = pd.to_datetime(df2['time_stamp'])
    seq_length = 5  # Adjust as needed
    # Select sensor columns only (ignore 'train_pred' and 'TimeStamp')
    sensor_columns =  df2.columns.drop(columns_to_drop)
    data2 = df2[sensor_columns].values
    new_data = scaler.transform(data2)
    X_new = create_sequences(new_data, seq_length)
    X_new = torch.tensor(X_new, dtype=torch.float32)
    new_loader = DataLoader(X_new, batch_size=batch_size, shuffle=False)

    model.eval()
    new_errors = []

    with torch.no_grad():
        for batch in new_loader:
            batch = batch.to(device)
            output = model(batch)
            batch_loss = torch.mean((output - batch) ** 2, dim=(1,2))
            new_errors.extend(batch_loss.cpu().numpy())

    new_errors = np.array(new_errors)
    # Clear NAN values
    new_errors = np.nan_to_num(new_errors, nan=0.0)
        # Option 1: Standard Deviation method
    k = 3  # can be tuned (e.g., 2 or 3)
    local_threshold = np.mean(new_errors) + k * np.std(new_errors)

    # Option 2: Percentile method (more robust)
    local_threshold = np.percentile(new_errors, 95)  #
    # Label as normal or anomaly
    global_anomalies = new_errors > global_threshold
    local_anomalies = new_errors> local_threshold
    
    timestamps = df2['time_stamp'].iloc[seq_length-1:].values  
    return new_errors, local_threshold, global_anomalies, local_anomalies, timestamps