using System.Collections.Generic;
using System.IO;
using ChachaAvatar;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ChachaAvatar.Editor
{
    public static class ChachaAvatarSetupWizard
    {
        private const string OutputFolder = "Assets/ChachaAvatar/Generated";
        private const string MaterialsFolder = "Assets/ChachaAvatar/Materials";
        private const string DefaultFbxPath = "Assets/ChachaAvatar/Models/Chacha_Rigged.fbx";

        [MenuItem("Chacha/1-Click Complete Setup (Avatar + Controller + Materials + Demo Scene)")]
        public static void OneClickSetup()
        {
            var fbxObject = Selection.activeObject as GameObject;
            var assetPath = fbxObject != null ? AssetDatabase.GetAssetPath(fbxObject) : "";

            if (string.IsNullOrWhiteSpace(assetPath) || Path.GetExtension(assetPath).ToLowerInvariant() != ".fbx")
            {
                assetPath = DefaultFbxPath;
                fbxObject = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);
            }

            if (fbxObject == null)
            {
                EditorUtility.DisplayDialog("Chacha Setup", "Could not find Chacha_Rigged.fbx at " + DefaultFbxPath + ". Please select the FBX in the Project window.", "OK");
                return;
            }

            EnsureFolder(OutputFolder);
            EnsureFolder(MaterialsFolder);

            // 1. Create or retrieve character materials with faithful colors
            var materials = CreateOrUpdateMaterials();

            // 2. Create Animator Controller
            var controller = CreateAnimatorController(assetPath);

            // 3. Create Avatar Instance
            var instance = PrefabUtility.InstantiatePrefab(fbxObject) as GameObject;
            if (instance == null)
            {
                EditorUtility.DisplayDialog("Chacha Setup", "The FBX could not be instantiated.", "OK");
                return;
            }

            instance.name = "ChachaAvatar";
            var animator = instance.GetComponent<Animator>();
            if (animator == null) animator = instance.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;

            var face = instance.GetComponentInChildren<SkinnedMeshRenderer>();
            if (face != null && materials != null && materials.Length > 0)
            {
                AssignMaterialsToRenderer(face, materials);
            }

            var audio = instance.GetComponent<AudioSource>() ?? instance.AddComponent<AudioSource>();
            audio.playOnAwake = false;

            var tts = instance.GetComponent<HttpTextToSpeechProvider>() ?? instance.AddComponent<HttpTextToSpeechProvider>();
            var stt = instance.GetComponent<HttpSpeechToTextProvider>() ?? instance.AddComponent<HttpSpeechToTextProvider>();
            var brain = instance.GetComponent<HttpBrainApiClient>() ?? instance.AddComponent<HttpBrainApiClient>();
            var lipSync = instance.GetComponent<AudioMouthLipSync>() ?? instance.AddComponent<AudioMouthLipSync>();
            var avatar = instance.GetComponent<ChachaAvatarController>() ?? instance.AddComponent<ChachaAvatarController>();
            var microphone = instance.GetComponent<MicrophoneSpeechInput>() ?? instance.AddComponent<MicrophoneSpeechInput>();
            var conversation = instance.GetComponent<ChachaConversationController>() ?? instance.AddComponent<ChachaConversationController>();
            var testUI = instance.GetComponent<ChachaTestUI>() ?? instance.AddComponent<ChachaTestUI>();

            // Configure endpoints to point to local mock server
            AssignString(stt, "endpoint", "http://127.0.0.1:8765/stt");
            AssignString(brain, "endpoint", "http://127.0.0.1:8765/brain");

            Assign(lipSync, "faceRenderer", face);
            Assign(avatar, "animator", animator);
            Assign(avatar, "faceRenderer", face);
            Assign(avatar, "speechAudio", audio);
            Assign(avatar, "lipSync", lipSync);
            Assign(avatar, "textToSpeech", tts);
            Assign(avatar, "brainApi", brain);
            ConfigureVoiceProfiles(avatar);

            var hiGreeting = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_greeting.wav");
            var hiHappy = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_happy.wav");
            var hiThinking = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_thinking.wav");
            var hiSurprised = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_surprised.wav");
            var hiNod = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_hi_nod.wav");

            var enGreeting = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_greeting.wav");
            var enHappy = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_happy.wav");
            var enThinking = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_thinking.wav");
            var enSurprised = AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/ChachaAvatar/Audio/chacha_en_surprised.wav");

            Assign(avatar, "greetingClipHindi", hiGreeting);
            Assign(avatar, "happyClipHindi", hiHappy);
            Assign(avatar, "thinkingClipHindi", hiThinking);
            Assign(avatar, "surprisedClipHindi", hiSurprised);
            Assign(avatar, "nodClipHindi", hiNod);

            Assign(avatar, "greetingClipEnglish", enGreeting);
            Assign(avatar, "happyClipEnglish", enHappy);
            Assign(avatar, "thinkingClipEnglish", enThinking);
            Assign(avatar, "surprisedClipEnglish", enSurprised);

            Assign(microphone, "speechToText", stt);
            Assign(conversation, "microphoneInput", microphone);
            Assign(conversation, "brainApi", brain);
            Assign(conversation, "avatar", avatar);
            Assign(testUI, "avatar", avatar);
            Assign(testUI, "conversation", conversation);

            var prefabPath = OutputFolder + "/ChachaAvatar.prefab";
            PrefabUtility.SaveAsPrefabAsset(instance, prefabPath);
            Object.DestroyImmediate(instance);

            // 4. Create and configure Demo Scene
            CreateDemoSceneInternal(prefabPath);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            EditorUtility.DisplayDialog("Chacha Setup Complete", "Chacha avatar, materials, animator, and demo scene created successfully!\n\nOpen Assets/ChachaAvatar/Generated/ChachaDemo.unity and click Play.", "OK");
        }

        [MenuItem("Chacha/Create Unity-Ready Avatar From Selected FBX")]
        private static void CreateAvatar()
        {
            OneClickSetup();
        }

        [MenuItem("Chacha/Create Demo Scene")]
        private static void CreateDemoScene()
        {
            var prefabPath = OutputFolder + "/ChachaAvatar.prefab";
            if (!File.Exists(prefabPath))
            {
                OneClickSetup();
                return;
            }
            CreateDemoSceneInternal(prefabPath);
        }

        private static void CreateDemoSceneInternal(string prefabPath)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null) return;

            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("Chacha Setup: Cannot create demo scene during play mode.");
                return;
            }

            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
                return;

            EnsureFolder(OutputFolder);
            EnsureFolder("Assets/ChachaAvatar/Scenes");

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var avatar = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
            avatar.name = "ChachaAvatar";
            avatar.transform.position = Vector3.zero;
            avatar.transform.rotation = Quaternion.identity;

            CreateFloor();
            CreateCamera();
            CreateLighting();

            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.24f, 0.26f, 0.30f);

            var scenePathGen = OutputFolder + "/ChachaDemo.unity";
            var scenePathMain = "Assets/ChachaAvatar/Scenes/ChachaDemo.unity";

            EditorSceneManager.SaveScene(scene, scenePathGen);
            EditorSceneManager.SaveScene(scene, scenePathMain);
            Selection.activeGameObject = avatar;
        }

        public static AnimatorController CreateAnimatorController(string fbxPath)
        {
            var path = OutputFolder + "/ChachaAnimator.controller";
            AssetDatabase.DeleteAsset(path);
            var controller = AnimatorController.CreateAnimatorControllerAtPath(path);

            controller.AddParameter("IsTalking", AnimatorControllerParameterType.Bool);
            foreach (var trigger in new[] { "Simple_Hand_Gesture", "Head_Nod", "Head_Turn", "Happy_Reaction", "Thinking_Reaction" })
                controller.AddParameter(trigger, AnimatorControllerParameterType.Trigger);

            var layer = controller.layers[0];
            var machine = layer.stateMachine;
            var clips = AssetDatabase.LoadAllAssetsAtPath(fbxPath);

            var idle = AddState(machine, "Idle_Breathing", FindClip(clips, "Idle_Breathing"));
            var talking = AddState(machine, "Talking_UpperBody", FindClip(clips, "Talking_UpperBody"));
            machine.defaultState = idle;

            AddBoolTransition(idle, talking, "IsTalking", true);
            AddBoolTransition(talking, idle, "IsTalking", false);

            AddOneShot(machine, idle, "Simple_Hand_Gesture", FindClip(clips, "Simple_Hand_Gesture"));
            AddOneShot(machine, idle, "Head_Nod", FindClip(clips, "Head_Nod"));
            AddOneShot(machine, idle, "Head_Turn", FindClip(clips, "Head_Turn"));
            AddOneShot(machine, idle, "Happy_Reaction", FindClip(clips, "Happy_Reaction"));
            AddOneShot(machine, idle, "Thinking_Reaction", FindClip(clips, "Thinking_Reaction"));

            return controller;
        }

        private static AnimatorState AddState(AnimatorStateMachine machine, string name, AnimationClip clip)
        {
            var state = machine.AddState(name);
            state.motion = clip;
            return state;
        }

        private static void AddBoolTransition(AnimatorState from, AnimatorState to, string parameter, bool value)
        {
            var transition = from.AddTransition(to);
            transition.hasExitTime = false;
            transition.duration = 0.12f;
            transition.AddCondition(value ? AnimatorConditionMode.If : AnimatorConditionMode.IfNot, 0f, parameter);
        }

        private static void AddOneShot(AnimatorStateMachine machine, AnimatorState idle, string trigger, AnimationClip clip)
        {
            var state = AddState(machine, trigger, clip);
            var enter = machine.AddAnyStateTransition(state);
            enter.hasExitTime = false;
            enter.duration = 0.08f;
            enter.AddCondition(AnimatorConditionMode.If, 0f, trigger);
            var exit = state.AddTransition(idle);
            exit.hasExitTime = true;
            exit.exitTime = 0.95f;
            exit.duration = 0.12f;
        }

        private static AnimationClip FindClip(Object[] assets, string name)
        {
            foreach (var asset in assets)
            {
                var clip = asset as AnimationClip;
                if (clip == null) continue;

                if (clip.name == name || clip.name.EndsWith("|" + name) || clip.name.EndsWith(name) || clip.name.Contains(name))
                {
                    return clip;
                }
            }
            Debug.LogWarning("Chacha setup: could not find clip matching '" + name + "'. Check FBX Animation settings.");
            return null;
        }

        private static Material[] CreateOrUpdateMaterials()
        {
            EnsureFolder(MaterialsFolder);
            var definitions = new (string name, Color color, float roughness)[]
            {
                ("Chacha_Skin", new Color(0.78f, 0.45f, 0.34f, 1f), 0.62f),
                ("Chacha_Turban_Red", new Color(0.62f, 0.025f, 0.018f, 1f), 0.72f),
                ("Chacha_Moustache_White", new Color(0.88f, 0.86f, 0.82f, 1f), 0.76f),
                ("Chacha_Shirt_White", new Color(0.82f, 0.84f, 0.86f, 1f), 0.67f),
                ("Chacha_Vest_Dark", new Color(0.055f, 0.055f, 0.052f, 1f), 0.70f),
                ("Chacha_Tie_Red", new Color(0.72f, 0.0f, 0.0f, 1f), 0.55f),
                ("Chacha_Pants_Navy", new Color(0.06f, 0.075f, 0.13f, 1f), 0.68f),
                ("Chacha_Shoes_Black", new Color(0.006f, 0.006f, 0.006f, 1f), 0.48f),
                ("Chacha_Cane_Brown", new Color(0.33f, 0.13f, 0.045f, 1f), 0.50f)
            };

            var list = new List<Material>();
            var standardShader = Shader.Find("Standard");

            foreach (var def in definitions)
            {
                var matPath = MaterialsFolder + "/" + def.name + ".mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
                if (mat == null)
                {
                    mat = new Material(standardShader);
                    mat.color = def.color;
                    mat.SetFloat("_Glossiness", 1f - def.roughness);
                    AssetDatabase.CreateAsset(mat, matPath);
                }
                else
                {
                    mat.color = def.color;
                    mat.SetFloat("_Glossiness", 1f - def.roughness);
                    EditorUtility.SetDirty(mat);
                }
                list.Add(mat);
            }
            return list.ToArray();
        }

        private static void AssignMaterialsToRenderer(SkinnedMeshRenderer renderer, Material[] createdMaterials)
        {
            var matDict = new Dictionary<string, Material>();
            foreach (var m in createdMaterials)
            {
                if (m != null) matDict[m.name] = m;
            }

            var current = renderer.sharedMaterials;
            var updated = new Material[current.Length];
            for (var i = 0; i < current.Length; i++)
            {
                var cur = current[i];
                if (cur != null)
                {
                    var cleanName = cur.name.Replace(" (Instance)", "").Replace(".001", "");
                    if (matDict.TryGetValue(cleanName, out var found))
                    {
                        updated[i] = found;
                        continue;
                    }
                }
                // Fallback by index or keep existing
                updated[i] = (i < createdMaterials.Length) ? createdMaterials[i] : cur;
            }
            renderer.sharedMaterials = updated;
            EditorUtility.SetDirty(renderer);
        }

        private static void CreateFloor()
        {
            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "Presentation Floor";
            floor.transform.position = Vector3.zero;
            floor.transform.localScale = new Vector3(3f, 1f, 3f);

            var materialPath = OutputFolder + "/ChachaFloor.mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            if (material == null)
            {
                material = new Material(Shader.Find("Standard"));
                material.color = new Color(0.12f, 0.14f, 0.17f);
                AssetDatabase.CreateAsset(material, materialPath);
            }
            floor.GetComponent<Renderer>().sharedMaterial = material;
        }

        private static void CreateCamera()
        {
            var cameraObject = new GameObject("Main Camera");
            cameraObject.tag = "MainCamera";
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.06f, 0.07f, 0.09f);
            camera.fieldOfView = 36f;

            // Frame Chacha's upper body and face clearly in Unity space (Y is up, Z is depth)
            cameraObject.transform.position = new Vector3(0f, 1.4f, -2.3f);
            cameraObject.transform.LookAt(new Vector3(0f, 1.25f, 0f));
        }

        private static void CreateLighting()
        {
            // Key Light (warm front-right)
            var keyLightObj = new GameObject("Key Light");
            keyLightObj.transform.position = new Vector3(1.5f, 2.6f, -1.8f);
            keyLightObj.transform.LookAt(new Vector3(0f, 1.2f, 0f));
            var keyLight = keyLightObj.AddComponent<Light>();
            keyLight.type = LightType.Directional;
            keyLight.intensity = 1.1f;
            keyLight.color = new Color(1f, 0.96f, 0.9f);

            // Fill Light (cool front-left)
            var fillLightObj = new GameObject("Fill Light");
            fillLightObj.transform.position = new Vector3(-1.8f, 2.0f, -1.5f);
            fillLightObj.transform.LookAt(new Vector3(0f, 1.2f, 0f));
            var fillLight = fillLightObj.AddComponent<Light>();
            fillLight.type = LightType.Directional;
            fillLight.intensity = 0.5f;
            fillLight.color = new Color(0.85f, 0.9f, 1f);

            // Rim / Back Light (subtle contour)
            var rimLightObj = new GameObject("Rim Light");
            rimLightObj.transform.position = new Vector3(0f, 2.8f, 2.0f);
            rimLightObj.transform.LookAt(new Vector3(0f, 1.2f, 0f));
            var rimLight = rimLightObj.AddComponent<Light>();
            rimLight.type = LightType.Directional;
            rimLight.intensity = 0.6f;
            rimLight.color = new Color(0.9f, 0.95f, 1f);
        }

        private static void Assign(Object target, string propertyName, Object value)
        {
            var serialized = new SerializedObject(target);
            var prop = serialized.FindProperty(propertyName);
            if (prop != null)
            {
                prop.objectReferenceValue = value;
                serialized.ApplyModifiedPropertiesWithoutUndo();
            }
        }

        private static void AssignString(Object target, string propertyName, string value)
        {
            var serialized = new SerializedObject(target);
            var prop = serialized.FindProperty(propertyName);
            if (prop != null)
            {
                prop.stringValue = value;
                serialized.ApplyModifiedPropertiesWithoutUndo();
            }
        }

        private static void ConfigureVoiceProfiles(ChachaAvatarController avatar)
        {
            var serialized = new SerializedObject(avatar);
            var profiles = serialized.FindProperty("voices");
            profiles.arraySize = 2;

            var p0 = profiles.GetArrayElementAtIndex(0);
            p0.FindPropertyRelative("language").stringValue = "hi";
            p0.FindPropertyRelative("voice").stringValue = "chacha_hi";
            p0.FindPropertyRelative("ttsEndpoint").stringValue = "http://127.0.0.1:8765/tts";

            var p1 = profiles.GetArrayElementAtIndex(1);
            p1.FindPropertyRelative("language").stringValue = "en";
            p1.FindPropertyRelative("voice").stringValue = "chacha_en";
            p1.FindPropertyRelative("ttsEndpoint").stringValue = "http://127.0.0.1:8765/tts";

            serialized.ApplyModifiedPropertiesWithoutUndo();
        }

        private static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            var parent = Path.GetDirectoryName(path).Replace("\\", "/");
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }
    }
}

