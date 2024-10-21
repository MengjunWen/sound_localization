#
# Data generator for training
#
# # [frame number (int)], [event_active (int)], [x (float)], [y (float)], [z (float)]
# # Frame, class, and source enumeration begins at 0. 
# Frames correspond to a temporal resolution of 100msec. 

import os
import shutil
import wave
import numpy as np
import random
from collections import defaultdict

# Set environment variable to avoid OpenMP error
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import csv
from scipy import interpolate
import torch
import cfg

class DataGenerator(object):
    def __init__(self, cfg, split=1, shuffle=True):
        self._dataset_dir = cfg.dataset_dir
        self._dataset_combination = '{}_{}'.format(cfg.dataset, 'dev')
        # 读取wav的文件夹
        self._wav_dir = os.path.join(self._dataset_dir,'wav')
        # 存放 track 的文件夹“/dataset/mic_recording_dev”
        self._track_dir = os.path.join(self._dataset_dir, self._dataset_combination)
        # 读取 location 的文件夹“/dataset/mic_recording_dev_location”
        self._location_dir = os.path.join(self._dataset_dir, 'source_loc')
        self._label_dir = os.path.join(self._dataset_dir, '{}_label'.format(self._dataset_combination))
        self._splits = np.array(split)

        self.mic_fs=cfg.mic_fs
        self.c = cfg.c
        self.label_location_fs=cfg.label_location_fs
        self.nb_track_label_ratio=cfg.nb_track_label_ratio
        self._label_len = None  # total length of label
        self.mic_locs = cfg.mic_locs_train
        self.max_tau = cfg.max_delay
        lower_bound = 0
        upper_bound = self.mic_fs * cfg.audio_length_s
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

        # read tracks
        # 从 _wav_path 读取signal数据放到 track_path 中，提取track长度，
        # 从 _location_dir 读取location的 x, y, z 数据，比较分辨率，并去尾，整合location的长度到跟与track长度一致。
        # 将低分辨率的数据进行填充放进。
        # 在每个对应signal data都得到一列客观的delay。

        print('\n\n---------------- Extracting track: -------------------------------------------------------------------')
        print('\t\tfrom wav_dir {} to track_dir {}'.format(self._wav_dir, self._track_dir))
        create_folder(self._track_dir)
        filewise_frames_min = process_audio_files(self._wav_dir, self._track_dir)
        
        print('\n\n---------------- Extracting labels: -------------------------------------------------------------------')
        print('\t\tfrom _location_dir {} to _label_dir {}'.format(self._location_dir, self._label_dir))
        create_folder(self._label_dir)
        process_location_files(self._location_dir, self._label_dir, filewise_frames_min, self.nb_track_label_ratio)
        # 读取_location_dir中的每个csv文件中的label_mat，得到其长度，
        # 然后与track的长度进行比较，补齐处理，最后得到的就是对应每个wav在每个时刻的值 + 对应的坐标。
    def generate(self):
        self._shuffle = random.shuffle
        self._filenames_list = list()
        self._nb_frames_file = 0   

        print('\n\n---------------- Computing some stats about the dataset----------------' )
        for filename in os.listdir(self._track_dir):
            if int(filename[4]) in self._splits:
                self._filenames_list.append(filename)
        print('\tnb_files: {}\n'.format(len(self._filenames_list)))
        print('self._filenames_list is {}'.format(self._filenames_list))
        print('\tDataset: {}, split: {}\n'
            '\tlabel_dir: {}\n'
            '\ttrack_dir: {}\n'.format(cfg.dataset, self._splits, self._label_dir, self._track_dir)
        )
        
        if self._shuffle:
            random.shuffle(self._filenames_list)
        # Gather in lists, and encode labels as indices
        print('\n\n---------------------getting all dataset------------------------')
        all_data1, all_data2, all_targets = [], [], []
        for file_name in self._filenames_list:
            temp_track = np.load(os.path.join(self._track_dir, file_name))
            print(temp_track)
            temp_label = np.load(os.path.join(self._label_dir, file_name))
            source_loc = temp_label[1:3, :].T  # 转置以匹配维度
            print('source_loc:{}'.format(source_loc))
            for pairs in [[0, 1], [0, 2], [1, 2]]:
                x1 = temp_track[pairs[0], :]
                x2 = temp_track[pairs[1], :]
                d = np.sqrt(np.sum((self.mic_locs[:, pairs[0]] - source_loc) ** 2, axis=1)) - \
                    np.sqrt(np.sum((self.mic_locs[:, pairs[1]] - source_loc) ** 2, axis=1))
                d = np.round(d, decimals=2)
                print('d:', d)
                print('d.shape:{}'.format(d.shape))

                gt_delay = d * self.mic_fs / self.c
                gt_target = gt_delay + self.max_tau
                print('gt_delay.shape:{}'.format(gt_target.shape))
                
                all_data1.extend(x1)
                all_data2.extend(x2)
                all_targets.extend(gt_target)

        # 将所有数据转换为一维张量
        final_tensor1 = torch.tensor(all_data1, dtype=torch.float).view(1, -1)
        final_tensor2 = torch.tensor(all_data2, dtype=torch.float).view(1, -1)
        final_targets = torch.tensor(all_targets, dtype=torch.float).view(1, -1)

        print('Final tensors shapes:')
        print('final_tensor1.shape:', final_tensor1.shape)
        print('final_tensor2.shape:', final_tensor2.shape)
        print('final_targets.shape:', final_targets.shape)

        print('\n\n------------------------all dataset ready------------------------------')

        return final_tensor1, final_tensor2, final_targets
 
def process_audio_files(wav_dir, track_dir):
    filewise_frames_min = {}
    audio_groups = defaultdict(list)
    for file_name in os.listdir(wav_dir):
        if file_name.endswith('.wav'):
            group_id = file_name[:12]
            wav_path = os.path.join(wav_dir, file_name)
            audio_groups[group_id].append(wav_path)

    for group_id, file_paths in audio_groups.items():
        if len(file_paths) == 3:
            # Read all audio files
            audio_data = []
            for wav_path in sorted(file_paths):
                with wave.open(wav_path, 'rb') as wf:
                    frames = wf.getnframes()
                    audio = np.frombuffer(wf.readframes(frames), dtype=np.int16)
                    audio_data.append(audio)

            # Find the minimum length
            proper_length = cfg.mic_fs*cfg.audio_length_s
            min_length = min(len(audio) for audio in audio_data)

            # Trim all audio to minimum length and stack
            combined_audio = np.row_stack([audio[:proper_length] for audio in audio_data])

            nb_track_frames_min = proper_length
            filewise_frames_min[f'{group_id}'] = nb_track_frames_min

            output_filename = f"{group_id}.npy"
            output_path = os.path.join(track_dir, output_filename)
            np.save(output_path, combined_audio)

            print(f"Saved: {output_filename}")
            print(f"Number of track frames: {nb_track_frames_min}")
    return filewise_frames_min

def location_files_read(_output_format_file):
    """
    Loads DCASE output format csv file and returns it as a numpy array

    :param _output_format_file: DCASE output format CSV
    :return: tuple containing:
             - data_array: numpy array of all data
             - total_frames: total number of frames (rows in CSV)
    """
    data_list = []
    with open(_output_format_file, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            # Convert each row to the appropriate data types
            # [frame, x, y, z]
            processed_row = [int(row[0]), float(row[1]), float(row[2]), float(row[3])]
            data_list.append(processed_row)
    # Convert list to numpy array
    data_array = np.array(data_list)
    return data_array

def process_location_files(location_dir, location_label_dir, filewise_frames_min,nb_track_label_ratio):
    print('filewise_frames_min is {}'.format(filewise_frames_min))
    for file_cnt, file_name in enumerate(os.listdir(location_dir)):
        print(file_name)
        data_array = location_files_read(os.path.join(location_dir, file_name))
        nb_track_frames_min = filewise_frames_min[file_name.split('.')[0]]
        # 以 nb_track_frames_min为基准，处理 nb_location_frames，先修剪，再填充成为统一长度。
        nb_label_minimum = nb_track_frames_min//nb_track_label_ratio
        if len(data_array) >= nb_label_minimum:
            # 裁剪数据数组（如果需要）
            data_array = data_array[:nb_label_minimum]
            # 使用三次样条插值将标签补齐到与 track 相同的分辨率
            interpolated_data = interpolate_labels(data_array, nb_track_frames_min)
            interpolated_data = interpolated_data.T
            print(f'{file_cnt}: {file_name}, Original shape: {data_array.shape}, Interpolated shape: {interpolated_data.shape}')
            # 保存插值后的数据
            np.save(os.path.join(location_label_dir, f'{file_name.split(".")[0]}.npy'), interpolated_data)
        else:
            # 如果data_array长度短于nb_label_minimum 那就出了问题。
            print(f'Error: Data array length ({len(data_array)}) is less than minimum required length ({nb_label_minimum}) for file {file_name}')
            continue

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        print('{} folder does not exist, creating it.'.format(folder_name))
        os.makedirs(folder_name)

def delete_and_create_folder(folder_name):
    if os.path.exists(folder_name) and os.path.isdir(folder_name):
        shutil.rmtree(folder_name)
    os.makedirs(folder_name, exist_ok=True)

def interpolate_labels(data_array, nb_track_frames_min):
        # 创建原始时间轴
        original_time = np.arange(len(data_array))
        # 创建新的时间轴
        new_time = np.linspace(0, len(data_array) - 1, nb_track_frames_min)
        # 对每个维度进行插值
        interpolated_data = np.zeros((nb_track_frames_min, data_array.shape[1]))
        for i in range(data_array.shape[1]):
            f = interpolate.interp1d(original_time, data_array[:, i], kind='cubic', fill_value="extrapolate")
            interpolated_data[:, i] = f(new_time)
        return interpolated_data