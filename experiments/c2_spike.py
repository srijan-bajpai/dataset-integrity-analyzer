import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Subset
import numpy as np
import matplotlib.pyplot as plt
import os
import time

def get_binary_cifar10(train=True):
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    dataset = torchvision.datasets.CIFAR10(root='./data', train=train,
                                            download=True, transform=transform)
    
    # Filter to only class 0 (airplane) and class 1 (automobile)
    idx = (np.array(dataset.targets) == 0) | (np.array(dataset.targets) == 1)
    dataset.targets = np.array(dataset.targets)[idx].tolist()
    dataset.data = dataset.data[idx]
    return dataset

def create_imbalanced_subset(dataset, imbalance_ratio):
    # Imbalance ratio: class 0 count / class 1 count
    # Let class 0 be the majority, class 1 be the minority
    class_0_idx = np.where(np.array(dataset.targets) == 0)[0]
    class_1_idx = np.where(np.array(dataset.targets) == 1)[0]
    
    # Base count is max 5000 for each in training
    # For a quick spike, let's use 2000 for majority class
    majority_count = 2000
    minority_count = int(majority_count / imbalance_ratio)
    
    subset_idx = np.concatenate([
        np.random.choice(class_0_idx, majority_count, replace=False),
        np.random.choice(class_1_idx, minority_count, replace=False)
    ])
    
    return Subset(dataset, subset_idx)

class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        self.fc1 = nn.Linear(32 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, 2)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.view(-1, 32 * 8 * 8)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

def train_and_evaluate(train_dataset, test_dataset, epochs=5):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)
    
    model = SimpleCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    for epoch in range(epochs):
        model.train()
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
    return 100 * correct / total

def main():
    print("Loading CIFAR-10...")
    full_train = get_binary_cifar10(train=True)
    test_dataset = get_binary_cifar10(train=False)
    
    # Quick balanced test set (e.g. 500 per class)
    idx_test_0 = np.where(np.array(test_dataset.targets) == 0)[0][:500]
    idx_test_1 = np.where(np.array(test_dataset.targets) == 1)[0][:500]
    test_subset = Subset(test_dataset, np.concatenate([idx_test_0, idx_test_1]))
    
    imbalance_ratios = [1.0, 5.0, 20.0]
    accuracies = []
    
    for ir in imbalance_ratios:
        print(f"\n--- Training with Imbalance Ratio: {ir}:1 ---")
        train_subset = create_imbalanced_subset(full_train, ir)
        acc = train_and_evaluate(train_subset, test_subset, epochs=5)
        print(f"Test Accuracy: {acc:.2f}%")
        accuracies.append(acc)
        
    print("\nResults:")
    for ir, acc in zip(imbalance_ratios, accuracies):
        print(f"IR {ir}:1 -> {acc:.2f}%")
        
    plt.figure(figsize=(8, 5))
    plt.plot(imbalance_ratios, accuracies, marker='o', linestyle='-', color='b')
    plt.title('Impact of Class Imbalance on Model Accuracy (C2 Spike)')
    plt.xlabel('Imbalance Ratio (Majority:Minority)')
    plt.ylabel('Test Accuracy (%)')
    plt.grid(True)
    plt.xticks(imbalance_ratios)
    
    output_path = 'c2_spike_results.png'
    plt.savefig(output_path)
    print(f"\nSaved plot to {output_path}")
    
    # Simple check for monotonicity
    if accuracies[0] > accuracies[1] and accuracies[1] > accuracies[2]:
        print("SUCCESS: Monotone degradation curve observed. C2 hypothesis is viable.")
    else:
        print("WARNING: Degradation curve is not strictly monotone. May need tuning.")

if __name__ == '__main__':
    main()
