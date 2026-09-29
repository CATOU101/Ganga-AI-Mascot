using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace ChachaAvatar
{
    // Sends user speech to Member 1's backend and expects an AvatarCommand JSON response.
    public class HttpBrainApiClient : BrainApiClient
    {
        [SerializeField] private string endpoint = "";
        [SerializeField] private string authorizationHeader = "";

        [Serializable]
        private class BrainRequest
        {
            public string text;
            public string language;
        }

        public override IEnumerator RequestResponse(string userText, string language, Action<BrainResult> completed)
        {
            if (string.IsNullOrWhiteSpace(endpoint))
            {
                completed(new BrainResult { Error = "No Brain API endpoint is configured." });
                yield break;
            }

            var payload = new BrainRequest { text = userText, language = language };
            using (var request = new UnityWebRequest(endpoint, UnityWebRequest.kHttpVerbPOST))
            {
                request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(JsonUtility.ToJson(payload)));
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");
                request.SetRequestHeader("Accept", "application/json");
                if (!string.IsNullOrWhiteSpace(authorizationHeader))
                    request.SetRequestHeader("Authorization", authorizationHeader);
                request.timeout = 3;
                yield return request.SendWebRequest();

                if (request.result != UnityWebRequest.Result.Success)
                {
                    completed(new BrainResult { Error = request.error });
                    yield break;
                }

                var command = JsonUtility.FromJson<AvatarCommand>(request.downloadHandler.text);
                if (command == null || string.IsNullOrWhiteSpace(command.text))
                {
                    completed(new BrainResult { Error = "Brain API returned invalid AvatarCommand JSON." });
                    yield break;
                }
                if (string.IsNullOrWhiteSpace(command.language)) command.language = language;
                completed(new BrainResult { Success = true, Command = command });
            }
        }
    }
}
