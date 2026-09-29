using System;
using System.Collections;
using UnityEngine;

namespace ChachaAvatar
{
    [Serializable]
    public class AvatarCommand
    {
        public string text;
        public string language = "hi";
        public string emotion = "neutral";
        public string gesture = "";
    }

    [Serializable]
    public class VoiceProfile
    {
        public string language = "hi";
        public string voice = "";
        public string ttsEndpoint = "";
    }

    public class SpeechResult
    {
        public bool Success;
        public string Error;
        public AudioClip Clip;
    }

    public class TranscriptionResult
    {
        public bool Success;
        public string Error;
        public string Text;
        public string Language;
    }

    public class BrainResult
    {
        public bool Success;
        public string Error;
        public AvatarCommand Command;
    }

    public abstract class TextToSpeechProvider : MonoBehaviour
    {
        public abstract IEnumerator Synthesize(AvatarCommand command, VoiceProfile voice, Action<SpeechResult> completed);
    }

    public abstract class SpeechToTextProvider : MonoBehaviour
    {
        public abstract IEnumerator Transcribe(AudioClip recording, string language, Action<TranscriptionResult> completed);
    }

    public abstract class BrainApiClient : MonoBehaviour
    {
        public abstract IEnumerator RequestResponse(string userText, string language, Action<BrainResult> completed);
    }
}
