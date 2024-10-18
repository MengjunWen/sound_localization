import numpy as np

dataset = 'mic_recording'
# INPUT PATH
# Base folder containing the foa/mic and metadata folders
dataset_dir = 'D:\\MOOD-SENSE\\ngcc-main\\dataset'

# OUTPUT PATHS
model_dir='/models'            # Dumps the trained models and training curves in this folder
output_dir='/results'    # recording-wise results are dumped in this path.

# Training room simulation parameters
# room dimensions in meters
room_dim_train = [3.5, 6.0, 2.65]
xyz_min_train = [0.0, 0.0, 0.0]
xyz_max_train = room_dim_train
# microphone locations
mic_locs_train = np.array([[1.55, 5.45, 1.80], [0.25, 0.05, 1.80], [3.30, 0.05, 1.80]]).T
print(mic_locs_train[:, 1])

# Testing environment configuration
# Training hyperparams
seed = 0
batch_size = 32
epochs = 30
lr = 0.001  # learning rate
wd = 0.0  # weight decay
ls = 0.0  # label smoothing

# Model parameters
model = 'NGCCPHAT'  # choices: NGCCPHAT, PGCCPHAT
max_delay = 24 #ms
num_channels = 128  # number of channels in final layer of NGCCPHAT backbone
head = 'classifier'  # final layer type. Choices: 'classifier', 'regression'
loss = 'ce'  # use 'ce' loss for classifier and 'mse' loss for regression
# Set to true in order to replace Sinc filters with regular convolutional layers
no_sinc = False

sig_len = 2048  # length of snippet used for tdoa estimation

audio_length_s = 5#s
mic_fs = int(20000)  # microphone sampling rate
# mic_hop_len_s = float(1/mic_fs) # 

label_location_fs = int(2000)
# label_hop_len_s = float(1/label_location_fs) #

# 因此，每 10 个 mic data有一个 location label。
nb_track_label_ratio = int(mic_fs / label_location_fs) # track_label_resolution

# threshold in samples
c = 343 # m/s
# accuracy threshold in cm
t_cm = 10
t = t_cm * mic_fs / (343 * 100)