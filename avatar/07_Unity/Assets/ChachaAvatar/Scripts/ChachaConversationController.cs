using System.Collections;
using UnityEngine;

namespace ChachaAvatar
{
    public class ChachaConversationController : MonoBehaviour
    {
        public enum ConversationState { Idle, Listening, Thinking, Speaking }

        [SerializeField] private MicrophoneSpeechInput microphoneInput;
        [SerializeField] private BrainApiClient brainApi;
        [SerializeField] private ChachaAvatarController avatar;

        public ConversationState State { get; private set; } = ConversationState.Idle;

        public void BeginListening()
        {
            if (State != ConversationState.Idle || microphoneInput == null)
                return;
            if (!microphoneInput.StartRecording())
                return;
            State = ConversationState.Listening;
        }

        public void EndListening()
        {
            if (State != ConversationState.Listening || microphoneInput == null)
                return;
            State = ConversationState.Thinking;
            microphoneInput.StopRecording(OnTranscriptionComplete);
        }

        private void OnTranscriptionComplete(TranscriptionResult result)
        {
            if (result == null || !result.Success || string.IsNullOrWhiteSpace(result.Text))
            {
                Debug.LogWarning("STT failed: " + (result == null ? "No result" : result.Error));
                State = ConversationState.Idle;
                return;
            }
            StartCoroutine(RequestBrainResponse(result.Text, result.Language));
        }

        public void SetLanguage(string lang)
        {
            if (microphoneInput != null)
                microphoneInput.Language = lang;
        }

        public void SetAvatar(ChachaAvatarController newAvatar)
        {
            avatar = newAvatar;
        }

        private IEnumerator RequestBrainResponse(string userText, string language)
        {
            if (brainApi == null || avatar == null)
            {
                Debug.LogWarning("Brain API client and avatar controller must be assigned.");
                State = ConversationState.Idle;
                yield break;
            }

            BrainResult result = null;
            yield return brainApi.RequestResponse(userText, language, value => result = value);
            if (result == null || !result.Success || result.Command == null)
            {
                Debug.LogWarning("Brain API request unfulfilled (" + (result == null ? "Null" : result.Error) + "). Playing offline dialogue.");
                State = ConversationState.Speaking;
                avatar.Speak(new AvatarCommand
                {
                    text = (language == "en") ? "Hello child! Chacha heard you clearly." : "Namaste beta! Main sun raha hoon.",
                    language = language,
                    emotion = "happy",
                    gesture = "wave"
                });
                yield return new WaitWhile(() => avatar != null && avatar.IsBusy);
                State = ConversationState.Idle;
                yield break;
            }

            State = ConversationState.Speaking;
            avatar.Speak(result.Command);
            yield return new WaitWhile(() => avatar != null && avatar.IsBusy);
            State = ConversationState.Idle;
        }
    }
}
