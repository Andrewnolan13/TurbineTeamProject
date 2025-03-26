import torch
import torch.nn as nn


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout=0.2, bidirectional=True):
        super(LSTMAutoencoder, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.num_directions = 2 if bidirectional else 1
        
        # Encoder
        self.lstm_encoder = nn.LSTM(
            input_size, hidden_size, num_layers, 
            batch_first=True, dropout=dropout, bidirectional=bidirectional
        )

        # Decoder
        self.lstm_decoder = nn.LSTM(
            hidden_size * self.num_directions, hidden_size, num_layers, 
            batch_first=True, dropout=dropout
        )
        
        # Output layer
        self.fc = nn.Linear(hidden_size, input_size)
    
    def forward(self, x):
        batch_size, seq_len, _ = x.shape
        
        # Encode
        _, (hidden, cell) = self.lstm_encoder(x)
        
        # If bidirectional, reshape hidden state
        if self.bidirectional:
            hidden = hidden.view(self.num_layers, self.num_directions, batch_size, self.hidden_size).sum(dim=1)
            cell = cell.view(self.num_layers, self.num_directions, batch_size, self.hidden_size).sum(dim=1)

        # Decoder input: start with zeros
        # decoder_input = torch.zeros(batch_size, seq_len, self.hidden_size).to(x.device)
        decoder_input = torch.zeros(batch_size, seq_len, self.hidden_size * self.num_directions).to(x.device)

        # Decode (Reconstruct the sequence)
        decoder_output, _ = self.lstm_decoder(decoder_input, (hidden, cell))
        
        # Output layer
        out = self.fc(decoder_output)
        return out