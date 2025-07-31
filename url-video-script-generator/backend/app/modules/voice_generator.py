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
        
        # デバッグ情報を出力
        print(f"\n🔧 VoiceGenerator 初期化:")
        if self.api_key:
            if self.api_key == "your_key_here":
                print("  ⚠️  APIキーがデフォルト値のため、モックモードで動作します")
            else:
                masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "設定済み"
                print(f"  ✅ APIキー読み込み成功: {masked_key}")
                print(f"  🌐 Base URL: {self.base_url}")
        else:
            print("  ❌ APIキーが読み込まれませんでした")
        
    async def get_voice_actors(self) -> List[Dict]:
        """利用可能なボイスアクター一覧を取得"""
        if not self.api_key or self.api_key == "your_key_here":
            logger.warning("Nijivoice API key not configured, returning mock data")
            return self._get_mock_voice_actors()
        
        try:
            # SSL証明書検証を無効化（開発環境用）
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                
                # 複数の認証パターンを試行
                auth_patterns = [
                    # パターン1: X-API-Key ヘッダー（最も一般的）
                    {
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    # パターン2: Authorization ヘッダー（API Key直接）
                    {
                        "Authorization": self.api_key,
                        "Content-Type": "application/json"
                    },
                    # パターン3: Bearer認証（現在のパターン）
                    {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    # パターン4: Nijivoice専用ヘッダー
                    {
                        "Nijivoice-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    }
                ]
                
                for i, headers in enumerate(auth_patterns, 1):
                    
                    try:
                        async with session.get(
                            f"{self.base_url}/voice-actors",
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"  ✅ 認証パターン{i}で成功! ボイスアクター取得完了")
                                
                                # レスポンス構造を詳しくログ出力
                                logger.info(f"  📊 レスポンス詳細: 型={type(data)}, キー={list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                                
                                # Nijivoice APIのレスポンス構造に対応
                                voice_actors = None
                                if isinstance(data, list):
                                    # 直接配列の場合
                                    voice_actors = data
                                    logger.info(f"  📋 直接配列形式: {len(voice_actors)}件")
                                elif isinstance(data, dict):
                                    # 辞書形式の場合、複数のキーパターンをチェック（キャメルケース対応）
                                    for key in ["voiceActors", "voice_actors", "data", "actors", "voices"]:
                                        if key in data and isinstance(data[key], list):
                                            voice_actors = data[key]
                                            logger.info(f"  📋 辞書形式（キー: {key}）: {len(voice_actors)}件")
                                            break
                                    
                                    if voice_actors is None:
                                        logger.warning(f"  ⚠️ 辞書にボイスアクター配列が見つからない: {list(data.keys())}")
                                        logger.info(f"  🔍 最初のキーの値をサンプル表示: {str(list(data.values())[0])[:200] if data.values() else 'なし'}")
                                
                                if voice_actors and len(voice_actors) > 0:
                                    logger.info(f"  🎯 最初のボイスアクター: {voice_actors[0].get('name', 'N/A')} (ID: {voice_actors[0].get('id', 'N/A')})")
                                    # 成功したパターンを保存
                                    self._successful_auth_pattern = headers
                                    return voice_actors
                                else:
                                    logger.warning(f"  ⚠️ ボイスアクターデータが見つからない、モックデータを使用")
                                    return self._get_mock_voice_actors()
                            else:
                                pass  # 失敗時の詳細ログは出力しない
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"  ⏱️ パターン{i}: タイムアウト")
                    except Exception as e:
                        logger.error(f"  💥 パターン{i}: 予期しない例外 - {type(e).__name__}: {e}")
                        import traceback
                        logger.error(f"  📋 トレースバック: {traceback.format_exc()}")
                
                # 全パターン失敗
                logger.error("🔄 全ての認証パターンが失敗しました。モックデータを使用します。")
                logger.error(f"使用したAPIキー: {self.api_key[:10]}...")
                logger.error(f"エンドポイントURL: {self.base_url}/voice-actors")
                return self._get_mock_voice_actors()
                        
        except Exception as e:
            logger.error(f"Voice actors API error: {str(e)}")
            logger.warning("🔄 予期しないエラーのため、モックデータを使用します。")
            return self._get_mock_voice_actors()
    
    async def generate(self, voice_actor_id: str, text: str, options: Optional[Dict] = None) -> bytes:
        """音声を生成"""
        if not self.api_key or self.api_key == "your_key_here":
            logger.warning("Nijivoice API key not configured, returning mock audio")
            return self._generate_mock_audio(text)
        
        # 成功した認証パターンがあるかチェック
        headers = getattr(self, '_successful_auth_pattern', {
            "X-API-Key": self.api_key,  # デフォルトでX-API-Keyを使用
            "Content-Type": "application/json"
        })
        
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as session:
                
                # デフォルトパラメータ（Nijivoice API公式仕様準拠）
                data = {
                    "script": text,  # 公式仕様: "text"ではなく"script"を使用
                    "format": "wav",
                    "speed": "1.0",              # 公式仕様: 文字列として設定
                    "emotionalLevel": "0.1",     # 公式仕様: 感情レベル（0〜1.5）
                    "soundDuration": "0.1"       # 公式仕様: 音素の長さ（0〜1.7）
                }
                
                # オプションパラメータがあれば上書き（数値を文字列に変換）
                if options:
                    # Nijivoice APIは数値パラメータを文字列で要求するため変換
                    string_options = {}
                    for key, value in options.items():
                        if isinstance(value, (int, float)):
                            string_options[key] = str(value)
                        else:
                            string_options[key] = value
                    data.update(string_options)
                
                logger.info(f"🎵 音声生成 API 呼び出し: {voice_actor_id} - {text[:30]}...")
                logger.debug(f"📊 最終パラメータ: {data}")
                
                async with session.post(
                    f"{self.base_url}/voice-actors/{voice_actor_id}/generate-voice",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)  # 30秒でタイムアウト
                ) as response:
                    if response.status == 200:
                        # JSONレスポンスを取得
                        response_data = await response.json()
                        logger.info(f"📥 API レスポンス取得: {type(response_data)}")
                        
                        # 音声ファイルURLを抽出
                        audio_url = None
                        if isinstance(response_data, dict) and "generatedVoice" in response_data:
                            generated_voice = response_data["generatedVoice"]
                            # audioFileDownloadUrl を優先、なければ audioFileUrl を使用
                            audio_url = generated_voice.get("audioFileDownloadUrl") or generated_voice.get("audioFileUrl")
                        
                        if not audio_url:
                            logger.error(f"❌ 音声URLが見つかりません: {response_data}")
                            return self._generate_mock_audio(text)
                        
                        logger.info(f"🎵 音声ファイルダウンロード開始: {audio_url[:100]}...")
                        
                        # 実際の音声ファイルをダウンロード
                        async with session.get(audio_url, timeout=aiohttp.ClientTimeout(total=60)) as audio_response:
                            if audio_response.status == 200:
                                audio_data = await audio_response.read()
                                logger.info(f"✅ 音声ダウンロード成功: {len(audio_data)} bytes - {text[:30]}...")
                                
                                # WAVファイルかどうか確認
                                if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
                                    logger.info("🎵 正常なWAVファイルを確認")
                                    return audio_data
                                else:
                                    logger.warning(f"⚠️ WAVファイル形式ではない可能性: {audio_data[:20]}")
                                    return audio_data
                            else:
                                logger.error(f"❌ 音声ダウンロード失敗: {audio_response.status}")
                                return self._generate_mock_audio(text)
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"音声生成失敗: {response.status} - {error_text}")
                        logger.error(f"使用ヘッダー: {list(headers.keys())}")
                        logger.error(f"リクエストURL: {self.base_url}/voice-actors/{voice_actor_id}/generate-voice")
                        logger.warning("🔄 音声生成APIが失敗しました。モック音声を使用します。")
                        return self._generate_mock_audio(text)
                        
        except asyncio.TimeoutError:
            logger.error("Nijivoice API timeout - 音声生成がタイムアウトしました")
            logger.warning("🔄 タイムアウトのため、モック音声を使用します。")
            return self._generate_mock_audio(text)
        except aiohttp.ClientConnectionError as e:
            logger.error(f"Nijivoice API connection error: {str(e)}")
            logger.warning("🔄 接続エラーのため、モック音声を使用します。")
            return self._generate_mock_audio(text)
        except Exception as e:
            logger.error(f"Voice generation error: {str(e)}")
            logger.warning("🔄 予期しないエラーのため、モック音声を使用します。")
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
    
    async def generate_individual_files_from_script(self, voice_prompt: Dict) -> List[Dict]:
        """スクリプトから音声を生成（個別ファイルとして）"""
        try:
            voice_actor_id = voice_prompt["api_settings"]["voice_actor_id"]
            audio_files = []
            
            logger.info(f"🎵 個別音声ファイル生成開始: {len(voice_prompt['segments'])} セグメント")
            
            for i, segment in enumerate(voice_prompt["segments"]):
                try:
                    segment_id = segment.get("segment_id", f"segment_{i+1}")
                    logger.info(f"🎤 セグメント {segment_id} 生成中: {segment['text'][:30]}...")
                    
                    audio_data = await self.generate(
                        voice_actor_id=voice_actor_id,
                        text=segment["text"],
                        options=segment.get("parameters", {})
                    )
                    
                    file_info = {
                        "segment_id": segment_id,
                        "filename": f"audio_segment_{i+1:02d}.wav",
                        "audio_data": audio_data,
                        "text": segment["text"],
                        "duration": segment.get("duration", 0),
                        "size_bytes": len(audio_data)
                    }
                    
                    audio_files.append(file_info)
                    logger.info(f"✅ セグメント {segment_id} 完了: {len(audio_data)} bytes")
                    
                except Exception as e:
                    logger.error(f"❌ セグメント {segment.get('segment_id', i+1)} 生成失敗: {str(e)}")
                    # 失敗したセグメントは無音で代替
                    silence_data = self._generate_silence(5.0)
                    file_info = {
                        "segment_id": segment.get("segment_id", f"segment_{i+1}"),
                        "filename": f"audio_segment_{i+1:02d}.wav",
                        "audio_data": silence_data,
                        "text": segment["text"],
                        "duration": segment.get("duration", 5.0),
                        "size_bytes": len(silence_data),
                        "error": str(e)
                    }
                    audio_files.append(file_info)
            
            total_size = sum(file_info["size_bytes"] for file_info in audio_files)
            logger.info(f"🎊 個別音声ファイル生成完了: {len(audio_files)} ファイル, 合計 {total_size} bytes")
            return audio_files
            
        except Exception as e:
            logger.error(f"Individual audio files generation failed: {str(e)}")
            # エラー時は空のリストを返す
            return []
    
    def create_voice_prompt(self, script: Dict, voice_actor_id: str, voice_speed: float = 1.0) -> Dict:
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
                    "speed": voice_speed,  # ユーザーが指定した速度を使用
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
