python - <<'PY'
import glob, os, json, textwrap
VID = "X7OtYqOl2L0"
paths = glob.glob(f"output/youtube_result/*{VID}*.json")
if not paths:
    print("❌  파일 자체를 못 찾음")
else:
    p = max(paths, key=os.path.getmtime)
    print("✓ 발견:", p)
    try:
        with open(p, encoding="utf-8") as f:
            obj = json.load(f)
        print("✓ JSON 파싱 성공, 프레임 수:", len(obj.get("data", [])))
    except Exception as e:
        print("❌ JSON 파싱 실패:", e)
PY