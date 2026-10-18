"""把 index.html、css、js 合併成一個檔案。

用法：python tools/build_single.py 輸出路徑 [--fragment]

--fragment 會拿掉 <!doctype>、<html>、<head>、<body> 外殼（給會自己包外殼的網頁託管服務用）。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def Build(Fragment):
    Html = (ROOT / "index.html").read_text(encoding="utf-8")

    def InlineCss(Match):
        Css = (ROOT / Match.group(1)).read_text(encoding="utf-8")
        return "<style>\n" + Css + "</style>"

    def InlineJs(Match):
        Js = (ROOT / Match.group(1)).read_text(encoding="utf-8")
        return "<script>\n" + Js + "</script>"

    Html = re.sub(r'<link rel="stylesheet" href="(css/[^"]+)">', InlineCss, Html)
    Html = re.sub(r'<script src="(js/[^"]+)"></script>', InlineJs, Html)
    if Fragment:
        for Pattern in [r"<!doctype html>\s*", r"<html[^>]*>\s*", r"</html>\s*", r"<head>\s*", r"</head>\s*",
                        r"<body>\s*", r"</body>\s*", r'<meta charset="utf-8">\s*', r'<meta name="viewport"[^>]*>\s*']:
            Html = re.sub(Pattern, "", Html, flags=re.IGNORECASE)
    return Html


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    Output = Path(sys.argv[1])
    Output.write_text(Build("--fragment" in sys.argv), encoding="utf-8")
    print("寫入", Output, Output.stat().st_size, "bytes")
