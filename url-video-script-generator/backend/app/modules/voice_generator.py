import aiohttp
from typing import Dict, List, Optional
import logging
import asyncio
from app.config import settings
from app.models.voice import VoiceActor, VoicePrompt, VoiceParameters

logger = logging.getLogger(__name__)

class VoiceGenerator:
    def __init__(self):
        self.api_key = settings.NIJIVOICE_API_KEY
        self.base_url = "https://api.nijivoice.com/api/platform/v1"
        self.session = None
        
    async def get_voice_actors(self) -> List[Dict]:
        """利用可能なボイスアクター一覧を取得"""
        if not self.api_key or self.api_key == "your_key_here":
            logger.warning("Nijivoice API key not configured, returning mock data")
            return self._get_mock_voice_actors()
        
        try:
            # SSL証明書検証を無効化（開発環境用）
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    f"{self.base_url}/voice-actors",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Retrieved {len(data)} voice actors")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get voice actors: {response.status} - {error_text}")
                        return self._get_mock_voice_actors()
                        
        except Exception as e:
            logger.error(f"Voice actors API error: {str(e)}")
            return self._get_mock_voice_actors()
    
    async def generate(self, voice_actor_id: str, text: str, options: Optional[Dict] = None) -> bytes:
        """音声を生成"""
        if not self.api_key or self.api_key == "your_key_here":
            logger.warning("Nijivoice API key not configured, returning mock audio")
            return self._generate_mock_audio(text)
        
        try:
            # SSL証明書検証を無効化（開発環境用）
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # デフォルトパラメータ
                data = {
                    "text": text,
                    "format": "wav",
                    "speed": 1.0,
                    "volume": 1.0,
                    "pitch": 0,
                    "pauseLength": 0.8,
                    "pauseLengthSentence": 1.0,
                    "intonation": 1.0
                }
                
                # オプションパラメータがあれば上書き
                if options:
                    data.update(options)
                
                async with session.post(
                    f"{self.base_url}/voice-actors/{voice_actor_id}/generate-voice",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info(f"Generated audio for text: {text[:50]}...")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Voice generation failed: {response.status} - {error_text}")
                        return self._generate_mock_audio(text)
                        
        except Exception as e:
            logger.error(f"Voice generation error: {str(e)}")
            return self._generate_mock_audio(text)
    
    async def generate_from_script(self, voice_prompt: Dict) -> bytes:
        """スクリプトから音声を生成（複数セグメントを結合）"""
        try:
            voice_actor_id = voice_prompt["api_settings"]["voice_actor_id"]
            audio_segments = []
            
            logger.info(f"Generating audio for {len(voice_prompt['segments'])} segments")
            
            for segment in voice_prompt["segments"]:
                try:
                    audio_data = await self.generate(
                        voice_actor_id=voice_actor_id,
                        text=segment["text"],
                        options=segment.get("parameters", {})
                    )
                    audio_segments.append(audio_data)
                except Exception as e:
                    logger.error(f"Failed to generate segment {segment['segment_id']}: {str(e)}")
                    # 失敗したセグメントは無音で代替
                    audio_segments.append(self._generate_silence(5.0))
            
            # 音声セグメントを結合
            combined_audio = self._combine_audio_segments(audio_segments)
            logger.info(f"Combined audio generated: {len(combined_audio)} bytes")
            return combined_audio
            
        except Exception as e:
            logger.error(f"Script audio generation failed: {str(e)}")
            return self._generate_mock_audio("音声生成に失敗しました")
    
    def create_voice_prompt(self, script: Dict, voice_actor_id: str) -> Dict:
        """スクリプトから音声生成用プロンプトを作成"""
        segments = []
        current_time = 0.0
        
        for scene in script["scenes"]:
            segment = {
                "segment_id": scene["scene_id"],
                "text": scene["text"],
                "start_time": current_time,
                "end_time": current_time + scene["duration"],
                "parameters": {
                    "speed": scene.get("voice_settings", {}).get("speed", 1.0),
                    "pitch": scene.get("voice_settings", {}).get("pitch", 0),
                    "volume": 1.0,
                    "pauseLength": 0.8,
                    "pauseLengthSentence": 1.0,
                    "intonation": 1.0
                }
            }
            segments.append(segment)
            current_time += scene["duration"]
        
        return {
            "api_settings": {
                "service": "nijivoice",
                "voice_actor_id": voice_actor_id,
                "output_format": "wav"
            },
            "segments": segments
        }
    
    async def estimate_duration(self, text: str) -> float:
        """テキストから音声の長さを推定"""
        # 日本語の平均読み上げ速度: 約300文字/分
        chars_per_minute = 300
        chars_per_second = chars_per_minute / 60
        
        # 文字数から推定時間を計算
        char_count = len(text)
        estimated_duration = char_count / chars_per_second
        
        # 最小1秒、最大300秒でクランプ
        return max(1.0, min(300.0, estimated_duration))
    
    def _get_mock_voice_actors(self) -> List[Dict]:
        """モックボイスアクターデータ"""
        return [
            {
                "id": "mock-voice-001",
                "name": "サンプル女性声優",
                "description": "明るく親しみやすい女性の声",
                "gender": "female",
                "age_range": "young"
            },
            {
                "id": "mock-voice-002", 
                "name": "サンプル男性声優",
                "description": "落ち着いた男性の声",
                "gender": "male",
                "age_range": "adult"
            }
        ]
    
    def _generate_mock_audio(self, text: str) -> bytes:
        """モック音声データを生成"""
        # 簡易的なWAVヘッダーを作成（44バイト）
        wav_header = b'RIFF'
        wav_header += (44 + 8000).to_bytes(4, 'little')  # ファイルサイズ
        wav_header += b'WAVE'
        wav_header += b'fmt '
        wav_header += (16).to_bytes(4, 'little')  # fmtチャンクサイズ
        wav_header += (1).to_bytes(2, 'little')   # PCM
        wav_header += (1).to_bytes(2, 'little')   # モノラル
        wav_header += (8000).to_bytes(4, 'little') # サンプリング周波数
        wav_header += (8000).to_bytes(4, 'little') # バイト/秒
        wav_header += (1).to_bytes(2, 'little')   # ブロックアライン
        wav_header += (8).to_bytes(2, 'little')   # ビット/サンプル
        wav_header += b'data'
        wav_header += (8000).to_bytes(4, 'little') # データサイズ
        
        # 1秒分の無音データ（8000バイト）
        audio_data = b'\x80' * 8000
        
        return wav_header + audio_data
    
    def _generate_silence(self, duration: float) -> bytes:
        """指定時間の無音データを生成"""
        sample_rate = 8000
        silence_bytes = int(duration * sample_rate)
        
        # WAVヘッダー
        wav_header = b'RIFF'
        wav_header += (44 + silence_bytes).to_bytes(4, 'little')
        wav_header += b'WAVE'
        wav_header += b'fmt '
        wav_header += (16).to_bytes(4, 'little')
        wav_header += (1).to_bytes(2, 'little')   # PCM
        wav_header += (1).to_bytes(2, 'little')   # モノラル
        wav_header += sample_rate.to_bytes(4, 'little')
        wav_header += sample_rate.to_bytes(4, 'little')
        wav_header += (1).to_bytes(2, 'little')
        wav_header += (8).to_bytes(2, 'little')
        wav_header += b'data'
        wav_header += silence_bytes.to_bytes(4, 'little')
        
        # 無音データ
        silence_data = b'\x80' * silence_bytes
        
        return wav_header + silence_data
    
    def _combine_audio_segments(self, segments: List[bytes]) -> bytes:
        """音声セグメントを結合（簡易版）"""
        if not segments:
            return self._generate_silence(1.0)
        
        # 最初のセグメントのヘッダーを基準とする
        if len(segments) == 1:
            return segments[0]
        
        # 複数セグメントがある場合は、データ部分のみを結合
        combined_data = b''
        total_data_size = 0
        
        for segment in segments:
            if len(segment) > 44:  # WAVヘッダーサイズチェック
                data_part = segment[44:]  # ヘッダー以降のデータ
                combined_data += data_part
                total_data_size += len(data_part)
        
        # 新しいWAVヘッダーを作成
        wav_header = b'RIFF'
        wav_header += (44 + total_data_size).to_bytes(4, 'little')
        wav_header += b'WAVE'
        wav_header += b'fmt '
        wav_header += (16).to_bytes(4, 'little')
        wav_header += (1).to_bytes(2, 'little')   # PCM
        wav_header += (1).to_bytes(2, 'little')   # モノラル
        wav_header += (8000).to_bytes(4, 'little') # サンプリング周波数
        wav_header += (8000).to_bytes(4, 'little') # バイト/秒
        wav_header += (1).to_bytes(2, 'little')   # ブロックアライン
        wav_header += (8).to_bytes(2, 'little')   # ビット/サンプル
        wav_header += b'data'
        wav_header += total_data_size.to_bytes(4, 'little')
        
        return wav_header + combined_data
