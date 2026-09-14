using System;
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

namespace ChachaAvatar
{
    /// <summary>
    /// Modern conversational UI for the Chacha AI avatar.
    /// Avatar-centric design: Keeps Chacha large and completely unobstructed with a single-row
    /// ultra-compact bottom dock (36px) and a collapsible developer/debug drawer.
    /// </summary>
    public class ChachaTestUI : MonoBehaviour
    {
        [Header("Avatar & Conversation References")]
        [SerializeField] private ChachaAvatarController avatar;
        [SerializeField] private ChachaConversationController conversation;
        [SerializeField] private ChachaAvatarController model2Avatar;
        [SerializeField] private ChachaAvatarController model3Avatar;

        [Header("Mock Server")]
        [SerializeField] private string mockServerHealthUrl = "http://127.0.0.1:8765/health";

        // UI State
        private bool showDebugPanel = false;
        private bool isCloseUpView = false;
        private int activeModel = 3; // 3 = Model 3 (Artwork Texture), 2 = Model 2 (PBR Stylized)
        private string currentLanguage = "hi"; // "hi" or "en"
        private string userCustomMessage = "Namaste Chacha kaise ho?";
        private string serverStatus = "Checking...";
        private bool isServerOnline = false;
        private bool playVoiceWithStates = true;

        // Camera transition targets (full body 78% fill vs close-up conversational)
        private readonly Vector3 fullBodyCamPos = new Vector3(0f, 0.95f, -3.54f);
        private readonly Vector3 closeUpCamPos = new Vector3(0f, 1.45f, -1.80f);
        private readonly Vector3 fullBodyLookAt = new Vector3(0f, 0.95f, 0f);
        private readonly Vector3 closeUpLookAt = new Vector3(0f, 1.45f, 0f);

        // GUI Rects
        private Rect debugWindowRect = new Rect(0, 0, 300, 480);

        private void Awake()
        {
            // If another active ChachaTestUI exists in scene, disable this duplicate
            var allUIs = FindObjectsByType<ChachaTestUI>(FindObjectsSortMode.None);
            foreach (var ui in allUIs)
            {
                if (ui != this && ui.enabled)
                {
                    if (this.gameObject.name == "ChachaAvatar" && ui.gameObject.name == "ChachaAvatar_v03")
                    {
                        this.enabled = false;
                        return;
                    }
                }
            }

            if (model2Avatar == null)
            {
                var go = GameObject.Find("ChachaAvatar");
                if (go == null)
                {
                    foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
                    {
                        if (root.name == "ChachaAvatar") { go = root; break; }
                    }
                }
                if (go != null) model2Avatar = go.GetComponent<ChachaAvatarController>();
            }
            if (model3Avatar == null)
            {
                var go = GameObject.Find("ChachaAvatar_v03");
                if (go == null)
                {
                    foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
                    {
                        if (root.name == "ChachaAvatar_v03") { go = root; break; }
                    }
                }
                if (go != null) model3Avatar = go.GetComponent<ChachaAvatarController>();
            }

            if (conversation == null)
            {
                conversation = GetComponent<ChachaConversationController>() ?? FindFirstObjectByType<ChachaConversationController>();
            }

            if (model3Avatar != null)
            {
                SwitchModel(3);
            }
            else if (model2Avatar != null)
            {
                SwitchModel(2);
            }
            else
            {
                if (avatar == null)
                {
                    avatar = GetComponent<ChachaAvatarController>() ?? FindFirstObjectByType<ChachaAvatarController>();
                }
            }

            if (conversation != null && avatar != null)
            {
                conversation.SetAvatar(avatar);
            }
        }

        public void SwitchModel(int modelIndex)
        {
            activeModel = (modelIndex == 2) ? 2 : 3;
            var activeCtrl = (activeModel == 3) ? model3Avatar : model2Avatar;
            var inactiveCtrl = (activeModel == 3) ? model2Avatar : model3Avatar;

            if (activeCtrl != null)
            {
                if (!activeCtrl.gameObject.activeSelf) activeCtrl.gameObject.SetActive(true);
                var rend = activeCtrl.GetComponentInChildren<SkinnedMeshRenderer>(true);
                if (rend != null) rend.enabled = true;
                var anim = activeCtrl.GetComponent<Animator>();
                if (anim != null) anim.enabled = true;
                avatar = activeCtrl;
            }
            if (inactiveCtrl != null)
            {
                var rend = inactiveCtrl.GetComponentInChildren<SkinnedMeshRenderer>(true);
                if (rend != null) rend.enabled = false;
                var anim = inactiveCtrl.GetComponent<Animator>();
                if (anim != null) anim.enabled = false;
            }
            if (conversation != null && avatar != null)
            {
                conversation.SetAvatar(avatar);
            }
        }

        private void Start()
        {
            StartCoroutine(CheckServerHealthRoutine());
        }

        private void Update()
        {
            // Smooth Camera Framing Transition
            var mainCam = Camera.main;
            if (mainCam != null)
            {
                var targetPos = isCloseUpView ? closeUpCamPos : fullBodyCamPos;
                var targetLook = isCloseUpView ? closeUpLookAt : fullBodyLookAt;
                mainCam.transform.position = Vector3.Lerp(mainCam.transform.position, targetPos, Time.deltaTime * 6f);
                mainCam.transform.rotation = Quaternion.Slerp(
                    mainCam.transform.rotation,
                    Quaternion.LookRotation(targetLook - mainCam.transform.position),
                    Time.deltaTime * 6f
                );
            }

            if (avatar == null) return;

            // Keyboard shortcuts for rapid testing
            if (Input.GetKeyDown(KeyCode.Alpha1)) avatar.PlayIdle();
            else if (Input.GetKeyDown(KeyCode.Alpha2)) avatar.PlayTalking();
            else if (Input.GetKeyDown(KeyCode.Alpha3)) avatar.PlayHappy(playVoiceWithStates, currentLanguage);
            else if (Input.GetKeyDown(KeyCode.Alpha4)) avatar.PlayThinking(playVoiceWithStates, currentLanguage);
            else if (Input.GetKeyDown(KeyCode.Alpha5)) avatar.PlaySurprised(playVoiceWithStates, currentLanguage);
            else if (Input.GetKeyDown(KeyCode.N)) avatar.PlayNod(playVoiceWithStates, currentLanguage);
            else if (Input.GetKeyDown(KeyCode.W)) avatar.PlayGreeting(currentLanguage);
            else if (Input.GetKeyDown(KeyCode.C)) isCloseUpView = !isCloseUpView;
            else if (Input.GetKeyDown(KeyCode.M)) SwitchModel(activeModel == 3 ? 2 : 3);
            else if (Input.GetKeyDown(KeyCode.Space))
            {
                SendCurrentMessage();
            }

            // Push-to-talk key 'T'
            if (conversation != null && Microphone.devices != null && Microphone.devices.Length > 0)
            {
                if (Input.GetKeyDown(KeyCode.T))
                {
                    conversation.SetLanguage(currentLanguage);
                    conversation.BeginListening();
                }
                else if (Input.GetKeyUp(KeyCode.T) && conversation.State == ChachaConversationController.ConversationState.Listening)
                {
                    conversation.EndListening();
                }
            }
        }

        private void OnGUI()
        {
            GUI.skin.box.fontSize = 11;
            GUI.skin.button.fontSize = 11;
            GUI.skin.textField.fontSize = 11;

            DrawTopStateBadge();
            DrawBottomConversationDock();
            DrawDebugToggleButton();

            if (showDebugPanel)
            {
                debugWindowRect.x = Screen.width - 315;
                debugWindowRect.y = 38;
                debugWindowRect = GUI.Window(99, debugWindowRect, DrawDebugWindow, "Developer Diagnostics");
            }
        }

        /// <summary>Floating top state badge centered cleanly above Chacha.</summary>
        private void DrawTopStateBadge()
        {
            var isSpeaking = avatar != null && avatar.IsBusy;
            var isListening = conversation != null && conversation.State == ChachaConversationController.ConversationState.Listening;
            var stateStr = isSpeaking ? "Speaking" : (isListening ? "Listening..." : (avatar != null ? avatar.CurrentState.ToString() : "Ready"));

            var dotColor = isSpeaking ? new Color(0.25f, 0.85f, 1f) : (isListening ? new Color(1f, 0.35f, 0.35f) : new Color(0.35f, 0.9f, 0.35f));

            var badgeWidth = 350f;
            var badgeHeight = 24f;
            var badgeRect = new Rect((Screen.width - badgeWidth) * 0.5f, 8f, badgeWidth, badgeHeight);

            GUI.color = new Color(0.12f, 0.15f, 0.20f, 0.80f);
            GUI.Box(badgeRect, GUIContent.none);
            GUI.color = Color.white;

            var labelStyle = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = 11,
                fontStyle = FontStyle.Bold
            };

            var statusText = $"●  Chacha: {stateStr}  |  {(currentLanguage == "hi" ? "हिंदी" : "EN")}  |  Model {(activeModel == 3 ? "3 (Artwork)" : "2 (PBR)")}";
            GUI.color = dotColor;
            GUI.Label(badgeRect, statusText, labelStyle);
            GUI.color = Color.white;
        }

        /// <summary>Ultra-compact single-line bottom dock (36px high) leaving Chacha's legs 100% visible.</summary>
        private void DrawBottomConversationDock()
        {
            var dockWidth = Mathf.Min(760f, Screen.width - 20f);
            var dockHeight = 36f;
            var dockX = (Screen.width - dockWidth) * 0.5f;
            var dockY = Screen.height - dockHeight - 8f;

            // Translucent dark background
            GUI.color = new Color(0.12f, 0.14f, 0.18f, 0.88f);
            GUI.Box(new Rect(dockX, dockY, dockWidth, dockHeight), GUIContent.none);
            GUI.color = Color.white;

            GUILayout.BeginArea(new Rect(dockX + 6f, dockY + 5f, dockWidth - 12f, dockHeight - 8f));
            GUILayout.BeginHorizontal();

            // Language Pill
            GUI.backgroundColor = (currentLanguage == "hi") ? new Color(1f, 0.82f, 0.30f) : new Color(0.35f, 0.75f, 1f);
            var langText = currentLanguage == "hi" ? "HI" : "EN";
            if (GUILayout.Button(langText, GUILayout.Width(32), GUILayout.Height(24)))
            {
                currentLanguage = (currentLanguage == "hi") ? "en" : "hi";
                if (currentLanguage == "hi" && userCustomMessage == "Hello Chacha how are you?")
                    userCustomMessage = "Namaste Chacha kaise ho?";
                else if (currentLanguage == "en" && userCustomMessage == "Namaste Chacha kaise ho?")
                    userCustomMessage = "Hello Chacha how are you?";
                conversation?.SetLanguage(currentLanguage);
            }
            GUI.backgroundColor = Color.white;

            // Model Switcher Button
            GUI.backgroundColor = (activeModel == 3) ? new Color(0.95f, 0.45f, 0.25f) : new Color(0.40f, 0.55f, 0.85f);
            var modelLabel = (activeModel == 3) ? "M3: Art" : "M2: PBR";
            if (GUILayout.Button(modelLabel, GUILayout.Width(58), GUILayout.Height(24)))
            {
                SwitchModel(activeModel == 3 ? 2 : 3);
            }
            GUI.backgroundColor = Color.white;

            // Expression Quick Buttons
            if (GUILayout.Button("Namaste", GUILayout.Height(24))) avatar?.PlayGreeting(currentLanguage);
            if (GUILayout.Button("Wah", GUILayout.Height(24))) avatar?.PlayHappy(playVoiceWithStates, currentLanguage);
            if (GUILayout.Button("Soch", GUILayout.Height(24))) avatar?.PlayThinking(playVoiceWithStates, currentLanguage);
            if (GUILayout.Button("Nod", GUILayout.Height(24))) avatar?.PlayNod(playVoiceWithStates, currentLanguage);

            // Message text field
            userCustomMessage = GUILayout.TextField(userCustomMessage, GUILayout.Height(24));

            // Send button
            GUI.backgroundColor = new Color(0.25f, 0.78f, 0.40f);
            if (GUILayout.Button("Send", GUILayout.Width(48), GUILayout.Height(24)))
            {
                SendCurrentMessage();
            }
            GUI.backgroundColor = Color.white;

            // Microphone / Push-to-Talk button
            var isListening = conversation != null && conversation.State == ChachaConversationController.ConversationState.Listening;
            GUI.backgroundColor = isListening ? new Color(1f, 0.35f, 0.35f) : new Color(0.35f, 0.65f, 1f);
            var micLabel = isListening ? "● Stop" : "Talk [T]";
            if (GUILayout.Button(micLabel, GUILayout.Width(62), GUILayout.Height(24)))
            {
                if (conversation != null)
                {
                    if (isListening)
                    {
                        conversation.EndListening();
                    }
                    else
                    {
                        conversation.SetLanguage(currentLanguage);
                        conversation.BeginListening();
                    }
                }
            }
            GUI.backgroundColor = Color.white;

            // Camera toggle
            GUI.backgroundColor = isCloseUpView ? new Color(0.85f, 0.65f, 1f) : new Color(0.6f, 0.75f, 0.9f);
            if (GUILayout.Button(isCloseUpView ? "Cam: Close" : "Cam: Full", GUILayout.Width(76), GUILayout.Height(24)))
            {
                isCloseUpView = !isCloseUpView;
            }
            GUI.backgroundColor = Color.white;

            GUILayout.EndHorizontal();
            GUILayout.EndArea();
        }

        private void DrawDebugToggleButton()
        {
            var btnRect = new Rect(Screen.width - 100f, 8f, 92f, 24f);
            GUI.backgroundColor = showDebugPanel ? new Color(1f, 0.75f, 0.4f) : new Color(0.25f, 0.30f, 0.38f);
            if (GUI.Button(btnRect, showDebugPanel ? "Dev ▲" : "Dev ▼"))
            {
                showDebugPanel = !showDebugPanel;
            }
            GUI.backgroundColor = Color.white;
        }

        /// <summary>Collapsible developer diagnostics panel.</summary>
        private void DrawDebugWindow(int windowId)
        {
            GUILayout.Space(4);

            // Server Status Section
            GUILayout.Label("<b>--- Mock Server & API ---</b>");
            GUI.color = isServerOnline ? new Color(0.4f, 1f, 0.4f) : new Color(1f, 0.75f, 0.35f);
            GUILayout.Label("Status: " + serverStatus);
            GUI.color = Color.white;

            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Check Health", GUILayout.Height(22)))
            {
                StartCoroutine(CheckServerHealthRoutine());
            }
#if UNITY_EDITOR
            if (!isServerOnline && GUILayout.Button("Start Server", GUILayout.Height(22)))
            {
                LaunchMockServerProcess();
            }
#endif
            GUILayout.EndHorizontal();

            GUILayout.Space(4);
            var apiStatus = avatar != null ? avatar.LastApiStatus : "N/A";
            GUILayout.Label("<size=10><b>Last API Result:</b> " + apiStatus + "</size>");

            GUILayout.Space(6);
            GUILayout.Label("<b>--- Audio & Lip-Sync ---</b>");
            playVoiceWithStates = GUILayout.Toggle(playVoiceWithStates, " Play Voice Audio with States");

            var audioSrc = avatar != null ? avatar.GetComponent<AudioSource>() : null;
            if (audioSrc != null)
            {
                GUILayout.Label($"<size=10>AudioSource: {(audioSrc.isPlaying ? "Playing" : "Idle")}, Vol: {audioSrc.volume:F1}</size>");
            }

            var lipSync = avatar != null ? avatar.GetComponent<AudioMouthLipSync>() : null;
            if (lipSync != null)
            {
                GUILayout.Label($"<size=10>LipSync: {(lipSync.IsActive ? "Active" : "Idle")}, Weight: {lipSync.CurrentWeight:F1}</size>");
            }

            GUILayout.Space(6);
            GUILayout.Label("<b>--- State Overrides ---</b>");
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Idle [1]", GUILayout.Height(22))) avatar?.PlayIdle();
            if (GUILayout.Button("Talk [2]", GUILayout.Height(22))) avatar?.PlayTalking();
            GUILayout.EndHorizontal();

            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Wave [W]", GUILayout.Height(22))) avatar?.PlayWave();
            if (GUILayout.Button("Nod [N]", GUILayout.Height(22))) avatar?.PlayNod(true, currentLanguage);
            GUILayout.EndHorizontal();

            GUILayout.Space(8);
            if (GUILayout.Button("Close Dev Panel", GUILayout.Height(22)))
            {
                showDebugPanel = false;
            }

            GUI.DragWindow();
        }

        private void SendCurrentMessage()
        {
            if (avatar == null) return;
            var prompt = !string.IsNullOrWhiteSpace(userCustomMessage)
                ? userCustomMessage
                : ((currentLanguage == "en") ? "Hello Chacha" : "Namaste Chacha");
            avatar.TriggerMockBrainPipeline(prompt, currentLanguage);
        }

        private IEnumerator CheckServerHealthRoutine()
        {
            serverStatus = "Checking...";
            using (var request = UnityWebRequest.Get(mockServerHealthUrl))
            {
                request.timeout = 2;
                yield return request.SendWebRequest();
                if (request.result == UnityWebRequest.Result.Success)
                {
                    isServerOnline = true;
                    serverStatus = "Online (Port 8765)";
                }
                else
                {
                    isServerOnline = false;
                    serverStatus = "Offline (Local Voice Active)";
                }
            }
        }

#if UNITY_EDITOR
        private void LaunchMockServerProcess()
        {
            try
            {
                var repoRoot = Path.GetFullPath(Path.Combine(Application.dataPath, "../.."));
                var serverScript = Path.Combine(repoRoot, "09_LocalMock", "chacha_mock_voice_server.py");
                if (File.Exists(serverScript))
                {
                    var psi = new System.Diagnostics.ProcessStartInfo
                    {
                        FileName = "python",
                        Arguments = $"\"{serverScript}\"",
                        WorkingDirectory = repoRoot,
                        UseShellExecute = true,
                        CreateNoWindow = false
                    };
                    System.Diagnostics.Process.Start(psi);
                    Debug.Log("[ChachaTestUI] Launched local mock server process: " + serverScript);
                    StartCoroutine(DelayedHealthCheck());
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[ChachaTestUI] Could not launch mock server: " + ex.Message);
            }
        }

        private IEnumerator DelayedHealthCheck()
        {
            yield return new WaitForSeconds(1.5f);
            yield return CheckServerHealthRoutine();
        }
#endif
    }
}
