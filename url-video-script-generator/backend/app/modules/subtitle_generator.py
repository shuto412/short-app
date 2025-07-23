from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SubtitleGenerator:
    def __init__(self):
        pass
    
    def generate_srt(self, script: Dict) -> str:
        """
        スクリプトからSRT字幕ファイルを生成
        
        Args:
            script: 台本データ
            
        Returns:
            SRT形式の字幕文字列
        """
        try:
            logger.info("Generating SRT subtitles")
            
            srt_content = []
            current_time = 0.0
            
            for i, scene in enumerate(script["scenes"], 1):
                start_time = current_time
                end_time = current_time + scene["duration"]
                
                # SRT時間形式に変換
                start_str = self._format_time(start_time)
                end_str = self._format_time(end_time)
                
                # SRT字幕エントリを作成
                srt_content.append(str(i))
                srt_content.append(f"{start_str} --> {end_str}")
                srt_content.append(scene["text"])
                srt_content.append("")  # 空行
                
                current_time = end_time
            
            result = "\n".join(srt_content)
            logger.info(f"Generated SRT with {len(script['scenes'])} subtitles")
            return result
            
        except Exception as e:
            logger.error(f"SRT generation failed: {str(e)}")
            return self._generate_fallback_srt()
    
    def generate_vtt(self, script: Dict) -> str:
        """
        スクリプトからWebVTT字幕ファイルを生成
        
        Args:
            script: 台本データ
            
        Returns:
            WebVTT形式の字幕文字列
        """
        try:
            logger.info("Generating WebVTT subtitles")
            
            vtt_content = ["WEBVTT", ""]
            current_time = 0.0
            
            for scene in script["scenes"]:
                start_time = current_time
                end_time = current_time + scene["duration"]
                
                # WebVTT時間形式に変換
                start_str = self._format_time_vtt(start_time)
                end_str = self._format_time_vtt(end_time)
                
                # WebVTT字幕エントリを作成
                vtt_content.append(f"{start_str} --> {end_str}")
                vtt_content.append(scene["text"])
                vtt_content.append("")  # 空行
                
                current_time = end_time
            
            result = "\n".join(vtt_content)
            logger.info(f"Generated WebVTT with {len(script['scenes'])} subtitles")
            return result
            
        except Exception as e:
            logger.error(f"WebVTT generation failed: {str(e)}")
            return "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\n字幕生成に失敗しました\n"
    
    def generate_with_timing_adjustment(self, script: Dict, audio_duration: Optional[float] = None) -> str:
        """
        音声の実際の長さに合わせて字幕タイミングを調整
        
        Args:
            script: 台本データ
            audio_duration: 実際の音声ファイルの長さ（秒）
            
        Returns:
            タイミング調整済みのSRT字幕
        """
        try:
            if audio_duration:
                # 音声の実際の長さに合わせて調整
                script_total_duration = sum(scene["duration"] for scene in script["scenes"])
                if script_total_duration != audio_duration:
                    ratio = audio_duration / script_total_duration
                    adjusted_script = self._adjust_scene_timings(script, ratio)
                    return self.generate_srt(adjusted_script)
            
            return self.generate_srt(script)
            
        except Exception as e:
            logger.error(f"Timing adjustment failed: {str(e)}")
            return self.generate_srt(script)
    
    def split_long_subtitles(self, script: Dict, max_chars: int = 42) -> Dict:
        """
        長い字幕を適切な長さに分割
        
        Args:
            script: 台本データ
            max_chars: 1行あたりの最大文字数
            
        Returns:
            分割処理済みの台本データ
        """
        try:
            modified_scenes = []
            
            for scene in script["scenes"]:
                text = scene["text"]
                
                if len(text) <= max_chars:
                    # 短い場合はそのまま
                    modified_scenes.append(scene)
                else:
                    # 長い場合は分割
                    split_scenes = self._split_scene_text(scene, max_chars)
                    modified_scenes.extend(split_scenes)
            
            # 新しいスクリプトデータを作成
            new_script = script.copy()
            new_script["scenes"] = modified_scenes
            
            return new_script
            
        except Exception as e:
            logger.error(f"Subtitle splitting failed: {str(e)}")
            return script
    
    def _format_time(self, seconds: float) -> str:
        """秒数をSRT時間形式に変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        millisecs = int((secs % 1) * 1000)
        secs = int(secs)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _format_time_vtt(self, seconds: float) -> str:
        """秒数をWebVTT時間形式に変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        millisecs = int((secs % 1) * 1000)
        secs = int(secs)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
    
    def _adjust_scene_timings(self, script: Dict, ratio: float) -> Dict:
        """シーンのタイミングを比率に従って調整"""
        adjusted_script = script.copy()
        adjusted_scenes = []
        
        for scene in script["scenes"]:
            adjusted_scene = scene.copy()
            adjusted_scene["duration"] = scene["duration"] * ratio
            adjusted_scenes.append(adjusted_scene)
        
        adjusted_script["scenes"] = adjusted_scenes
        return adjusted_script
    
    def _split_scene_text(self, scene: Dict, max_chars: int) -> List[Dict]:
        """長いシーンテキストを複数のシーンに分割"""
        text = scene["text"]
        words = text.split()
        
        split_scenes = []
        current_text = ""
        scene_duration = scene["duration"]
        words_per_scene = []
        
        # 文字数制限に基づいて分割
        for word in words:
            if len(current_text + " " + word) <= max_chars:
                current_text += " " + word if current_text else word
            else:
                if current_text:
                    words_per_scene.append(current_text)
                current_text = word
        
        if current_text:
            words_per_scene.append(current_text)
        
        # 分割されたテキストに時間を割り当て
        if len(words_per_scene) > 1:
            duration_per_split = scene_duration / len(words_per_scene)
            
            for i, text_part in enumerate(words_per_scene):
                split_scene = scene.copy()
                split_scene["text"] = text_part
                split_scene["duration"] = duration_per_split
                split_scene["scene_id"] = f"{scene['scene_id']}-{i+1}"
                split_scenes.append(split_scene)
        else:
            split_scenes.append(scene)
        
        return split_scenes
    
    def _generate_fallback_srt(self) -> str:
        """フォールバック字幕を生成"""
        return """1
00:00:00,000 --> 00:00:05,000
字幕生成に失敗しました

2
00:00:05,000 --> 00:00:10,000
システムエラーが発生しました
"""
    
    def validate_subtitle_timing(self, subtitle_content: str) -> bool:
        """字幕のタイミングが正しいかチェック"""
        try:
            lines = subtitle_content.split('\n')
            previous_end_time = 0.0
            
            for i, line in enumerate(lines):
                if '-->' in line:
                    # 時間行を解析
                    time_parts = line.split(' --> ')
                    if len(time_parts) == 2:
                        start_time = self._parse_srt_time(time_parts[0])
                        end_time = self._parse_srt_time(time_parts[1])
                        
                        # タイミングの検証
                        if start_time >= end_time:
                            return False
                        if start_time < previous_end_time:
                            return False
                        
                        previous_end_time = end_time
            
            return True
            
        except Exception:
            return False
    
    def _parse_srt_time(self, time_str: str) -> float:
        """SRT時間文字列を秒数に変換"""
        # "00:01:30,500" -> 90.5
        time_str = time_str.strip()
        time_part, ms_part = time_str.split(',')
        hours, minutes, seconds = map(int, time_part.split(':'))
        
        total_seconds = hours * 3600 + minutes * 60 + seconds + int(ms_part) / 1000
        return total_seconds
