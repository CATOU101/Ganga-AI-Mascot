using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace ChachaAvatar
{
    public class HttpTextToSpeechProvider : TextToSpeechProvider
    {
        [SerializeField] private AudioType audioType = AudioType.WAV;

        [Serializable]
        private class TtsPayload
        {
            public string text;
            public string language;
            public string voice;
        }

        public override IEnumerator Synthesize(AvatarCommand command, VoiceProfile voice, Action<SpeechResult> completed)
        {
            if (string.IsNullOrWhiteSpace(voice.ttsEndpoint))
            {
                completed(new SpeechResult { Error = "No TTS endpoint configured for language " + command.language });
                yield break;
            }

            var payload = new TtsPayload { text = command.text, language = command.language, voice = voice.voice };
            var request = new UnityWebRequest(voice.ttsEndpoint, UnityWebRequest.kHttpVerbPOST);
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(payload)));
            request.downloadHandler = new DownloadHandlerAudioClip(voice.ttsEndpoint, audioType);
            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("Accept", "audio/wav, audio/mpeg");
            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
            {
                completed(new SpeechResult { Error = request.error });
                yield break;
            }

            completed(new SpeechResult { Success = true, Clip = DownloadHandlerAudioClip.GetContent(request) });
        }
    }
}
