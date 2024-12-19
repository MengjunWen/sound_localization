import os
import json
import wave
import requests
import socket
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
from logger import Logger
import asyncio

class AudioRecorders:
    def __init__(self, output_directory, logger: Logger):
        self.output_directory = output_directory
        self.list_of_esp32 = []
        self.bin_download_folder = os.path.join(self.output_directory, "audio_raw_files")
        self.logger = logger
        os.makedirs(self.bin_download_folder, exist_ok=True)

    async def discover_devices(self, expected_count, timeout=10):
        while True:
            zeroconf = Zeroconf()
            browser = ServiceBrowser(zeroconf, "_http._tcp.local.", handlers=[self._on_service_state_change])
            print("Discovering ESP32 devices...")

            try:
                for _ in range(timeout):
                    if len(self.list_of_esp32) >= expected_count:
                        break
                    await asyncio.sleep(1)
            finally:
                zeroconf.close()

            if len(self.list_of_esp32) >= expected_count:
                print(f"All {expected_count} devices discovered.")
                break  # 找到期望数量设备，退出循环
            else:
                print(f"Only {len(self.list_of_esp32)} devices discovered. Retrying...")

    def _on_service_state_change(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Added and "ESP32_Audio_Device" in name:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                ip = socket.inet_ntoa(info.addresses[0])
                if ip not in self.list_of_esp32:
                    self.list_of_esp32.append(ip)
                    print(f"Discovered device: {ip}")

    def start_tcp(self):
        for ip in self.list_of_esp32:
            url = f"http://{ip}/start"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print(f"Recording started successfully on {ip}")
                    self.logger.log_timestamp(f'audio_start_{ip}')
                else:
                    print(f"Failed to start recording on {ip}")
            except requests.RequestException as e:
                print(f"Error connecting to {ip}: {e}")

    def stop_tcp(self):
        for ip in self.list_of_esp32:
            url = f"http://{ip}/stop"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    self.logger.log_timestamp(f'audio_stop_{ip}')
                else:
                    print(f"Failed to stop recording on {ip}")
            except requests.RequestException as e:
                print(f"Error stopping recording on {ip}: {e}")

    def list_recordings(self, device_ip):
        url = f"http://{device_ip}/list"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return json.loads(response.text)
            else:
                print(f"Failed to retrieve recording list from {device_ip}")
                return None
        except requests.RequestException as e:
            print(f"Error connecting to {device_ip} for listing recordings: {e}")
            return None

    def download_latest_recording(self, device_ip):
        recordings = self.list_recordings(device_ip)
        if not recordings:
            print(f"No recordings found on {device_ip}")
            return

        recordings.sort()
        latest = next((rec for rec in reversed(recordings) if rec.endswith('.bin')), None)

        if latest:
            sanitized_ip = device_ip.replace('.', '')
            download_name = f"{sanitized_ip}_{latest}"
            url = f"http://{device_ip}/{latest}"

            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    file_path = os.path.join(self.bin_download_folder, download_name)

                    with open(file_path, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=4096):
                            file.write(chunk)

                    print(f"Downloaded {latest} from {device_ip} as {download_name}")

                    # 转换二进制文件到WAV
                    audio_wav_folder = os.path.join(self.output_directory, "audio_wav_files")
                    os.makedirs(audio_wav_folder, exist_ok=True)

                    bin_path = file_path
                    self.convert_bin_to_wav(bin_path, audio_wav_folder)

                else:
                    print(f"Failed to download {latest} from {device_ip}")
            except requests.RequestException as e:
                print(f"Error downloading {latest} from {device_ip}: {e}")

    def convert_bin_to_wav(self, bin_path, output_dir):
        try:
            # 获取文件名，不包括扩展名
            ip_mapping = {
                "17221159": "1",
                "17221170": "2",
                "17221157": "3",
                "17221172": "4",
            }
            filename = os.path.basename(bin_path).replace(".bin", "")

            # 提取 IP 地址和剩余部分
            parts = filename.split("_")
            ip_address = parts[0]
            other_part = parts[-1]

            # 替换 IP 为对应序号
            if ip_address in ip_mapping:
                new_filename = f"{ip_mapping[ip_address]}_{other_part}"
            else:
                raise ValueError(f"IP  {ip_address} not found")

            # 确定输出路径
            output_path = os.path.join(output_dir, f"{new_filename}.wav")

            # 确保目标文件夹存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 读取二进制文件数据
            with open(bin_path, 'rb') as file:
                binary_data = file.read()

            # 参数定义：立体声、PCM 16位、采样率 44.1 kHz
            channels = 2
            sample_width = 2
            frame_rate = 44100

            # 创建WAV文件
            with wave.open(output_path, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(frame_rate)
                wav_file.writeframes(binary_data)

            print(f"WAV file created at {output_path}")

        except Exception as e:
            print(f"Failed to convert {bin_path} to WAV: {e}")
