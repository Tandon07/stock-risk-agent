from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

def detect_lang(text: str) -> str:
    try:
        lang = detect(text)
        # normalize: treat 'hi' as Hindi, everything else 'en' for our app
        return "hi" if lang.startswith("hi") else "en"
    except Exception:
        return "en"
