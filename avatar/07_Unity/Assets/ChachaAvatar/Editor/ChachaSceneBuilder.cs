using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace ChachaAvatar.Editor
{
    public static class ChachaSceneBuilder
    {
        private const string FbxPath = "Assets/ChachaAvatar/Models/Chacha_Rigged.fbx";
        private const string FbxPath_v03 = "Assets/ChachaAvatar/Models/Chacha_v03.fbx";
        private const string ScenePath = "Assets/ChachaAvatar/Scenes/ChachaDemo.unity";
        private const string GenScenePath = "Assets/ChachaAvatar/Generated/ChachaDemo.unity";
        private const string PrefabPath = "Assets/ChachaAvatar/Generated/ChachaAvatar.prefab";
        private const string PrefabPath_v03 = "Assets/ChachaAvatar/Generated/ChachaAvatar_v03.prefab";
        private const string MaterialsFolder = "Assets/ChachaAvatar/Materials";
        private const string ControllerPath = "Assets/ChachaAvatar/Generated/ChachaAnimator.controller";
        private const string Model3MaterialPath = "Assets/ChachaAvatar/Materials/Chacha_Model3_Mat.mat";

        [MenuItem("Chacha/Rebuild Scene and Make Character Visible")]
        public static void ExecuteBuild()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            try
            {
                Debug.Log("[ChachaSceneBuilder] Starting character setup (Model 2 + Model 3)...");
                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);

                if (!Directory.Exists("Assets/ChachaAvatar/Generated"))
                {
                    Directory.CreateDirectory("Assets/ChachaAvatar/Generated");
                }
                if (!Directory.Exists("Assets/ChachaAvatar/Scenes"))
                {
                    Directory.CreateDirectory("Assets/ChachaAvatar/Scenes");
                }

                // 1. Create a clean empty scene
                var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

                var controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(ControllerPath);

                // ===================================================================
                // 2. Setup Model 2 (PBR Stylized Avatar)
                // ===================================================================
                GameObject avatar2 = null;
                ChachaAvatarController avatar2Ctrl = null;
                ChachaConversationController convo2 = null;
                ChachaTestUI testUI2 = null;
                var fbx2 = AssetDatabase.LoadAssetAtPath<GameObject>(FbxPath);
                if (fbx2 != null)
                {
                    avatar2 = PrefabUtility.InstantiatePrefab(fbx2) as GameObject;
                    if (avatar2 != null)
                    {
                        avatar2.name = "ChachaAvatar";
                        avatar2.transform.position = Vector3.zero;
                        avatar2.transform.rotation = Quaternion.Euler(0f, 180f, 0f);
                        avatar2.transform.localScale = Vector3.one;

                        var skinnedMesh2 = avatar2.GetComponentInChildren<SkinnedMeshRenderer>(true);
                        if (skinnedMesh2 != null)
                        {
                            skinnedMesh2.enabled = true;
                            skinnedMesh2.updateWhenOffscreen = true;
                            var materialNames = new string[]
                            {
                                "Chacha_Skin", "Chacha_Turban_Red", "Chacha_Moustache_White",
                                "Chacha_Shirt_White", "Chacha_Vest_Dark", "Chacha_Tie_Red",
                                "Chacha_Pants_Navy", "Chacha_Shoes_Black", "Chacha_Cane_Brown"
                            };
                            var mats = new Material[materialNames.Length];
                            for (int i = 0; i < materialNames.Length; i++)
                            {
                                mats[i] = AssetDatabase.LoadAssetAtPath<Material>(MaterialsFolder + "/" + materialNames[i] + ".mat");
                            }
                            skinnedMesh2.sharedMaterials = mats;
                        }

                        SetupAvatarComponents(avatar2, skinnedMesh2, controller, out avatar2Ctrl, out convo2, out testUI2);
                        PrefabUtility.SaveAsPrefabAssetAndConnect(avatar2, PrefabPath, InteractionMode.AutomatedAction);
                    }
                }

                // ===================================================================
                // 3. Setup Model 3 (Artwork Image-Textured Avatar)
                // ===================================================================
                GameObject avatar3 = null;
                ChachaAvatarController avatar3Ctrl = null;
                ChachaConversationController convo3 = null;
                ChachaTestUI testUI3 = null;
                var fbx3 = AssetDatabase.LoadAssetAtPath<GameObject>(FbxPath_v03) ?? fbx2;
                if (fbx3 != null)
                {
                    avatar3 = PrefabUtility.InstantiatePrefab(fbx3) as GameObject;
                    if (avatar3 != null)
                    {
                        avatar3.name = "ChachaAvatar_v03";
                        avatar3.transform.position = Vector3.zero;
                        avatar3.transform.rotation = Quaternion.Euler(0f, 180f, 0f);
                        avatar3.transform.localScale = Vector3.one;

                        var skinnedMesh3 = avatar3.GetComponentInChildren<SkinnedMeshRenderer>(true);
                        if (skinnedMesh3 != null)
                        {
                            skinnedMesh3.enabled = true;
                            skinnedMesh3.updateWhenOffscreen = true;
                            var mat3 = AssetDatabase.LoadAssetAtPath<Material>(Model3MaterialPath);
                            if (mat3 != null)
                            {
                                skinnedMesh3.sharedMaterials = new Material[] { mat3 };
                            }
                        }

                        SetupAvatarComponents(avatar3, skinnedMesh3, controller, out avatar3Ctrl, out convo3, out testUI3);
                        PrefabUtility.SaveAsPrefabAssetAndConnect(avatar3, PrefabPath_v03, InteractionMode.AutomatedAction);
                    }
                }

                // ===================================================================
                // 4. Configure Multi-Model Switching in Scene
                // ===================================================================
                if (avatar2 != null && avatar3 != null)
                {
                    // Model 3 (Artwork) is hero, visible by default
                    // Model 2 has its SkinnedMeshRenderer and Animator disabled initially
                    var rend2 = avatar2.GetComponentInChildren<SkinnedMeshRenderer>(true);
                    if (rend2 != null) rend2.enabled = false;
                    var anim2 = avatar2.GetComponent<Animator>();
                    if (anim2 != null) anim2.enabled = false;
                    if (testUI2 != null) testUI2.enabled = false;

                    var rend3 = avatar3.GetComponentInChildren<SkinnedMeshRenderer>(true);
                    if (rend3 != null) rend3.enabled = true;
                    var anim3 = avatar3.GetComponent<Animator>();
                    if (anim3 != null) anim3.enabled = true;

                    // Wire dual avatar references into both TestUIs
                    if (testUI3 != null)
                    {
                        AssignRef(testUI3, "model2Avatar", avatar2Ctrl);
                        AssignRef(testUI3, "model3Avatar", avatar3Ctrl);
                        AssignRef(testUI3, "avatar", avatar3Ctrl);
                        AssignRef(testUI3, "conversation", convo3);
                    }
                    if (testUI2 != null)
                    {
                        AssignRef(testUI2, "model2Avatar", avatar2Ctrl);
                        AssignRef(testUI2, "model3Avatar", avatar3Ctrl);
                        AssignRef(testUI2, "avatar", avatar3Ctrl);
                        AssignRef(testUI2, "conversation", convo3);
                    }
                }

                // ===================================================================
                // 5. Setup Camera for full-body view (head to shoes)
                // ===================================================================
                var camObj = new GameObject("Main Camera");
                camObj.tag = "MainCamera";
                var cam = camObj.AddComponent<Camera>();
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = new Color(0.38f, 0.42f, 0.46f); // Soft neutral studio grey backdrop
                cam.fieldOfView = 38f;
                cam.nearClipPlane = 0.1f;
                cam.farClipPlane = 100f;
                cam.allowHDR = false;
                camObj.AddComponent<AudioListener>();

                // Position camera directly in front of Chacha, framed head-to-toe (78% vertical fill)
                camObj.transform.position = new Vector3(0f, 0.95f, -3.54f);
                camObj.transform.LookAt(new Vector3(0f, 0.95f, 0f));

                // 6. Soft Studio-Style Cartoon Lighting (directional key, fill, rim + ambient)
                var keyLightObj = new GameObject("Key Light");
                var keyLight = keyLightObj.AddComponent<Light>();
                keyLight.type = LightType.Directional;
                keyLight.intensity = 0.85f;
                keyLight.color = new Color(1f, 0.97f, 0.92f);
                keyLightObj.transform.rotation = Quaternion.Euler(10f, -20f, 0f);

                var fillLightObj = new GameObject("Fill Light");
                var fillLight = fillLightObj.AddComponent<Light>();
                fillLight.type = LightType.Directional;
                fillLight.intensity = 0.55f;
                fillLight.color = new Color(0.90f, 0.94f, 1f);
                fillLightObj.transform.rotation = Quaternion.Euler(6f, 24f, 0f);

                var rimLightObj = new GameObject("Rim Light");
                var rimLight = rimLightObj.AddComponent<Light>();
                rimLight.type = LightType.Directional;
                rimLight.intensity = 0.75f;
                rimLight.color = new Color(0.95f, 0.95f, 1f);
                rimLightObj.transform.position = new Vector3(0.5f, 2.2f, 2.2f);
                rimLightObj.transform.rotation = Quaternion.Euler(25f, 155f, 0f);

                // Ambient light settings: bright neutral studio ambient
                RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
                RenderSettings.ambientLight = new Color(0.38f, 0.38f, 0.42f);
                RenderSettings.ambientIntensity = 0.75f;

                // 7. Ground Floor Disc/Plane
                var floorObj = GameObject.CreatePrimitive(PrimitiveType.Plane);
                floorObj.name = "Presentation Floor";
                floorObj.transform.position = Vector3.zero;
                floorObj.transform.localScale = new Vector3(0.5f, 1f, 0.5f);
                var floorMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/ChachaAvatar/Generated/ChachaFloor.mat");
                if (floorMat != null)
                {
                    floorObj.GetComponent<Renderer>().sharedMaterial = floorMat;
                }

                EditorSceneManager.SaveScene(scene, ScenePath);
                EditorSceneManager.SaveScene(scene, GenScenePath);

                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();

                // 10. Capture 1080p verification screenshot
                try
                {
                    var rt = new RenderTexture(1920, 1080, 24);
                    cam.targetTexture = rt;
                    cam.Render();
                    RenderTexture.active = rt;
                    var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
                    tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
                    tex.Apply();
                    cam.targetTexture = null;
                    RenderTexture.active = null;
                    Object.DestroyImmediate(rt);
                    var projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
                    var repoRoot = Path.GetFullPath(Path.Combine(projectRoot, ".."));
                    var finalDir = Path.Combine(repoRoot, "08_Final");
                    if (!Directory.Exists(finalDir)) Directory.CreateDirectory(finalDir);
                    var screenPath = Path.Combine(finalDir, "game_view_verification.png");
                    File.WriteAllBytes(screenPath, tex.EncodeToPNG());
                    Object.DestroyImmediate(tex);
                    Debug.Log("[ChachaSceneBuilder] Captured verification screenshot: " + screenPath);
                }
                catch (Exception ex)
                {
                    Debug.LogWarning("[ChachaSceneBuilder] Could not capture screenshot: " + ex.Message);
                }

                Selection.activeGameObject = avatar3 ?? avatar2;
                Debug.Log("[ChachaSceneBuilder] SUCCESS! Chacha avatars (Model 2 + Model 3) fully set up with " +
                    "FBX mesh, materials, animator, script components, audio clips, " +
                    "voice profiles, camera, and 3-point lighting.");
            }
            catch (Exception ex)
            {
                Debug.LogError("[ChachaSceneBuilder] Exception during build: " + ex);
            }
        }

        private static void SetupAvatarComponents(
            GameObject avatar,
            SkinnedMeshRenderer skinnedMesh,
            RuntimeAnimatorController controller,
            out ChachaAvatarController avatarCtrl,
            out ChachaConversationController convo,
            out ChachaTestUI testUI)
        {
            var animator = GetOrAdd<Animator>(avatar);
            if (controller != null)
            {
                animator.runtimeAnimatorController = controller;
            }

            var audioSource = GetOrAdd<AudioSource>(avatar);
            audioSource.playOnAwake = false;

            var tts = GetOrAdd<HttpTextToSpeechProvider>(avatar);
            var stt = GetOrAdd<HttpSpeechToTextProvider>(avatar);
            var brain = GetOrAdd<HttpBrainApiClient>(avatar);
            var lipSync = GetOrAdd<AudioMouthLipSync>(avatar);
            avatarCtrl = GetOrAdd<ChachaAvatarController>(avatar);
            var micInput = GetOrAdd<MicrophoneSpeechInput>(avatar);
            convo = GetOrAdd<ChachaConversationController>(avatar);
            testUI = GetOrAdd<ChachaTestUI>(avatar);

            Assign(stt, "endpoint", "http://127.0.0.1:8765/stt");
            Assign(brain, "endpoint", "http://127.0.0.1:8765/brain");

            if (skinnedMesh != null)
            {
                AssignRef(lipSync, "faceRenderer", skinnedMesh);
                AssignRef(avatarCtrl, "faceRenderer", skinnedMesh);
            }
            AssignRef(avatarCtrl, "animator", animator);
            AssignRef(avatarCtrl, "speechAudio", audioSource);
            AssignRef(avatarCtrl, "lipSync", lipSync);
            AssignRef(avatarCtrl, "textToSpeech", tts);
            AssignRef(avatarCtrl, "brainApi", brain);

            AssignRef(avatarCtrl, "greetingClipHindi", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_greeting.wav"));
            AssignRef(avatarCtrl, "happyClipHindi", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_happy.wav"));
            AssignRef(avatarCtrl, "thinkingClipHindi", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_thinking.wav"));
            AssignRef(avatarCtrl, "surprisedClipHindi", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_surprised.wav"));
            AssignRef(avatarCtrl, "nodClipHindi", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_nod.wav"));

            AssignRef(avatarCtrl, "greetingClipEnglish", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_greeting.wav"));
            AssignRef(avatarCtrl, "happyClipEnglish", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_happy.wav"));
            AssignRef(avatarCtrl, "thinkingClipEnglish", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_thinking.wav"));
            AssignRef(avatarCtrl, "surprisedClipEnglish", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_surprised.wav"));

            var profiles = new SerializedObject(avatarCtrl).FindProperty("voices");
            if (profiles != null)
            {
                profiles.arraySize = 2;
                var p0 = profiles.GetArrayElementAtIndex(0);
                p0.FindPropertyRelative("language").stringValue = "hi";
                p0.FindPropertyRelative("voice").stringValue = "chacha_hi";
                p0.FindPropertyRelative("ttsEndpoint").stringValue = "http://127.0.0.1:8765/tts";
                var p1 = profiles.GetArrayElementAtIndex(1);
                p1.FindPropertyRelative("language").stringValue = "en";
                p1.FindPropertyRelative("voice").stringValue = "chacha_en";
                p1.FindPropertyRelative("ttsEndpoint").stringValue = "http://127.0.0.1:8765/tts";
                profiles.serializedObject.ApplyModifiedPropertiesWithoutUndo();
            }

            AssignRef(micInput, "speechToText", stt);
            AssignRef(convo, "microphoneInput", micInput);
            AssignRef(convo, "brainApi", brain);
            AssignRef(convo, "avatar", avatarCtrl);

            AssignRef(testUI, "avatar", avatarCtrl);
            AssignRef(testUI, "conversation", convo);
        }

        /// <summary>Assigns a string value to a SerializeField by name.</summary>
        private static void Assign(Object target, string propertyName, string value)
        {
            var so = new SerializedObject(target);
            var prop = so.FindProperty(propertyName);
            if (prop != null)
            {
                prop.stringValue = value;
                so.ApplyModifiedPropertiesWithoutUndo();
            }
            else
            {
                Debug.LogWarning("[ChachaSceneBuilder] Property '" + propertyName + "' not found on " + target.GetType().Name);
            }
        }

        /// <summary>Assigns an object reference to a SerializeField by name.</summary>
        private static void AssignRef(Object target, string propertyName, Object value)
        {
            var so = new SerializedObject(target);
            var prop = so.FindProperty(propertyName);
            if (prop != null)
            {
                prop.objectReferenceValue = value;
                so.ApplyModifiedPropertiesWithoutUndo();
            }
            else
            {
                Debug.LogWarning("[ChachaSceneBuilder] Property '" + propertyName + "' not found on " + target.GetType().Name);
            }
        }

        /// <summary>Gets existing component or adds it if missing, using Unity's overloaded null check.</summary>
        private static T GetOrAdd<T>(GameObject go) where T : Component
        {
            var comp = go.GetComponent<T>();
            if (comp == null)
            {
                comp = go.AddComponent<T>();
            }
            return comp;
        }
    }
}
