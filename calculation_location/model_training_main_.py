

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
import numpy as np
import random
from sklearn.model_selection import train_test_split
from torchinfo import summary
from model import NGCCPHAT, PGCCPHAT, GCC

import cfg
import matplotlib.pyplot as plot
import cls_data_generator
from helpers import LabelSmoothing
plot.switch_backend('agg')

torch.autograd.set_detect_anomaly(True)

# for reproducibility
torch.manual_seed(cfg.seed)
random.seed(cfg.seed)
np.random.seed(cfg.seed)

# calculate the max_delay for gcc
max_tau_gcc = int(np.floor(
    max(np.linalg.norm(cfg.mic_locs_train[:, 0] - cfg.mic_locs_train[:, 1]), 
    np.linalg.norm(cfg.mic_locs_train[:, 0] - cfg.mic_locs_train[:, 1]), 
    np.linalg.norm(cfg.mic_locs_train[:, 0] - cfg.mic_locs_train[:, 1])) * cfg.mic_fs / cfg.c))
print('max_tau_gcc:',max_tau_gcc)

# training parameters
max_tau = max_tau_gcc # cfg.max_delay# cfg.max_delay
fs = cfg.mic_fs
sig_len = cfg.sig_len

epochs = cfg.epochs
# DataLoader参数
batch_size = cfg.batch_size
lr = cfg.lr
wd = cfg.wd
audio_length = cfg.mic_fs * cfg.audio_length_s
label_smooth = cfg.ls

# Training setup
all_splits = [1, 2]

# 对所有文件夹进行循环处理。
print('\n\n---------------------------------------------------------------------------------------------------')
print('----------------------------------      preparing dataset   ------------------------------------------')
print('-------------------------------------------------------------------------------------------   --------')

# ------------------------------- Load train and validation data  -------------------------------
print('Loading all dataset:')
data_gen_all =cls_data_generator.DataGenerator(cfg=cfg, split=all_splits)
tensors1, tensors2, targets =data_gen_all.generate()
samples1 = tensors1.view(-1).numpy() 
samples2 = tensors2.view(-1).numpy()
labels = targets.view(-1).numpy()

# 合并 samples1 和 samples2
data = np.column_stack((samples1, samples2))
print('\n\n---------------------------------------------------------------------------------------------------')

train_data, temp_data, train_labels, temp_labels = train_test_split(data, labels, test_size=0.3, random_state=42)
val_data, test_data, val_labels, test_labels = train_test_split(temp_data, temp_labels, test_size=0.5, random_state=42)
print(train_data)
print('train_data.shape:', train_data.shape)
print(train_labels)
print('train_labels.shape:', train_labels.shape) 
print('\n---------------------------------------------------------------------------------------------------')

# 自定义数据集类，实现overlapping windows
class SequenceDataset(object):
    def __init__(self, data, labels, window_size, stride):
        self.data = data
        self.labels = labels
        self.window_size = window_size
        self.stride = stride

    def __len__(self):
        return int(max(1, (len(self.data) - self.window_size) // self.stride))#+ 1

    def __getitem__(self, idx):
        start = int(idx * self.stride)
        end = int(start + self.window_size)
        data_slice = self.data[start:end]
        label_slice = self.labels[start:end]
        return data_slice, label_slice

# 定义窗口大小和步长
window_size = sig_len
stride = window_size/2

# 创建数据集
train_set = SequenceDataset(train_data, train_labels, window_size, stride)
val_set = SequenceDataset(val_data, val_labels, window_size, stride)
test_set = SequenceDataset(test_data, test_labels, window_size, stride)

# use GPU if available, else CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device: " + str(device))
if device == "cuda":
    num_workers = 1
    pin_memory = True
else:
    num_workers = 0
    pin_memory = False

# load model
if cfg.model == 'NGCCPHAT':
    use_sinc = True if not cfg.no_sinc else False
    model = NGCCPHAT(max_tau, cfg.head, use_sinc,
                     sig_len, cfg.num_channels, fs)
elif cfg.model == 'PGCCPHAT':
    model = PGCCPHAT(max_tau=max_tau_gcc, head=cfg.head)
else:
    raise Exception("Please specify a valid model")

model = model.to(device)
model.eval()
summary(model, [(1, 1, sig_len), (1, 1, sig_len)])

gcc = GCC(max_tau=max_tau_gcc)

optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, epochs)

if cfg.loss == 'ce':
    loss_fn = LabelSmoothing(label_smooth)
elif cfg.loss == 'mse':
    loss_fn = nn.MSELoss()
else:
    raise Exception("Please specify a valid loss function")
print('Using loss function: ' + str(loss_fn))

# ------------------------------- Load data and start training  -------------------------------
# torch.utils.data.DataLoader是PyTorch中用于加载数据的一个迭代器工具。
# 它可以方便地从一个数据集(Dataset)中按批次(batch)加载数据。
train_loader = torch.utils.data.DataLoader(
    train_set,
    batch_size=batch_size,
    shuffle=True,
    num_workers=num_workers,
    pin_memory=pin_memory,
    drop_last=True,
)

val_loader = torch.utils.data.DataLoader(
    val_set,
    batch_size=batch_size,
    shuffle=False,
    num_workers=num_workers,
    pin_memory=pin_memory,
    drop_last=True,
)

test_loader = torch.utils.data.DataLoader(
    test_set,
    batch_size=batch_size,
    shuffle=False,
    num_workers=num_workers,
    pin_memory=pin_memory,
    drop_last=True,
)
print('\n\n------------------------------------------------------------------------------------------')

print('\n\n----------------------------start training------------------------------------------------')
for e in range(epochs):
    mae = 0
    gcc_mae = 0
    acc = 0
    gcc_acc = 0
    train_loss = 0
    logs = {}
    model.train()
    pbar_update = batch_size
    with tqdm(total=len(train_loader.dataset)) as pbar:
        for batch_idx, (data, target) in enumerate(train_loader):
            print('\nbatch_idx:', batch_idx)
            print('\ndata.shape:', data.shape)
            # 分离并重塑 x1 和 x2
            x1 = data[:, :, 0].unsqueeze(1)  
            x2 = data[:, :, 1].unsqueeze(1)  
            target = target.float().to(device)
            delays = torch.mean(target.squeeze(),dim=-1)
            print('\nx1.shape:', x1.shape)  # 验证形状
            print('\nx2.shape:', x2.shape)  # 验证形状
            print('\ndelays.shape:', delays.shape)  # 验证形状
            print('\ndelays:', delays)
            bs = x1.shape[0]
            print('bs:', bs)
            # get delay statistics for normalization when using regression loss
            if cfg.loss == "mse":
                delay_mu = torch.mean(delays) 
                delay_sigma = torch.std(delays) 
                print('\ndelay_mu:', delay_mu) 
                print('\ndelay_mu.shape:', delay_mu.shape) 
                print('\ndelay_sigma:', delay_sigma) 
                print('\ndelay_sigma.shape:', delay_sigma.shape) 

            print('开始计算GCC') 
            
            cc = gcc(x1.squeeze(), x2.squeeze())
            print('\nx1.squeeze().shape:', x1.squeeze().shape)  # 验证形状
            shift_gcc = torch.argmax(cc, dim=-1) - max_tau_gcc
            print('shift_gcc.shape:', shift_gcc.shape) 

            print('开始计算model') 

            if cfg.loss == 'ce':
                delays_loss = torch.round(delays).type(torch.LongTensor)
                print('\n delays_loss.shape:', delays_loss.shape) 
                y_hat = model(x1, x2)
                print('\n y_hat.shape:', y_hat.shape) 
                shift = torch.argmax(y_hat, dim=-1) - max_tau
                print('\n shift.shape:', shift.shape) 
            else:
                delays_loss = (delays - delay_mu) / delay_sigma
                print('\n delays_loss.shape:', delays_loss.shape) 
                y_hat = model(x1, x2)
                print('\n y_hat.shape:', y_hat.shape) 
                shift = y_hat * delay_sigma + delay_mu - max_tau
                print('\n shift.shape:', shift.shape) 

            gt = delays - max_tau
            print('\n gt.shape:', gt.shape) 
            mae += torch.sum(torch.abs(shift-gt))
            gcc_mae += torch.sum(torch.abs(shift_gcc-gt))

            acc += torch.sum(torch.abs(shift-gt) < cfg.t)
            gcc_acc += torch.sum(torch.abs(shift_gcc-gt) < cfg.t)

            optimizer.zero_grad()
            print('y_hat.shape:', y_hat.shape)
            print('delays_loss.shape:', delays_loss.shape)
            loss = loss_fn(y_hat, delays_loss.to(device))
            loss.backward()
            optimizer.step()
            train_loss += loss.detach().item() * bs
            pbar.update(pbar_update)

    train_loss = train_loss / len(train_loader.dataset)
    print(f"Epoch {e+1}, Train Loss: {train_loss:.4f}")
    mae = mae / len(train_loader.dataset)
    gcc_mae = gcc_mae / len(train_loader.dataset)
    acc = acc / len(train_loader.dataset)
    gcc_acc = gcc_acc / len(train_loader.dataset)

    scheduler.step()
    torch.cuda.empty_cache()

    print('\n\n------------------------ start Validation --------------------------------------------')
    # Validation
    model.eval()
    mae = 0.
    gcc_mae = 0.
    acc = 0.
    gcc_acc = 0.
    val_loss = 0.
    with torch.no_grad():
        for data, target in val_loader:
            print('\nbatch_idx:', batch_idx)
            print('\ndata.shape:', data.shape)
            # 分离并重塑 x1 和 x2
            x1 = data[:, :, 0].unsqueeze(1)  
            x2 = data[:, :, 1].unsqueeze(1)  
            target = target.float().to(device)
            delays = torch.mean(target.squeeze(),dim=-1)
            print('\nx1.shape:', x1.shape)  # 验证形状
            print('\nx2.shape:', x2.shape)  # 验证形状
            print('\ndelays.shape:', delays.shape)  # 验证形状
            print('\ndelays:', delays)
            bs = x1.shape[0]
            print('bs:', bs)
            # get delay statistics for normalization when using regression loss
            if cfg.loss == "mse":
                delay_mu = torch.mean(delays) 
                delay_sigma = torch.std(delays) 
                print('\ndelay_mu:', delay_mu) 
                print('\ndelay_mu.shape:', delay_mu.shape) 
                print('\ndelay_sigma:', delay_sigma) 
                print('\ndelay_sigma.shape:', delay_sigma.shape) 

            print('开始计算GCC') 
            
            cc = gcc(x1.squeeze(), x2.squeeze())
            print('\nx1.squeeze().shape:', x1.squeeze().shape)  # 验证形状
            shift_gcc = torch.argmax(cc, dim=-1) - max_tau_gcc
            print('shift_gcc.shape:', shift_gcc.shape) 

            print('开始计算model') 

            if cfg.loss == 'ce':
                delays_loss = torch.round(delays).type(torch.LongTensor)
                print('\n delays_loss.shape:', delays_loss.shape) 
                y_hat = model(x1, x2)
                print('\n y_hat.shape:', y_hat.shape) 
                shift = torch.argmax(y_hat, dim=-1) - max_tau
                print('\n shift.shape:', shift.shape) 
            else:
                delays_loss = (delays - delay_mu) / delay_sigma
                print('\n delays_loss.shape:', delays_loss.shape) 
                y_hat = model(x1, x2)
                print('\n y_hat.shape:', y_hat.shape) 
                shift = y_hat * delay_sigma + delay_mu - max_tau
                print('\n shift.shape:', shift.shape) 

            gt = delays - max_tau
            print('\n gt.shape:', gt.shape) 
            mae += torch.sum(torch.abs(shift-gt))
            gcc_mae += torch.sum(torch.abs(shift_gcc-gt))

            acc += torch.sum(torch.abs(shift-gt) < cfg.t)
            gcc_acc += torch.sum(torch.abs(shift_gcc-gt) < cfg.t)

            loss = loss_fn(y_hat, delays_loss.to(device))
            val_loss += loss.detach().item() * x1.shape[0]

    mae = mae / len(val_loader.dataset)
    gcc_mae = gcc_mae / len(val_loader.dataset)
    acc = acc / len(val_loader.dataset)
    gcc_acc = gcc_acc / len(val_loader.dataset)
    val_loss = val_loss / len(val_loader.dataset)
    print(f"Epoch {e+1}, Val Loss: {val_loss:.4f}")
    torch.cuda.empty_cache()
    
# ------------------------------- training done, save the model  -------------------------------
# Save the model
torch.save(model.state_dict(), 'experiments/NGCC/model.pth')
print('\n\n------------------------------------------------------------------------------------------')

# 在测试集上评估模型
model.eval()
test_loss = 0
with torch.no_grad():
    for data, target in test_loader:
        print('\nbatch_idx:', batch_idx)
        print('\ndata.shape:', data.shape)
        # 分离并重塑 x1 和 x2
        x1 = data[:, :, 0].unsqueeze(1)  
        x2 = data[:, :, 1].unsqueeze(1)  
        target = target.float().to(device)
        delays = torch.mean(target.squeeze(),dim=-1)
        print('\nx1.shape:', x1.shape)  # 验证形状
        print('\nx2.shape:', x2.shape)  # 验证形状
        print('\ndelays.shape:', delays.shape)  # 验证形状
        print('\ndelays:', delays)
        bs = x1.shape[0]
        print('bs:', bs)
        # get delay statistics for normalization when using regression loss
        if cfg.loss == "mse":
            delay_mu = torch.mean(delays) 
            delay_sigma = torch.std(delays) 
            print('\ndelay_mu:', delay_mu) 
            print('\ndelay_mu.shape:', delay_mu.shape) 
            print('\ndelay_sigma:', delay_sigma) 
            print('\ndelay_sigma.shape:', delay_sigma.shape) 

        print('开始计算GCC') 
        
        cc = gcc(x1.squeeze(), x2.squeeze())
        print('\nx1.squeeze().shape:', x1.squeeze().shape)  # 验证形状
        shift_gcc = torch.argmax(cc, dim=-1) - max_tau_gcc
        print('shift_gcc.shape:', shift_gcc.shape) 

        print('开始计算model') 

        if cfg.loss == 'ce':
            delays_loss = torch.round(delays).type(torch.LongTensor)
            print('\n delays_loss.shape:', delays_loss.shape) 
            y_hat = model(x1, x2)
            print('\n y_hat.shape:', y_hat.shape) 
            shift = torch.argmax(y_hat, dim=-1) - max_tau
            print('\n shift.shape:', shift.shape) 
        else:
            delays_loss = (delays - delay_mu) / delay_sigma
            print('\n delays_loss.shape:', delays_loss.shape) 
            y_hat = model(x1, x2)
            print('\n y_hat.shape:', y_hat.shape) 
            shift = y_hat * delay_sigma + delay_mu - max_tau
            print('\n shift.shape:', shift.shape) 

        gt = delays - max_tau
        print('\n gt.shape:', gt.shape) 
        mae += torch.sum(torch.abs(shift-gt))
        gcc_mae += torch.sum(torch.abs(shift_gcc-gt))

        acc += torch.sum(torch.abs(shift-gt) < cfg.t)
        gcc_acc += torch.sum(torch.abs(shift_gcc-gt) < cfg.t)

        loss = loss_fn(y_hat, delays_loss.to(device))
        test_loss += loss.detach().item() * x1.shape[0]

test_loss /= len(test_loader.dataset)
print(f"Test Loss: {test_loss:.4f}")