using System;
using System.Collections;
using System.Linq;
using UnityEngine;

namespace ChachaAvatar
{
    public enum AvatarState
    {
        Idle,
        Talking,
        Happy,
        Thinking,
        Surprised
    }

    public class ChachaAvatarController : MonoBehaviour
    {
        [Header("Avatar Components")]
        [SerializeField] private Animator animator;
        [SerializeField] private SkinnedMeshRenderer faceRenderer;
        [SerializeField] private AudioSource speechAudio;
        [SerializeField] private AudioMouthLipSync lipSync;

        [Header("Speech & Brain Providers")]
        [SerializeField] private TextToSpeechProvider textToSpeech;
        [SerializeField] private BrainApiClient brainApi;
        [SerializeField] private VoiceProfile[] voices;

        [Header("Local Voice Library (Hindi)")]
        [SerializeField] private AudioClip greetingClipHindi;
        [SerializeField] private AudioClip happyClipHindi;
        [SerializeField] private AudioClip thinkingClipHindi;
        [SerializeField] private AudioClip surprisedClipHindi;
        [SerializeField] private AudioClip nodClipHindi;

        [Header("Local Voice Library (English)")]
        [SerializeField] private AudioClip greetingClipEnglish;
        [SerializeField] private AudioClip happyClipEnglish;
        [SerializeField] private AudioClip thinkingClipEnglish;
        [SerializeField] private AudioClip surprisedClipEnglish;

        private bool isBusy;
        private AvatarState currentState = AvatarState.Idle;
        private Coroutine activeSpeechRoutine;

        private static readonly string[] ExpressionKeys =
        {
            "Face_Happy", "Face_Thinking", "Face_Surprised", "Face_SadConfused"
        };

        public bool IsBusy => isBusy;
        public AvatarState CurrentState => currentState;

        public event Action<AvatarState> OnStateChanged;

        private void Awake()
        {
            EnsureReferences();
            EnsureDefaultVoices();
        }

        private void Start()
        {
            PlayIdle();
        }

        public string LastApiStatus { get; private set; } = "Ready";

        public void EnsureReferences()
        {
            if (animator == null) animator = GetComponent<Animator>() ?? GetComponentInChildren<Animator>();
            if (faceRenderer == null) faceRenderer = GetComponentInChildren<SkinnedMeshRenderer>();
            if (speechAudio == null) speechAudio = GetComponent<AudioSource>() ?? GetComponentInChildren<AudioSource>();
            if (lipSync == null) lipSync = GetComponent<AudioMouthLipSync>() ?? GetComponentInChildren<AudioMouthLipSync>();
            if (textToSpeech == null) textToSpeech = GetComponent<TextToSpeechProvider>() ?? GetComponentInChildren<TextToSpeechProvider>();
            if (brainApi == null) brainApi = GetComponent<BrainApiClient>() ?? GetComponentInChildren<BrainApiClient>();

            if (speechAudio != null)
            {
                speechAudio.volume = 1f;
                speechAudio.mute = false;
                speechAudio.spatialBlend = 0f;
                speechAudio.playOnAwake = false;
            }

            if (lipSync != null && faceRenderer != null)
            {
                lipSync.EnsureInitialized(faceRenderer);
            }

#if UNITY_EDITOR
            if (greetingClipHindi == null)
            {
                greetingClipHindi = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_greeting.wav");
                happyClipHindi = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_happy.wav");
                thinkingClipHindi = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_thinking.wav");
                surprisedClipHindi = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_surprised.wav");
                nodClipHindi = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_nod.wav");

                greetingClipEnglish = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_greeting.wav");
                happyClipEnglish = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_happy.wav");
                thinkingClipEnglish = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_thinking.wav");
                surprisedClipEnglish = UnityEditor.AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_surprised.wav");
            }
#endif
        }

        public void AssignVoiceClips(
            AudioClip hiGreeting, AudioClip hiHappy, AudioClip hiThinking, AudioClip hiSurprised, AudioClip hiNod,
            AudioClip enGreeting, AudioClip enHappy, AudioClip enThinking, AudioClip enSurprised)
        {
            greetingClipHindi = hiGreeting;
            happyClipHindi = hiHappy;
            thinkingClipHindi = hiThinking;
            surprisedClipHindi = hiSurprised;
            nodClipHindi = hiNod;

            greetingClipEnglish = enGreeting;
            happyClipEnglish = enHappy;
            thinkingClipEnglish = enThinking;
            surprisedClipEnglish = enSurprised;
        }

        public AudioClip GetVoiceClip(string type, string language = "hi")
        {
            var isEnglish = string.Equals(language, "en", StringComparison.OrdinalIgnoreCase);
            var key = (type ?? "").Trim().ToLowerInvariant();

            if (isEnglish)
            {
                if (key.Contains("happy") || key.Contains("pleased") || key.Contains("wah")) return happyClipEnglish;
                if (key.Contains("think") || key.Contains("ponder") || key.Contains("soch")) return thinkingClipEnglish;
                if (key.Contains("surpris") || key.Contains("arre") || key.Contains("goodness")) return surprisedClipEnglish;
                if (key.Contains("nod") || key.Contains("yes") || key.Contains("agree") || key.Contains("haan")) return greetingClipEnglish;
                return greetingClipEnglish;
            }
            else
            {
                if (key.Contains("happy") || key.Contains("shabash") || key.Contains("wah")) return happyClipHindi;
                if (key.Contains("think") || key.Contains("soch") || key.Contains("ponder")) return thinkingClipHindi;
                if (key.Contains("surpris") || key.Contains("baap") || key.Contains("arre")) return surprisedClipHindi;
                if (key.Contains("nod") || key.Contains("haan") || key.Contains("theek") || key.Contains("agree")) return nodClipHindi;
                return greetingClipHindi;
            }
        }

        private void EnsureDefaultVoices()
        {
            if (voices == null || voices.Length == 0)
            {
                voices = new[]
                {
                    new VoiceProfile { language = "hi", voice = "chacha_hi", ttsEndpoint = "http://127.0.0.1:8765/tts" },
                    new VoiceProfile { language = "en", voice = "chacha_en", ttsEndpoint = "http://127.0.0.1:8765/tts" }
                };
            }
            else
            {
                foreach (var v in voices)
                {
                    if (string.IsNullOrWhiteSpace(v.ttsEndpoint))
                        v.ttsEndpoint = "http://127.0.0.1:8765/tts";
                }
            }
        }

        public void SetState(AvatarState newState)
        {
            switch (newState)
            {
                case AvatarState.Idle:
                    PlayIdle();
                    break;
                case AvatarState.Talking:
                    PlayTalking();
                    break;
                case AvatarState.Happy:
                    PlayHappy();
                    break;
                case AvatarState.Thinking:
                    PlayThinking();
                    break;
                case AvatarState.Surprised:
                    PlaySurprised();
                    break;
            }
        }

        public void PlayIdle()
        {
            StopCurrentSpeech();
            SetExpression(null);
            if (animator != null) animator.SetBool("IsTalking", false);
            ChangeState(AvatarState.Idle);
        }

        public void PlayTalking()
        {
            StopCurrentSpeech();
            ChangeState(AvatarState.Talking);
            if (animator != null) animator.SetBool("IsTalking", true);
            if (lipSync != null) lipSync.SetProceduralTalking(true);
        }

        public void PlayGreeting(string language = "hi")
        {
            PlayVoiceLine("greeting", language, "wave");
        }

        public void PlayHappy(bool withVoice = false, string language = "hi")
        {
            if (withVoice)
            {
                PlayVoiceLine("happy", language, "happy");
            }
            else
            {
                StopCurrentSpeech();
                ChangeState(AvatarState.Happy);
                SetExpression("happy");
                if (animator != null) animator.SetTrigger("Happy_Reaction");
            }
        }

        public void PlayThinking(bool withVoice = false, string language = "hi")
        {
            if (withVoice)
            {
                PlayVoiceLine("thinking", language, "thinking");
            }
            else
            {
                StopCurrentSpeech();
                ChangeState(AvatarState.Thinking);
                SetExpression("thinking");
                if (animator != null) animator.SetTrigger("Thinking_Reaction");
            }
        }

        public void PlaySurprised(bool withVoice = false, string language = "hi")
        {
            if (withVoice)
            {
                PlayVoiceLine("surprised", language, null);
            }
            else
            {
                StopCurrentSpeech();
                ChangeState(AvatarState.Surprised);
                SetExpression("surprised");
            }
        }

        public void PlayNod(bool withVoice = false, string language = "hi")
        {
            if (withVoice)
            {
                PlayVoiceLine("nod", language, "nod");
            }
            else
            {
                if (animator != null) animator.SetTrigger("Head_Nod");
            }
        }

        public void PlayWave()
        {
            if (animator != null) animator.SetTrigger("Simple_Hand_Gesture");
        }

        public void PlayHandGesture()
        {
            PlayWave();
        }

        public void PlayHeadTurn()
        {
            if (animator != null) animator.SetTrigger("Head_Turn");
        }

        public void PlayVoiceLine(string emotionOrType, string language = "hi", string gesture = null)
        {
            EnsureReferences();
            var clip = GetVoiceClip(emotionOrType, language);
            if (clip != null)
            {
                PlayAudioClip(clip, emotionOrType, gesture);
            }
            else
            {
                StopCurrentSpeech();
                ChangeState(AvatarState.Talking);
                SetExpression(emotionOrType);
                if (!string.IsNullOrEmpty(gesture)) TriggerGesture(gesture);
                activeSpeechRoutine = StartCoroutine(FallbackProceduralSpeech(2.5f));
            }
        }

        public void PlayAudioClip(AudioClip clip, string emotion = null, string gesture = null)
        {
            if (clip == null) return;
            StopCurrentSpeech();
            isBusy = true;
            ChangeState(AvatarState.Talking);
            activeSpeechRoutine = StartCoroutine(PlayAudioRoutine(clip, emotion, gesture));
        }

        private IEnumerator PlayAudioRoutine(AudioClip clip, string emotion, string gesture)
        {
            SetExpression(emotion);
            if (!string.IsNullOrEmpty(gesture)) TriggerGesture(gesture);

            if (speechAudio != null)
            {
                speechAudio.clip = clip;
                if (animator != null) animator.SetBool("IsTalking", true);
                if (lipSync != null) lipSync.Begin(speechAudio, "Mouth_Open");
                speechAudio.Play();
                yield return new WaitWhile(() => speechAudio != null && speechAudio.isPlaying);
            }
            else
            {
                yield return FallbackProceduralSpeech(clip.length > 0 ? clip.length : 2.5f);
            }

            StopCurrentSpeech();
            PlayIdle();
        }

        public void ReceiveBrainCommandJson(string json)
        {
            var command = JsonUtility.FromJson<AvatarCommand>(json);
            if (command == null || string.IsNullOrWhiteSpace(command.text))
            {
                Debug.LogWarning("Chacha received an invalid Brain API command.");
                return;
            }
            Speak(command);
        }

        public void Speak(AvatarCommand command)
        {
            StopCurrentSpeech();
            isBusy = true;
            ChangeState(AvatarState.Talking);
            activeSpeechRoutine = StartCoroutine(SpeakRoutine(command));
        }

        public void TriggerMockBrainPipeline(string userMessage = "Namaste Chacha", string language = "hi")
        {
            EnsureReferences();
            if (brainApi == null)
            {
                Debug.LogWarning("No BrainApiClient attached. Performing direct offline voice speech.");
                Speak(new AvatarCommand
                {
                    text = (language == "en") ? "Hello child! Welcome to Chacha Avatar." : "Namaste beta! Main bilkul taiyar hoon.",
                    language = language,
                    emotion = "happy",
                    gesture = "wave"
                });
                return;
            }

            PlayThinking();
            StartCoroutine(brainApi.RequestResponse(userMessage, language, result =>
            {
                if (result != null && result.Success && result.Command != null)
                {
                    LastApiStatus = "Connected: Brain response received (" + result.Command.emotion + ")";
                    Speak(result.Command);
                }
                else
                {
                    var err = result == null ? "Null response" : result.Error;
                    LastApiStatus = "Offline Fallback (" + err + ")";
                    Debug.Log("[ChachaAvatar] Brain server offline (" + err + "). Playing authentic offline dialogue.");
                    Speak(new AvatarCommand
                    {
                        text = (language == "en") ? "Hello child! I am here to help you." : "Namaste beta! Yeh local demo chal raha hai.",
                        language = language,
                        emotion = "happy",
                        gesture = "wave"
                    });
                }
            }));
        }

        public void SetExpression(string emotion)
        {
            if (faceRenderer == null || faceRenderer.sharedMesh == null)
                return;

            foreach (var key in ExpressionKeys)
                SetBlendShape(key, 0f);

            var expression = emotion == null ? "" : emotion.Trim().ToLowerInvariant();
            if (expression == "happy") SetBlendShape("Face_Happy", 100f);
            else if (expression == "thinking") SetBlendShape("Face_Thinking", 100f);
            else if (expression == "surprised") SetBlendShape("Face_Surprised", 100f);
            else if (expression == "sad" || expression == "confused" || expression == "sad_confused") SetBlendShape("Face_SadConfused", 100f);
        }

        private IEnumerator SpeakRoutine(AvatarCommand command)
        {
            SetExpression(command.emotion);
            TriggerGesture(command.gesture);
            EnsureDefaultVoices();

            var voice = voices == null ? null : voices.FirstOrDefault(v => v != null && v.language == command.language)
                        ?? voices.FirstOrDefault();

            SpeechResult result = null;
            if (textToSpeech != null && voice != null && !string.IsNullOrWhiteSpace(voice.ttsEndpoint))
            {
                yield return textToSpeech.Synthesize(command, voice, value => result = value);
            }

            if (result != null && result.Success && result.Clip != null && speechAudio != null)
            {
                speechAudio.clip = result.Clip;
                if (animator != null) animator.SetBool("IsTalking", true);
                if (lipSync != null) lipSync.Begin(speechAudio, "Mouth_Open");
                speechAudio.Play();
                yield return new WaitWhile(() => speechAudio != null && speechAudio.isPlaying);
            }
            else
            {
                // Intelligent fallback: check local voice library for matching clip
                var fallbackClip = GetVoiceClip(command.emotion ?? "greeting", command.language);
                if (fallbackClip != null && speechAudio != null)
                {
                    Debug.Log("TTS server offline or empty. Playing authentic local voice clip: " + fallbackClip.name);
                    speechAudio.clip = fallbackClip;
                    if (animator != null) animator.SetBool("IsTalking", true);
                    if (lipSync != null) lipSync.Begin(speechAudio, "Mouth_Open");
                    speechAudio.Play();
                    yield return new WaitWhile(() => speechAudio != null && speechAudio.isPlaying);
                }
                else
                {
                    Debug.LogWarning("TTS and local audio clip unavailable. Using fallback procedural talk.");
                    yield return FallbackProceduralSpeech(2.5f);
                }
            }

            StopCurrentSpeech();
            PlayIdle();
        }

        private IEnumerator FallbackProceduralSpeech(float duration)
        {
            if (animator != null) animator.SetBool("IsTalking", true);
            if (lipSync != null) lipSync.SetProceduralTalking(true);
            yield return new WaitForSeconds(duration);
            if (lipSync != null) lipSync.SetProceduralTalking(false);
        }

        public void TriggerGesture(string gesture)
        {
            if (animator == null || string.IsNullOrWhiteSpace(gesture))
                return;
            var value = gesture.Trim().ToLowerInvariant();
            if (value == "wave" || value == "hand" || value == "gesture") animator.SetTrigger("Simple_Hand_Gesture");
            else if (value == "nod") animator.SetTrigger("Head_Nod");
            else if (value == "turn") animator.SetTrigger("Head_Turn");
            else if (value == "happy") animator.SetTrigger("Happy_Reaction");
            else if (value == "thinking") animator.SetTrigger("Thinking_Reaction");
        }

        private void SetBlendShape(string name, float weight)
        {
            if (faceRenderer == null || faceRenderer.sharedMesh == null)
                return;
            var index = faceRenderer.sharedMesh.GetBlendShapeIndex(name);
            if (index >= 0) faceRenderer.SetBlendShapeWeight(index, weight);
        }

        private void StopCurrentSpeech()
        {
            if (activeSpeechRoutine != null)
            {
                StopCoroutine(activeSpeechRoutine);
                activeSpeechRoutine = null;
            }
            if (speechAudio != null && speechAudio.isPlaying) speechAudio.Stop();
            if (lipSync != null) lipSync.Stop();
            if (animator != null) animator.SetBool("IsTalking", false);
            SetBlendShape("Mouth_Open", 0f);
            isBusy = false;
        }

        private void ChangeState(AvatarState next)
        {
            currentState = next;
            OnStateChanged?.Invoke(currentState);
        }
    }
}
