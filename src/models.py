'''
this file will eventually have LTSM too
'''

import torch.nn as nn


# class FeedForwardNN(nn.Module):
#     def __init__(self, input_size, hidden_size=32):
#         super(FeedForwardNN, self).__init__()
#         self.fc1 = nn.Linear(input_size, hidden_size)
#         self.relu = nn.ReLU()
#         self.fc2 = nn.Linear(hidden_size, 1)  # Output layer (1 neuron for power output)

#     def forward(self, x):
#         x = self.fc1(x)
#         x = self.relu(x)
#         x = self.fc2(x)
#         return x
    
class FeedForwardNN(nn.Module):
    def __init__(self, input_size, hidden_size=32):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, 1)
        self.activation = nn.Tanh()

    def forward(self, x):
        x = self.fc1(x)
        x = self.activation(x)
        x = self.fc2(x)
        x = self.activation(x)
        x = self.fc3(x)
        return x