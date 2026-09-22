using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace ChachaAvatar
{
    public class HttpSpeechToTextProvider : SpeechToTextProvider
    {
        [SerializeField] private string endpoint = "";

        [Serializable]
        private class SttResponse
        {
            public string text;
            public string language;
        }

        public override IEnumerator Transcribe(AudioClip recording, string language, Action<TranscriptionResult> completed)
        {
            if (recording == null || string.IsNullOrWhiteSpace(endpoint))
            {
                completed(new TranscriptionResult { Error = "A recording and STT endpoint are required." });
                yield break;
            }

            var form = new List<IMultipartFormSection>
            {
                new MultipartFormFileSection("audio", WavEncoder.Encode(recording), "recording.wav", "audio/wav"),
                new MultipartFormDataSection("language", language)
            };
            using (var request = UnityWebRequest.Post(endpoint, form))
            {
                yield return request.SendWebRequest();
                if (request.result != UnityWebRequest.Result.Success)
                {
                    completed(new TranscriptionResult { Error = request.error });
                    yield break;
                }

                var response = JsonUtility.FromJson<SttResponse>(request.downloadHandler.text);
                completed(new TranscriptionResult
                {
                    Success = response != null && !string.IsNullOrWhiteSpace(response.text),
                    Text = response == null ? "" : response.text,
                    Language = response == null || string.IsNullOrWhiteSpace(response.language) ? language : response.language,
                    Error = response == null ? "Invalid STT JSON response." : ""
                });
            }
        }
    }

    internal static class WavEncoder
    {
        public static byte[] Encode(AudioClip clip)
        {
            var sampleCount = clip.samples * clip.channels;
            var samples = new float[sampleCount];
            clip.GetData(samples, 0);
            var bytes = new byte[44 + sampleCount * 2];
            WriteText(bytes, 0, "RIFF");
            WriteInt(bytes, 4, 36 + sampleCount * 2);
            WriteText(bytes, 8, "WAVEfmt ");
            WriteInt(bytes, 16, 16);
            WriteShort(bytes, 20, 1);
            WriteShort(bytes, 22, (short)clip.channels);
            WriteInt(bytes, 24, clip.frequency);
            WriteInt(bytes, 28, clip.frequency * clip.channels * 2);
            WriteShort(bytes, 32, (short)(clip.channels * 2));
            WriteShort(bytes, 34, 16);
            WriteText(bytes, 36, "data");
            WriteInt(bytes, 40, sampleCount * 2);
            for (var i = 0; i < sampleCount; i++)
            {
                var pcm = (short)Mathf.Clamp(samples[i] * short.MaxValue, short.MinValue, short.MaxValue);
                bytes[44 + i * 2] = (byte)(pcm & 0xff);
                bytes[45 + i * 2] = (byte)((pcm >> 8) & 0xff);
            }
            return bytes;
        }

        private static void WriteText(byte[] bytes, int offset, string value) { Encoding.ASCII.GetBytes(value).CopyTo(bytes, offset); }
        private static void WriteInt(byte[] bytes, int offset, int value) { BitConverter.GetBytes(value).CopyTo(bytes, offset); }
        private static void WriteShort(byte[] bytes, int offset, short value) { BitConverter.GetBytes(value).CopyTo(bytes, offset); }
    }
}
