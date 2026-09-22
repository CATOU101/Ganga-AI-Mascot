using UnityEngine;

namespace ChachaAvatar
{
    // Lightweight amplitude-based mouth animation. No paid lip-sync package is required.
    public class AudioMouthLipSync : MonoBehaviour
    {
        [SerializeField] private SkinnedMeshRenderer faceRenderer;
        [SerializeField, Range(1f, 12f)] private float sensitivity = 6f;
        [SerializeField, Range(1f, 30f)] private float smoothing = 16f;
        [SerializeField, Range(0f, 0.05f)] private float silenceThreshold = 0.008f;
        [SerializeField, Range(0f, 40f)] private float minimumOpenWeight = 12f;
        [SerializeField, Range(40f, 100f)] private float maximumOpenWeight = 85f;
        [SerializeField] private bool enableProceduralFallback = true;

        private readonly float[] samples = new float[256];
        private AudioSource source;
        private int mouthIndex = -1;
        private float currentWeight;
        private bool isProceduralTalking;

        public bool IsActive => (source != null && source.isPlaying) || isProceduralTalking;
        public float CurrentWeight => currentWeight;

        public void EnsureInitialized(SkinnedMeshRenderer renderer = null)
        {
            if (renderer != null) faceRenderer = renderer;
            if (faceRenderer == null) faceRenderer = GetComponentInChildren<SkinnedMeshRenderer>();
            if (faceRenderer != null && faceRenderer.sharedMesh != null)
            {
                mouthIndex = faceRenderer.sharedMesh.GetBlendShapeIndex("Mouth_Open");
            }
        }

        public void Begin(AudioSource audioSource, string mouthShapeName = "Mouth_Open")
        {
            source = audioSource;
            EnsureInitialized();
            if (faceRenderer != null && faceRenderer.sharedMesh != null)
            {
                mouthIndex = faceRenderer.sharedMesh.GetBlendShapeIndex(mouthShapeName);
            }
            isProceduralTalking = false;
        }

        public void SetProceduralTalking(bool talking)
        {
            EnsureInitialized();
            isProceduralTalking = talking;
            if (!talking && (source == null || !source.isPlaying))
            {
                Stop();
            }
        }

        public void Stop()
        {
            source = null;
            isProceduralTalking = false;
            currentWeight = 0f;
            if (mouthIndex >= 0 && faceRenderer != null)
            {
                faceRenderer.SetBlendShapeWeight(mouthIndex, 0f);
            }
        }

        private void Update()
        {
            if (mouthIndex < 0)
            {
                EnsureInitialized();
                if (mouthIndex < 0) return;
            }

            var target = 0f;

            if (source != null && source.isPlaying)
            {
                source.GetOutputData(samples, 0);
                var sum = 0f;
                for (var i = 0; i < samples.Length; i++) sum += samples[i] * samples[i];
                var rms = Mathf.Sqrt(sum / samples.Length);
                if (rms > silenceThreshold)
                {
                    var normalized = Mathf.Clamp01((rms - silenceThreshold) * sensitivity);
                    target = Mathf.Lerp(minimumOpenWeight, maximumOpenWeight, normalized);
                }
            }
            else if (isProceduralTalking && enableProceduralFallback)
            {
                // Procedural speech flap oscillation (approx. 5-6 syllables per second)
                var wave = Mathf.Sin(Time.time * 24f) * 0.5f + 0.5f;
                var subWave = Mathf.Sin(Time.time * 11f) * 0.3f + 0.7f;
                target = wave * subWave * (maximumOpenWeight * 0.75f);
            }
            else
            {
                target = 0f;
            }

            // Asymmetric attack/release smoothing: snappy attack on vowels, gentle decay on release
            var speed = (target > currentWeight) ? 24f : 14f;
            currentWeight = Mathf.Lerp(currentWeight, target, 1f - Mathf.Exp(-speed * Time.deltaTime));
            if (faceRenderer != null)
            {
                faceRenderer.SetBlendShapeWeight(mouthIndex, currentWeight);
            }
        }

        private void OnDisable()
        {
            Stop();
        }
    }
}
