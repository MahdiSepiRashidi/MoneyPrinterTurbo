"""R-1 Azure Speech F0 test: Farsi question intonation via the V2 (SSML) path.


Prereqs: [azure] speech_key + speech_region filled in config.toml.
Scratch script — delete after running.
"""
import os
import sys
from xml.sax.saxutils import escape

from app.config import config
from app.services import voice

speech_key = config.azure.get("speech_key", "")
speech_region = config.azure.get("speech_region", "")
if not speech_key or not speech_region:
    print(
        "Azure not configured yet. Fill [azure] speech_key / speech_region in "
        "config.toml and re-run."
    )
    sys.exit(1)

import azure.cognitiveservices.speech as speechsdk

OUT_DIR = "storage/r1-tts-check"
VOICE = "fa-IR-DilaraNeural"

Q_HEAD = "آیا تا به حال فکر کرده‌اید که چرا برخی افراد موفق‌تر از بقیه"
Q_TAIL = "هستند؟"
FULL = """آیا تا به حال فکر کرده‌اید که چرا برخی افراد، با وجود شرایط مشابه، به موفقیت‌های بزرگ‌تری رسیده‌اند؟ پاسخ اغلب ساده‌تر از آن چیزی است که به نظر می‌رسد. هزاران پژوهش نشان داده است که خواندن، قوی‌ترین مهارتی است که می‌توانید در آن سرمایه‌گذاری کنید. هر روز فقط بیست دقیقه مطالعه، در طول یک سال، به خواندن چندین کتاب منجر می‌شود. این کار نه تنها دایره واژگان شما را گسترش می‌دهد، بلکه ذهن شما را به فکر کردن عمیق‌تر عادت می‌دهد. وقتی کتاب می‌خوانید، بدون هزینه و ریسک، تجربه هزاران زندگی دیگر را در ذهن خود مرور می‌کنید. از شکست‌ها درس می‌گیرید و از پیروزی‌ها الهام می‌گیرید. نکته مهم این است که کتاب خواندن یک فرآیند تدریجی است، نه یک شتاب‌طلبی. کافی است هر روز یک صفحه بخوانید و ایده‌های آن را به زندگی روزمره خود بیاورید. یادتان باشد که هیچ تلاشی هدر نمی‌رود؛ اگر مسیر درست باشد، نتیجه در پایان راه خود را نشان می‌دهد. پس از همین امروز، یک کتاب بردارید، برای خود قاعده‌ای ساده بگذارید، و اجازه دهید ایده‌ها آرام‌آرام مسیر زندگی‌تان را تغییر دهند. آینده‌ای که همیشه به فکرش بودید، از همین لحظه شروع می‌شود."""


def make_synthesizer(out_path: str) -> speechsdk.SpeechSynthesizer:
    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=speech_region
    )
    speech_config.speech_synthesis_voice_name = VOICE
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
    )
    return speechsdk.SpeechSynthesizer(
        audio_config=audio_config, speech_config=speech_config
    )


def speak_ssml(ssml: str, out_path: str) -> bool:
    synthesizer = make_synthesizer(out_path)
    result = synthesizer.speak_ssml_async(ssml).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"{out_path}: ok")
        return True
    print(
        f"{out_path}: FAILED reason={result.reason} "
        f"cancel={result.cancellation_details.reason} "
        f"error={result.cancellation_details.error_details}"
    )
    return False


def report(label: str, out_path: str) -> None:
    if os.path.exists(out_path):
        d = voice.get_audio_duration(out_path)
        print(f"  {label} -> {out_path} ({os.path.getsize(out_path)} bytes, {d:.2f}s)")
    else:
        print(f"  {label} -> {out_path} (missing)")


# 1. Plain text through MPT's V2 dispatch (its internal SSML builder).
sub = voice.tts(Q_HEAD + " " + Q_TAIL, f"{VOICE}-V2", 1.0, f"{OUT_DIR}/az_base_q.mp3")
report("az_base_q (MPT V2, plain text)", f"{OUT_DIR}/az_base_q.mp3")

# 2. Hand-built SSML: gentle pitch rise into the final word (interpolated contour).
ssml_rise_word = (
    '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="fa-IR">'
    f'<voice name="{VOICE}"><p>{escape(Q_HEAD)} '
    f'<prosody pitch="+40%">{escape(Q_TAIL)}</prosody></p></voice></speak>'
)
speak_ssml(ssml_rise_word, f"{OUT_DIR}/az_rise_q.mp3")

# 3. Hand-built SSML: smaller rise over the whole question sentence + short break.
ssml_rise_sent = (
    '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="fa-IR">'
    f'<voice name="{VOICE}"><p>'
    f'<prosody pitch="+0%">{escape(Q_HEAD)}</prosody> '
    f'<break time="150ms"/>'
    f'<prosody pitch="+25%">{escape(Q_TAIL)}</prosody>'
    "</p></voice></speak>"
)
speak_ssml(ssml_rise_sent, f"{OUT_DIR}/az_rise_q2.mp3")

# 4. Full script via MPT's V2 dispatch (duration/quality comparison with Edge).
sub = voice.tts(FULL, f"{VOICE}-V2", 1.0, f"{OUT_DIR}/az_base_full.mp3")
report("az_base_full (MPT V2, full 189-word script)", f"{OUT_DIR}/az_base_full.mp3")
