# 开发人员   wyq
# 开发时间：2023/1/3 14:40
import torch
import torchvision
from torch import nn
from torch.optim.lr_scheduler import StepLR
from torch.utils.tensorboard import SummaryWriter
import time
from model import *

'''
使用GPU进行训练
方式一：网络模型  数据（输入，标注） 损失函数     进行.cuda()

方式二：.to   一般此方式居多   -------------本页以此为例

    device=torch.device("cpu") 或
    device=torch.device("cuda:0")
    模型、损失函数、数据   例：model=model.to(device)
'''
# 定义训练的设备
device = torch.device("cuda:0")
# 步骤1：准备数据集
from torch.utils.data import DataLoader

train_data = torchvision.datasets.CIFAR10(root="./dataset", train=True, transform=torchvision.transforms.ToTensor(),
                                          download=True)
test_data = torchvision.datasets.CIFAR10(root="./dataset", train=False, transform=torchvision.transforms.ToTensor(),
                                         download=True)
train_data_size = len(train_data)
test_data_size = len(test_data)
print(f'训练集长度为{train_data_size}')
print(f'测试集长度为{test_data_size}')
# 利用DataLoader加载数据集
train_dataloader = DataLoader(train_data, batch_size=64)
test_dataloader = DataLoader(test_data, batch_size=64)

# 创建模型网络
model = torchvision.models.vgg16(weights="DEFAULT",
                                 progress=True)
model.classifier.add_module("add_linear", nn.Linear(1000, 10))
model = model.to(device)  # 到这个设备上
# 损失函数
loss_fn = nn.CrossEntropyLoss()
loss_fn = loss_fn.to(device)
# 优化器
learning_rate = 0.01
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)

# 训练网络的一些参数
# 训练次数
total_train_step = 0
# 测试次数
total_test_step = 0
# 训练轮数
epoch = 50

# 添加TensorBoard
writer = SummaryWriter("./logs_train")
start_time = time.time()

'''
等间隔调整学习率 StepLR
>>> # Assuming optimizer uses lr = 0.01 for all groups
>>> # lr = 0.01     if epoch < step_size
>>> # lr = 0.001    if step_size <= epoch < step_size*2
>>> # lr = 0.0001   if step_size*2 <= epoch < step_size*3
VGG16模型 epoch==1 就能達到
'''
scheduler = StepLR(optimizer, step_size=20, gamma=0.1)

for i in range(epoch):
    print(f'-------第{i + 1}次训练开始-------')

    # 训练步骤开始
    model.train()
    for data in train_dataloader:
        imgs, targets = data
        imgs = imgs.to(device)
        targets = targets.to(device)
        outputs = model(imgs)
        loss = loss_fn(outputs, targets)
        # 优化器优化模型
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_train_step += 1
        if total_train_step % 100 == 0:
            end_time = time.time()
            print(end_time - start_time)
            print(f'训练次数{total_train_step}step,Loss为：{loss.item()}')
            writer.add_scalar("train_loss", loss.item(), total_train_step)
    scheduler.step()
    print('-------epoch: ', i, 'lr: ', scheduler.get_last_lr())
    print('-------epoch: ', i, 'optimizer.[lr]: ', optimizer.param_groups[0]['lr'])
    # 测试步骤开始
    model.eval()
    total_test_loss = 0
    total_accuracy = 0
    with torch.no_grad():
        for data in test_dataloader:
            imgs, targets = data
            imgs = imgs.to(device)
            targets = targets.to(device)
            outputs = model(imgs)
            loss = loss_fn(outputs, targets)
            total_test_loss += loss.item()
            accuracy = (outputs.argmax(1) == targets).sum()
            total_accuracy += accuracy
    print(f"该轮测试集上的Loss：{total_test_loss}")
    print(f"该轮测试集上的accuracy：{total_accuracy / test_data_size}")
    writer.add_scalar("test_loss", total_test_loss, total_test_step)
    writer.add_scalar("test_accuraacy", total_accuracy / test_data_size, total_test_step)
    total_test_step += 1
    # 保存每轮的模型
    # torch.save(model, f"model{epoch}.pth")
torch.save(model, f"model{epoch}.pth")
writer.close()
