import os
import json
from model import SenseVoiceSmall
from funasr.utils.postprocess_utils import rich_transcription_postprocess
#the file is to produce the listening.txt file
# 假设你已经定义了 VoiceTranscriptionPipeline 类（如上）
import os
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
import tempfile
import shutil
import os
import sys

# 尝试导入依赖，若缺失给出提示

import torch


class VoiceTranscriptionPipeline:
    def __init__(self, model_dir="iic/SenseVoiceSmall", device="cuda:0"):
        self.model, self.kwargs = SenseVoiceSmall.from_pretrained(
            model=model_dir, device=device)
        self.model.eval()
        self.device = device

    def transcribe_audio(self, audio_path, language="auto", use_itn=False,
                         ban_emo_unk=False, output_timestamp=False):
        """基础的短音频转录方法"""
        res = self.model.inference(
            data_in=audio_path,
            language=language,
            use_itn=use_itn,
            ban_emo_unk=ban_emo_unk,
            output_timestamp=output_timestamp,
            **self.kwargs
        )
        text = rich_transcription_postprocess(res[0][0]["text"])
        if output_timestamp:
            return text, res[0][0]["timestamp"]
        return text

    def split_audio_file(self, audio_path, chunk_duration=60, overlap=2, output_dir=None):
        """
        将长音频文件切割成小文件
        """
        # 创建输出目录
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="audio_chunks_")
        else:
            os.makedirs(output_dir, exist_ok=True)
        
        # 加载音频
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        total_duration = len(y) / sr
        
        # 计算切片参数
        chunk_samples = chunk_duration * sr
        overlap_samples = overlap * sr
        step_samples = chunk_samples - overlap_samples
        
        chunks_info = []
        base_name = Path(audio_path).stem
        
        for i, start in enumerate(range(0, len(y), step_samples)):
            end = min(start + chunk_samples, len(y))
            chunk = y[start:end]
            
            # 计算时间信息
            start_time = start / sr
            end_time = end / sr
            
            # 保存切片文件
            chunk_filename = f"{base_name}_chunk_{i:04d}.wav"
            chunk_path = os.path.join(output_dir, chunk_filename)
            sf.write(chunk_path, chunk, sr)
            
            chunks_info.append({
                'path': chunk_path,
                'index': i,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time
            })
            
            print(f"创建切片 {i+1}: {start_time:.1f}s - {end_time:.1f}s ({chunk_path})")
            
            if end >= len(y):
                break
        
        print(f"音频切割完成: 共{len(chunks_info)}个切片, 总时长{total_duration:.1f}秒")
        return chunks_info, output_dir

    def transcribe_long_audio_segmented(self, audio_path, chunk_duration=60, overlap=2, 
                                      language="auto", use_itn=True, output_timestamp=True,
                                      keep_chunks=False, output_dir=None):
        """
        分段转录长音频文件
        """
        print(f"开始处理长音频: {audio_path}")
        
        # 切割音频文件
        chunks_info, chunks_dir = self.split_audio_file(
            audio_path, chunk_duration, overlap, output_dir)
        
        all_results = []
        full_text = ""
        full_timestamps = []
        
        try:
            # 分段处理每个切片
            for chunk_info in chunks_info:
                print(f"处理切片 {chunk_info['index']+1}/{len(chunks_info)}: "
                      f"{chunk_info['start_time']:.1f}s - {chunk_info['end_time']:.1f}s")
                
                try:
                    # 直接转录，不进行重叠处理
                    if output_timestamp:
                        text, timestamps = self.transcribe_audio(
                            audio_path=chunk_info['path'],
                            language=language,
                            use_itn=use_itn,
                            output_timestamp=True
                        )
                        # 调整时间戳
                        adjusted_timestamps = self._adjust_timestamps(
                            timestamps, chunk_info['start_time'])
                        full_timestamps.extend(adjusted_timestamps)
                    else:
                        text = self.transcribe_audio(
                            audio_path=chunk_info['path'],
                            language=language,
                            use_itn=use_itn,
                            output_timestamp=False
                        )
                    
                    # 简单的文本拼接，不进行复杂的重叠处理
                    processed_text = text
                    
                    chunk_result = {
                        'chunk_index': chunk_info['index'],
                        'start_time': chunk_info['start_time'],
                        'end_time': chunk_info['end_time'],
                        'text': text,
                        'processed_text': processed_text,
                        'file_path': chunk_info['path']
                    }
                    
                    all_results.append(chunk_result)
                    full_text += " " + processed_text if full_text else processed_text
                    
                    print(f"切片 {chunk_info['index']+1} 完成: {text[:50]}...")
                    
                except Exception as e:
                    print(f"切片 {chunk_info['index']+1} 处理失败: {e}")
                    import traceback
                    print(f"错误详情: {traceback.format_exc()}")
                    
                    # 添加一个空结果以保持顺序
                    all_results.append({
                        'chunk_index': chunk_info['index'],
                        'start_time': chunk_info['start_time'],
                        'end_time': chunk_info['end_time'],
                        'text': '',
                        'processed_text': '',
                        'file_path': chunk_info['path'],
                        'error': str(e)
                    })
            
            # 清理临时文件
            if not keep_chunks:
                if output_dir is None:  # 临时目录
                    shutil.rmtree(chunks_dir)
                else:
                    for chunk_info in chunks_info:
                        if os.path.exists(chunk_info['path']):
                            os.remove(chunk_info['path'])
            
            # 构建最终结果
            result = {
                'full_text': full_text.strip(),
                'chunk_results': all_results,
                'total_chunks': len(chunks_info),
                'audio_duration': chunks_info[-1]['end_time'] if chunks_info else 0
            }
            
            if output_timestamp:
                result['timestamps'] = full_timestamps
            
            print(f"长音频处理完成: 共处理{len(chunks_info)}个切片")
            return result
            
        except Exception as e:
            print(f"长音频处理失败: {e}")
            import traceback
            print(f"错误详情: {traceback.format_exc()}")
            # 确保清理临时文件
            if not keep_chunks and output_dir is None:
                shutil.rmtree(chunks_dir, ignore_errors=True)
            raise e

    def _adjust_timestamps(self, timestamps, offset):
        """调整时间戳偏移"""
        if not timestamps:
            return []
            
        adjusted = []
        for ts in timestamps:
            if isinstance(ts, dict):
                adjusted.append({
                    'start': ts['start'] + offset,
                    'end': ts['end'] + offset,
                    'text': ts['text']
                })
            elif isinstance(ts, (list, tuple)) and len(ts) >= 2:
                adjusted.append([ts[0] + offset, ts[1] + offset] + list(ts[2:]))
            else:
                # 如果时间戳格式未知，直接返回原样
                adjusted.append(ts)
        return adjusted

    def transcribe_long_audio_simple(self, audio_path, chunk_duration=60, 
                                   language="auto", use_itn=True, output_dir=None):
        """
        简化版本的长音频转录，没有重叠处理
        """
        print(f"开始简化处理长音频: {audio_path}")
        
        # 切割音频文件（不重叠）
        chunks_info, chunks_dir = self.split_audio_file(
            audio_path, chunk_duration, overlap=0, output_dir=output_dir)
        
        all_texts = []
        
        try:
            for i, chunk_info in enumerate(chunks_info):
                print(f"处理切片 {i+1}/{len(chunks_info)}")
                
                try:
                    text = self.transcribe_audio(
                        audio_path=chunk_info['path'],
                        language=language,
                        use_itn=use_itn,
                        output_timestamp=False
                    )
                    
                    all_texts.append(text)
                    print(f"切片 {i+1} 完成: {text[:100]}...")
                    
                except Exception as e:
                    print(f"切片 {i+1} 处理失败: {e}")
                    all_texts.append("")
            
            # 合并所有文本
            full_text = " ".join(filter(None, all_texts))
            
            # 清理临时文件
            if output_dir is None:
                shutil.rmtree(chunks_dir)
            else:
                for chunk_info in chunks_info:
                    if os.path.exists(chunk_info['path']):
                        os.remove(chunk_info['path'])
            
            result = {
                'full_text': full_text,
                'total_chunks': len(chunks_info),
                'successful_chunks': len([t for t in all_texts if t])
            }
            
            print(f"简化处理完成: 成功{result['successful_chunks']}/{result['total_chunks']}个切片")
            return result
            
        except Exception as e:
            print(f"简化处理失败: {e}")
            if output_dir is None:
                shutil.rmtree(chunks_dir, ignore_errors=True)
            raise e

    def save_transcription_result(self, result, output_path):
        """保存转录结果到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("完整转录文本:\n")
            f.write("=" * 50 + "\n")
            f.write(result.get('full_text', '') + "\n\n")
            
            if 'timestamps' in result:
                f.write("时间戳信息:\n")
                f.write("=" * 50 + "\n")
                for ts in result['timestamps']:
                    if isinstance(ts, dict):
                        f.write(f"[{ts['start']:.1f}s - {ts['end']:.1f}s]: {ts['text']}\n")
                    else:
                        f.write(f"{ts}\n")
                f.write("\n")
            
            if 'chunk_results' in result:
                f.write("分段详细信息:\n")
                f.write("=" * 50 + "\n")
                for chunk in result['chunk_results']:
                    f.write(f"切片 {chunk['chunk_index']+1}: "
                           f"{chunk['start_time']:.1f}s - {chunk['end_time']:.1f}s\n")
                    f.write(f"原始文本: {chunk['text']}\n")
                    if 'error' in chunk:
                        f.write(f"错误: {chunk['error']}\n")
                    f.write("-" * 30 + "\n")


def main():
    base_dir = "data/task2"
    tpo_folders = [f"TPO{i}" for i in range(55, 56)]  # TPO66 到 TPO75

    # 初始化转写器
    pipeline = VoiceTranscriptionPipeline()

    for folder in tpo_folders:
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            print(f"⚠️  跳过（文件夹不存在）: {folder}")
            continue

        # 查找 audio.m4a 或 audio.mp3
        audio_path = None
        for ext in [".m4a", ".mp3"]:
            candidate = os.path.join(folder_path, f"audio{ext}")
            if os.path.isfile(candidate):
                audio_path = candidate
                break

        output_path = os.path.join(folder_path, "listening.txt")

        # 始终覆盖写入 listening.txt
        with open(output_path, "w", encoding="utf-8") as f_out:
            if not audio_path:
                msg = "[ERROR] 未找到 audio.m4a 或 audio.mp3\n"
                print(f"❌ {folder}: 音频缺失")
                f_out.write(msg)
                continue

            print(f"🔊 正在处理: {folder} ({os.path.basename(audio_path)})")
            
            try:
                # 获取音频时长
                duration = get_audio_duration(audio_path)
                print(f"    ⏱️  音频时长: {duration:.1f}秒 ({duration/60:.1f}分钟)")
                
                # 以3分钟（180秒）为分割点自动选择模式
                if duration <= 180:  # 3分钟及以下使用直接转录
                    print("    🎯 使用直接转录模式（≤3分钟）")
                    transcription = pipeline.transcribe_audio(
                        audio_path=audio_path,
                        language="auto",
                        use_itn=True,
                        ban_emo_unk=False,
                        output_timestamp=False
                    )
                    f_out.write(transcription + "\n")
                    print(f"    ✅ 直接转录成功: {folder}")
                    
                else:  # 超过3分钟使用分段转录
                    print(f"    🎯 使用分段转录模式（＞3分钟）")
                    result = pipeline.transcribe_long_audio_simple(
                        audio_path=audio_path,
                        chunk_duration=60,  # 每段60秒
                        language="auto",
                        use_itn=True
                    )
                    
                    if result['full_text']:
                        f_out.write(result['full_text'] + "\n")
                        print(f"    ✅ 分段转录成功: {folder} (成功{result['successful_chunks']}/{result['total_chunks']}个片段)")
                    else:
                        error_msg = f"[ERROR] 分段转录失败，所有片段均未成功\n"
                        f_out.write(error_msg)
                        print(f"    ❌ 分段转录失败: {folder}")
                        
            except Exception as e:
                error_msg = f"[ERROR] 处理失败: {str(e)}\n"
                print(f"❌ 失败: {folder} - {e}")
                f_out.write(error_msg)

    print("\n🎉 所有任务完成！每个 TPO 文件夹下已生成 listening.txt")


def get_audio_duration(audio_path):
    """获取音频文件时长（秒）"""
    try:
        # 使用librosa获取音频时长
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        duration = len(y) / sr
        return duration
    except Exception as e:
        print(f"    ⚠️  无法获取音频时长: {e}")
        # 如果无法获取时长，根据文件大小估算
        file_size = os.path.getsize(audio_path)
        # 假设是压缩音频，大致估算（这个估算可能不准确，但作为备用方案）
        estimated_duration = file_size / (16 * 1024)  # 粗略估算
        print(f"    📊 使用估算时长: {estimated_duration:.1f}秒")
        return estimated_duration


def main_with_progress():
    """带进度显示和时长检测的版本"""
    base_dir = "data/task4"
    tpo_folders = [f"TPO{i}" for i in range(55, 76)]  # TPO66 到 TPO75
    
    # 初始化转写器
    pipeline = VoiceTranscriptionPipeline()
    
    total = len(tpo_folders)
    success_count = 0
    fail_count = 0
    direct_count = 0
    segmented_count = 0
    
    print(f"🎯 开始处理 {total} 个TPO文件夹...")
    
    for i, folder in enumerate(tpo_folders, 1):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            print(f"[{i}/{total}] ⚠️  跳过（文件夹不存在）: {folder}")
            fail_count += 1
            continue

        # 查找音频文件
        audio_path = None
        for ext in [".m4a", ".mp3"]:
            candidate = os.path.join(folder_path, f"audio{ext}")
            if os.path.isfile(candidate):
                audio_path = candidate
                break

        output_path = os.path.join(folder_path, "listening.txt")

        with open(output_path, "w", encoding="utf-8") as f_out:
            if not audio_path:
                msg = "[ERROR] 未找到 audio.m4a 或 audio.mp3\n"
                print(f"[{i}/{total}] ❌ {folder}: 音频缺失")
                f_out.write(msg)
                fail_count += 1
                continue

            print(f"[{i}/{total}] 🔊 正在处理: {folder}")
            
            try:
                # 获取音频时长
                duration = get_audio_duration(audio_path)
                minutes = duration / 60
                print(f"    ⏱️  音频时长: {duration:.1f}秒 ({minutes:.1f}分钟)")
                
                # 以3分钟为分割点自动选择模式
                if duration <= 180:  # 3分钟及以下
                    print("    🎯 使用直接转录模式（≤3分钟）")
                    transcription = pipeline.transcribe_audio(
                        audio_path=audio_path,
                        language="auto",
                        use_itn=True,
                        ban_emo_unk=False,
                        output_timestamp=False
                    )
                    f_out.write(transcription + "\n")
                    print(f"    ✅ 直接转录成功")
                    success_count += 1
                    direct_count += 1
                    
                else:  # 超过3分钟
                    print(f"    🎯 使用分段转录模式（＞3分钟）")
                    # 根据时长动态调整分块大小
                    if duration > 600:  # 超过10分钟，使用更小的分块
                        chunk_duration = 45
                        print(f"    🔧 长音频检测，使用分块大小: {chunk_duration}秒")
                    else:
                        chunk_duration = 60
                    
                    result = pipeline.transcribe_long_audio_simple(
                        audio_path=audio_path,
                        chunk_duration=chunk_duration,
                        language="auto",
                        use_itn=True
                    )
                    
                    if result['full_text']:
                        f_out.write(result['full_text'] + "\n")
                        print(f"    ✅ 分段转录成功 (成功{result['successful_chunks']}/{result['total_chunks']}个片段)")
                        success_count += 1
                        segmented_count += 1
                    else:
                        error_msg = f"[ERROR] 分段转录失败\n"
                        f_out.write(error_msg)
                        print(f"    ❌ 分段转录失败")
                        fail_count += 1
                            
            except Exception as e:
                error_msg = f"[ERROR] 处理失败: {str(e)}\n"
                print(f"    ❌ 失败: {e}")
                f_out.write(error_msg)
                fail_count += 1

    print(f"\n🎉 所有任务完成！")
    print(f"📊 统计:")
    print(f"   成功: {success_count}/{total}")
    print(f"   失败: {fail_count}/{total}")
    print(f"   直接转录: {direct_count} 个")
    print(f"   分段转录: {segmented_count} 个")


if __name__ == "__main__":
    # 使用带进度显示的版本
    main_with_progress()