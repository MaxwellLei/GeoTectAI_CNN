import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import numpy as np
from NetCore import CNNNetCore
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# 设置随机种子以确保可重复性
torch.manual_seed(42)
np.random.seed(42)

# 定义设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 数据预处理和加载
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

train_dataset = datasets.ImageFolder(root='DataSet/TrainDataSet', transform=transform)
test_dataset = datasets.ImageFolder(root='DataSet/TestDataSet', transform=transform)

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# 初始化模型
model = CNNNetCore().to(device)

# 定义损失函数和优化器
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)


# MCMC采样函数
def mcmc_sample(model, acceptance_prob):
    current_state = {name: param.clone() for name, param in model.named_parameters()}
    proposed_state = {name: param.clone() + torch.randn_like(param) * 0.01 for name, param in model.named_parameters()}

    if np.random.rand() < acceptance_prob:
        for name, param in model.named_parameters():
            param.data.copy_(proposed_state[name])
    else:
        for name, param in model.named_parameters():
            param.data.copy_(current_state[name])


# 训练函数
def train(model, epochs):
    train_losses = []
    train_accuracies = []
    test_accuracies = []

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        correct = 0
        total = 0
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            _, predicted = torch.max(output.data, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()

            if batch_idx % 100 == 0:
                print(f'Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item()}')

        train_loss = epoch_loss / len(train_loader)
        train_accuracy = correct / total
        train_losses.append(train_loss)
        train_accuracies.append(train_accuracy)

        # 在每个epoch结束后测试
        test_accuracy, _, _, _ = test(model)  # Only keep the accuracy
        test_accuracies.append(test_accuracy)

        # 在每个epoch结束后进行MCMC采样
        mcmc_sample(model, acceptance_prob=test_accuracy)

    return train_losses, train_accuracies, test_accuracies


# 测试函数
def test(model):
    model.eval()
    all_predictions = []
    all_targets = []
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            outputs = model(data)
            _, predicted = torch.max(outputs.data, 1)
            all_predictions.extend(predicted.cpu().numpy())
            all_targets.extend(target.cpu().numpy())

    # 计算总体准确率
    accuracy = np.mean(np.array(all_predictions) == np.array(all_targets))
    print(f'Overall Accuracy: {accuracy:.4f}')

    # 计算每个类别的准确率、召回率和F1分数
    precision, recall, f1, _ = precision_recall_fscore_support(all_targets, all_predictions, average=None)

    # 获取类别名称
    class_names = test_dataset.classes

    # 打印每个类别的详细信息
    print("\\nPer-class Performance:")
    for i, class_name in enumerate(class_names):
        print(f"Class: {class_name}")
        print(f"  Precision: {precision[i]:.4f}")
        print(f"  Recall: {recall[i]:.4f}")
        print(f"  F1-score: {f1[i]:.4f}")

    # 计算并打印混淆矩阵
    cm = confusion_matrix(all_targets, all_predictions)
    print("\\nConfusion Matrix:")
    print(cm)

    return accuracy, all_predictions, all_targets, cm


# 主训练循环
num_epochs = 50
train_losses, train_accuracies, test_accuracies = train(model, num_epochs)

# 最终测试
final_accuracy, all_predictions, all_targets, cm = test(model)
print(f'Final Overall Accuracy: {final_accuracy:.4f}')

# 保存模型和结果
torch.save({
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'train_losses': train_losses,
    'train_accuracies': train_accuracies,
    'test_accuracies': test_accuracies,
    'final_accuracy': final_accuracy,
    'all_predictions': all_predictions,
    'all_targets': all_targets,
    'confusion_matrix': cm,
}, 'cnn_mcmc_model_full.pth')

print("Model and training data saved.")


# 绘制学习曲线
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(train_losses)
plt.title('Training Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')

plt.subplot(1, 2, 2)
plt.plot(train_accuracies, label='Train')
plt.plot(test_accuracies, label='Test')
plt.title('Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

plt.tight_layout()
plt.savefig('learning_curves.png')
plt.close()

# 绘制混淆矩阵
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('True')
plt.savefig('confusion_matrix.png')
plt.close()

print("Learning curves and confusion matrix plots saved.")

# 输出模型参数
for name, param in model.named_parameters():
    print(f'{name}: {param.data}')