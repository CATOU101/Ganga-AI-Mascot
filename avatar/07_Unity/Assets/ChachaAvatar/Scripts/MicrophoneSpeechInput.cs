using System;
using System.Collections;
using UnityEngine;

namespace ChachaAvatar
{
    public class MicrophoneSpeechInput : MonoBehaviour
    {
        [SerializeField] private SpeechToTextProvider speechToText;
        [SerializeField] private string language = "hi";
        [SerializeField] private int maxRecordingSeconds = 20;
        [SerializeField] private int sampleRate = 16000;

        private string microphone;
        private AudioClip recording;

        public string Language
        {
            get => language;
            set => language = value;
        }

        public bool StartRecording()
        {
            if (Microphone.devices == null || Microphone.devices.Length == 0)
            {
                Debug.LogWarning("No microphone device is available.");
                return false;
            }
            microphone = Microphone.devices[0];
            recording = Microphone.Start(microphone, false, maxRecordingSeconds, sampleRate);
            return recording != null;
        }

        public void StopRecording(Action<TranscriptionResult> completed)
        {
            if (recording == null || string.IsNullOrWhiteSpace(microphone))
            {
                completed(new TranscriptionResult { Error = "Recording has not started." });
                return;
            }
            var position = Microphone.GetPosition(microphone);
            Microphone.End(microphone);
            var trimmed = Trim(recording, position);
            recording = null;
            if (speechToText == null)
            {
                completed(new TranscriptionResult { Error = "No SpeechToTextProvider is attached." });
                return;
            }
            StartCoroutine(speechToText.Transcribe(trimmed, language, completed));
        }

        private static AudioClip Trim(AudioClip source, int samples)
        {
            samples = Mathf.Max(1, samples);
            var data = new float[samples * source.channels];
            source.GetData(data, 0);
            var output = AudioClip.Create("UserSpeech", samples, source.channels, source.frequency, false);
            output.SetData(data, 0);
            return output;
        }
    }
}
