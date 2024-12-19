
from datetime import datetime
import time
import numpy as np
from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange

from experiment_manager import ExperimentManager

from audio_recorder import AudioRecorders
from logger import Logger

import asyncio

async def main():
    exp_manager = ExperimentManager()  # 创建实验文件夹管理器
    exp_folder = exp_manager.get_exp_folder()
    logger = Logger(exp_folder)

    audio_recorder = AudioRecorders(exp_folder, logger)

    await audio_recorder.discover_devices(expected_count=4)

    if len(audio_recorder.list_of_esp32) == 4:
        print("All devices discovered, starting audio recording...")
        await asyncio.sleep(2)
        audio_recorder.start_tcp()
        await asyncio.sleep(12)

        audio_recorder.stop_tcp()

        for ip in audio_recorder.list_of_esp32:
            audio_recorder.download_latest_recording(ip)

    print('Finished')

# 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())
