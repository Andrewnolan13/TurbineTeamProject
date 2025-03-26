import torch.optim as optim
import torch
import torch.nn as nn
import numpy as np
def train_model(model, num_epochs, train_loader, device):
    '''
    Train LSTM Model 
    model: LSTM model 
    num_epochs: Total Epochs 
    train_loader; Data Loder Dataseset
    device: cpu or gpu (setto = GPU)
    '''

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            output = model(batch)
            loss = criterion(output, batch)  # Reconstruction loss
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss/len(train_loader):.4f}")



# calculate Threshol;d 
# Step 1: Collect Reconstruction Errors on Training Set
def eval_model(model, train_loader, device, k=6):
    '''
    Eval on trainloader to get threshold values. 
    model: LSTM model
    train_loder: Dataset
    k: number of std deviations to consider default to k=6
    device: CPU or GPU

    '''
    model.eval()
    train_errors = []

    with torch.no_grad():
        for batch in train_loader:
            batch = batch.to(device)
            output = model(batch)
            # Compute MSE per sequence (batch-wise)
            batch_loss = torch.mean((output - batch) ** 2, dim=(1,2))  # (batch_size,) shape
            train_errors.extend(batch_loss.cpu().numpy())

    train_errors = np.array(train_errors)


    # Option 1: Standard Deviation method
    k = 6  # can be tuned (e.g., 2 or 3)
    threshold = np.mean(train_errors) + k * np.std(train_errors)

    # Option 2: Percentile method (more robust)
    threshold = np.percentile(train_errors, 95)  #
    

    return train_errors, threshold