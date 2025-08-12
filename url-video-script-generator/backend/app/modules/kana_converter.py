from typing import Optional


def to_hiragana(text: Optional[str]) -> str:
    """与えられた日本語テキストをひらがなへ変換する。

    pykakasi が利用可能な場合はそれを使って厳密に変換。
    未導入またはエラー時は入力文字列をそのまま返すフォールバック。
    """
    if not text:
        return ""
    try:
        from pykakasi import kakasi  # type: ignore

        kks = kakasi()
        # Kanji/Katakana/Hiragana -> Hiragana
        kks.setMode("J", "H")
        kks.setMode("K", "H")
        kks.setMode("H", "H")
        conv = kks.getConverter()
        return conv.do(text)
    except Exception:
        # 変換に失敗した場合は元のテキストを返す
        return text


