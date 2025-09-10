import subprocess
import os

def wav_to_sensevoice_16k(in_wav: str, out_wav: str = None) -> str:
    """
    把任意 WAV/音频文件转码为 16 kHz 单声道 16-bit PCM WAV，
    返回输出文件路径。
    """
    in_wav = os.path.abspath(in_wav)
    out_wav = out_wav or os.path.splitext(in_wav)[0] + '_16k.wav'

    cmd = [
        'ffmpeg', '-y',
        '-i', in_wav,
        '-ar', '16000',
        '-ac', '1',
        '-sample_fmt', 's16',
        out_wav
    ]

    # 运行并捕获日志
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_wav


if __name__ == '__main__':
    # 测试：把当前目录下的 test2.wav 转成 fixed.wav
    out = wav_to_sensevoice_16k('test5.wav', 'fixed.wav')
    print('转码完成 ->', out)