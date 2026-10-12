"""The fixed words of the digests and images, one entry per content language.

These are content labels (headings, chips), not operator messages: the operator-facing CLI and
logs stay English, like the rest of the harness.
"""

L = {
    "vi": {
        "sep": ".",
        "bucket": {"ai": "AI", "software": "Phần mềm", "solutions": "Giải pháp", "startup": "Khởi nghiệp"},
        "stars": "sao", "forks": "fork", "license": "Giấy phép", "language": "Ngôn ngữ", "scanned": "Quét ngày",
        "problem": "Vấn đề nó giải quyết", "analogy": "Hình dung đời thường", "how": "Nó chạy như thế nào",
        "parts": "Các mảnh ghép", "learn": "Học được gì từ thiết kế này", "who": "Ai nên xem",
        "try": "Tự thử", "caveats": "Lưu ý trước khi dùng", "glossary": "Từ khóa", "source": "Nguồn dữ kiện",
        "evidence": "Căn cứ", "no_cmd": "README không đưa lệnh cài đặt rõ ràng; hãy đọc README gốc.",
        "radar_title": "Radar GitHub", "picks": "Các repo của lần quét này", "stars_chart": "Số sao GitHub",
        "series": "Radar GitHub", "save": "Lưu lại để học dần", "save_text": "Mỗi tuần hai lần có một repo mới.",
        "who_slide": "Ai nên xem", "learn_slide": "Học được gì", "caveat_slide": "Lưu ý", "flow_slide": "Nó chạy thế nào",
        "parts_slide": "Các mảnh ghép", "stars_label": "sao trên GitHub", "scan_note": "Số liệu theo ngày quét",
        "repo_link": "Repo gốc", "disclaimer": "Nội dung do AI tóm tắt từ README và cấu trúc repo; hãy đọc repo gốc trước khi dùng.",
    },
    "en": {
        "sep": ",",
        "bucket": {"ai": "AI", "software": "Software", "solutions": "Solutions", "startup": "Startup"},
        "stars": "stars", "forks": "forks", "license": "License", "language": "Language", "scanned": "Scanned",
        "problem": "The problem it solves", "analogy": "Everyday picture", "how": "How it works",
        "parts": "The moving parts", "learn": "What the design teaches", "who": "Who should look",
        "try": "Try it", "caveats": "Before you use it", "glossary": "Glossary", "source": "Facts from",
        "evidence": "Evidence", "no_cmd": "The README gives no clear install command; read the original README.",
        "radar_title": "GitHub Radar", "picks": "This scan's repositories", "stars_chart": "GitHub stars",
        "series": "GitHub Radar", "save": "Save it to learn step by step", "save_text": "A new repository twice a week.",
        "who_slide": "Who should look", "learn_slide": "What to learn", "caveat_slide": "Heads-up", "flow_slide": "How it works",
        "parts_slide": "The moving parts", "stars_label": "stars on GitHub", "scan_note": "Numbers as of the scan date",
        "repo_link": "Original repo", "disclaimer": "AI summary of the README and repository layout; read the original repository before relying on it.",
    },
    "ja": {
        "sep": ",",
        "bucket": {"ai": "AI", "software": "ソフトウェア", "solutions": "ソリューション", "startup": "スタートアップ"},
        "stars": "スター", "forks": "フォーク", "license": "ライセンス", "language": "言語", "scanned": "調査日",
        "problem": "解決する課題", "analogy": "身近なたとえ", "how": "仕組み",
        "parts": "構成要素", "learn": "設計から学べること", "who": "おすすめの人",
        "try": "試してみる", "caveats": "使う前の注意", "glossary": "用語", "source": "情報源",
        "evidence": "根拠", "no_cmd": "README に明確なインストール手順がありません。元の README を確認してください。",
        "radar_title": "GitHub レーダー", "picks": "今回の調査対象", "stars_chart": "GitHub スター数",
        "series": "GitHub レーダー", "save": "保存して少しずつ学ぼう", "save_text": "毎週水曜と土曜に、新しいリポジトリを紹介します。",
        "who_slide": "おすすめの人", "learn_slide": "学べること", "caveat_slide": "注意点", "flow_slide": "仕組み",
        "parts_slide": "構成要素", "stars_label": "GitHub のスター数", "scan_note": "数値は調査日時点",
        "repo_link": "元のリポジトリ", "disclaimer": "README とリポジトリ構成を AI が要約したものです。利用前に元のリポジトリを確認してください。",
    },
}
