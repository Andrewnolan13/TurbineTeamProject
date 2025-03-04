import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
from sklearn.metrics import mean_absolute_error, mean_squared_error

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class WindPowerLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(WindPowerLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])



def create_sequences(X, y, seq_length):
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_length):
        X_seq.append(X[i:i+seq_length])
        y_seq.append(y[i+seq_length])
    return np.array(X_seq), np.array(y_seq)



def trainLSTM(model, trainloader, num_epochs = 20):
    criterion = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr = 0.001)

    model.to(device)

    for epoch in range(num_epochs):
        model.train()
        epoch_loss = 0
        for X_batch, y_batch in trainloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            optimizer.zero_grad()

            y_pred = model(X_batch)
            loss = criterion(y_pred, y_batch) 
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss:.4f}")

    # return model 
    #Comment below line if need to save weights. 
    # torch.save(model.satate_dict(), 'lstm_model.pt') 


def testLSTM(model, testloader, scaler):
    model.eval()
    predictions = []
    actuals = []

    with torch.no_grad():
        for X_batch, y_batch in testloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            y_pred = model(X_batch)
            predictions.append(y_pred.cpu().numpy())
            actuals.append(y_batch.cpu().numpy())

    predictions = np.concatenate(predictions)
    actuals = np.concatenate(actuals)
    
    predictions = scaler.inverse_transform(predictions)
    actuals = scaler.inverse_transform(actuals)

    predictions = predictions.flatten()
    actuals = actuals.flatten()

    mae = mean_absolute_error(actuals, predictions)
    rmse = mean_squared_error(actuals, predictions)  # RMSE = sqrt(MSE)
    mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100  # Mean Absolute Percentage Error

    # Print results
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")


    return predictions, actuals
    

def getpredictions(model_class, model_weights, scaler_weights, dataset, seq_length):

    scaler = torch.load(scaler_weights)

    scaled_data = scaler.transform(dataset)

    X_seq, _ = create_sequences(scaled_data, np.zeros(scaled_data.shape[0]), seq_length)  # Y is not needed for prediction

    scaled_tensor = torch.tensor(X_seq, dtype=torch.float32)

        # Initialize the model and load the saved weights
    model = model_class(input_size=scaled_tensor.shape[2], hidden_size=64, num_layers=2, output_size=1)  # Modify params as necessary
    model.load_state_dict(torch.load(model_weights))
    model.eval()  # Set model to evaluation mode

    with torch.no_grad():
        predictions = model(scaled_tensor)

    predictions = predictions.numpy()

    return predictions