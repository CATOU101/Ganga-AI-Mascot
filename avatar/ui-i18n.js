(function attachGangaUiI18n(root, build) {
  const api = build();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaUII18n = api;
  if (root && root.document) api.initialize(root.document, root);
})(typeof globalThis !== 'undefined' ? globalThis : this, function createGangaUiI18n() {
  'use strict';

  const LANGUAGES = Object.freeze([
    { code: 'en', name: 'English' },
    { code: 'hi', name: 'हिंदी' },
    { code: 'kn', name: 'ಕನ್ನಡ' },
    { code: 'ta', name: 'தமிழ்' },
  ]);
  const LANGUAGE_CODES = new Set(LANGUAGES.map(language => language.code));
  const STORAGE_KEY = 'gangaWebsiteLanguage';

  // Static interface wording only. Source-document text and citations are never passed through this catalog.
  const MESSAGES = {
    'site.title': ['Ganga AI Mascot — Chacha Chaudhary Digital Avatar', 'गंगा एआई मैस्कॉट — चाचा चौधरी डिजिटल अवतार', 'ಗಂಗಾ ಎಐ ಮ್ಯಾಸ್ಕಾಟ್ — ಚಾಚಾ ಚೌಧರಿ ಡಿಜಿಟಲ್ ಅವತಾರ', 'கங்கை ஏஐ மாஸ்காட் — சாச்சா சௌத்ரி டிஜிட்டல் அவதாரம்'],
    'site.description': ['Chacha Chaudhary Ganga AI Mascot — Interactive 3D Avatar, Grounded RAG Knowledge Base, Multilingual Input, and Neural Voice Synthesis.', 'चाचा चौधरी गंगा एआई मैस्कॉट — इंटरैक्टिव 3D अवतार, सत्यापित ज्ञान आधार, बहुभाषी इनपुट और वॉइस सुविधा।', 'ಚಾಚಾ ಚೌಧರಿ ಗಂಗಾ ಎಐ ಮ್ಯಾಸ್ಕಾಟ್ — ಸಂವಾದಾತ್ಮಕ 3D ಅವತಾರ, ಆಧಾರಿತ ಜ್ಞಾನಸಂಗ್ರಹ, ಬಹುಭಾಷಾ ಇನ್‌ಪುಟ್ ಮತ್ತು ಧ್ವನಿ ಸೌಲಭ್ಯ.', 'சாச்சா சௌத்ரி கங்கை ஏஐ மாஸ்காட் — ஊடாடும் 3D அவதாரம், ஆதார அறிவுத்தளம், பல்மொழி உள்ளீடு மற்றும் குரல் வசதி.'],
    'brand.tagline': ['Chacha Chaudhary – Your Ganga Guide', 'चाचा चौधरी – आपके गंगा मार्गदर्शक', 'ಚಾಚಾ ಚೌಧರಿ – ನಿಮ್ಮ ಗಂಗಾ ಮಾರ್ಗದರ್ಶಕ', 'சாச்சா சௌத்ரி – உங்கள் கங்கை வழிகாட்டி'],
    'avatar.stageAria': ['Chacha Chaudhary 3D Avatar Stage', 'चाचा चौधरी 3D अवतार मंच', 'ಚಾಚಾ ಚೌಧರಿ 3D ಅವತಾರ ವೇದಿಕೆ', 'சாச்சா சௌத்ரி 3D அவதார மேடை'],
    'avatar.eyebrow': ['DIGITAL AI MASCOT', 'डिजिटल एआई मैस्कॉट', 'ಡಿಜಿಟಲ್ ಎಐ ಮ್ಯಾಸ್ಕಾಟ್', 'டிஜிட்டல் ஏஐ மாஸ்காட்'],
    'avatar.loading': ['Loading Chacha New (3D GLB)...', 'चाचा का 3D मॉडल लोड हो रहा है...', 'ಚಾಚಾ ಅವರ 3D ಮಾದರಿ ಲೋಡ್ ಆಗುತ್ತಿದೆ...', 'சாச்சாவின் 3D மாதிரி ஏற்றப்படுகிறது...'],
    'avatar.loadingDetails': ['Full Rig with 28 Skeletal Animations & Lip-Sync', '28 कंकाल एनिमेशन और लिप-सिंक वाला पूर्ण मॉडल', '28 ಅಸ್ಥಿಪಂಜರ ಅನಿಮೇಷನ್ ಮತ್ತು ಲಿಪ್-ಸಿಂಕ್ ಹೊಂದಿದ ಸಂಪೂರ್ಣ ಮಾದರಿ', '28 எலும்புக்கூடு அசைவுகள் மற்றும் உதட்டசைவுடன் முழு மாதிரி'],
    'avatar.signalAria': ['Speech signal indicator', 'वॉइस संकेतक', 'ಧ್ವನಿ ಸೂಚಕ', 'குரல் குறியீடு'],
    'avatar.statusAria': ['Avatar status', 'अवतार स्थिति', 'ಅವತಾರ ಸ್ಥಿತಿ', 'அவதார நிலை'],
    'avatar.idleTitle': ['Chacha is idle and attentive', 'चाचा तैयार और ध्यान से सुन रहे हैं', 'ಚಾಚಾ ಸಿದ್ಧರಾಗಿ ಗಮನಿಸುತ್ತಿದ್ದಾರೆ', 'சாச்சா கவனமாகத் தயாராக இருக்கிறார்'],
    'avatar.listeningTitle': ['Chacha is listening to your voice', 'चाचा आपकी आवाज़ सुन रहे हैं', 'ಚಾಚಾ ನಿಮ್ಮ ಧ್ವನಿಯನ್ನು ಕೇಳುತ್ತಿದ್ದಾರೆ', 'சாச்சா உங்கள் குரலைக் கேட்கிறார்'],
    'avatar.thinkingTitle': ['Chacha is consulting the GRBMP Brain', 'चाचा GRBMP ज्ञान आधार देख रहे हैं', 'ಚಾಚಾ GRBMP ಜ್ಞಾನಸಂಗ್ರಹ ಪರಿಶೀಲಿಸುತ್ತಿದ್ದಾರೆ', 'சாச்சா GRBMP அறிவுத்தளத்தைப் பார்க்கிறார்'],
    'avatar.speakingTitle': ['Chacha is speaking with neural voice', 'चाचा प्राकृतिक आवाज़ में बोल रहे हैं', 'ಚಾಚಾ ನೈಸರ್ಗಿಕ ಧ್ವನಿಯಲ್ಲಿ ಮಾತನಾಡುತ್ತಿದ್ದಾರೆ', 'சாச்சா இயல்பான குரலில் பேசுகிறார்'],
    'avatar.listening': ['Listening', 'सुन रहा है', 'ಕೇಳುತ್ತಿದೆ', 'கேட்கிறது'],
    'avatar.thinking': ['Thinking', 'सोच रहा है', 'ಯೋಚಿಸುತ್ತಿದೆ', 'யோசிக்கிறது'],
    'avatar.speaking': ['Speaking', 'बोल रहा है', 'ಮಾತನಾಡುತ್ತಿದೆ', 'பேசுகிறது'],
    'avatar.imageAlt': ['Chacha Chaudhary avatar', 'चाचा चौधरी अवतार', 'ಚಾಚಾ ಚೌಧರಿ ಅವತಾರ', 'சாச்சா சௌத்ரி அவதாரம்'],
    'header.takeQuiz': ['Take Quiz', 'प्रश्नोत्तरी खेलें', 'ರಸಪ್ರಶ್ನೆ ಪ್ರಾರಂಭಿಸಿ', 'வினாடி வினா தொடங்கு'],
    'header.websiteLanguage': ['Website Language', 'वेबसाइट की भाषा', 'ವೆಬ್‌ಸೈಟ್ ಭಾಷೆ', 'இணையதள மொழி'],
    'header.websiteLanguageAria': ['Website language', 'वेबसाइट की भाषा', 'ವೆಬ್‌ಸೈಟ್ ಭಾಷೆ', 'இணையதள மொழி'],
    'header.outputLanguage': ['Output Language', 'उत्तर की भाषा', 'ಉತ್ತರದ ಭಾಷೆ', 'பதில் மொழி'],
    'header.outputHint': ['Select response language', 'उत्तर की भाषा चुनें', 'ಉತ್ತರದ ಭಾಷೆಯನ್ನು ಆರಿಸಿ', 'பதில் மொழியைத் தேர்ந்தெடுக்கவும்'],
    'header.voiceInput': ['Voice input', 'आवाज़ से इनपुट', 'ಧ್ವನಿ ಇನ್‌ಪುಟ್', 'குரல் உள்ளீடு'],
    'header.voiceInputAria': ['Voice input language', 'आवाज़ इनपुट की भाषा', 'ಧ್ವನಿ ಇನ್‌ಪುಟ್ ಭಾಷೆ', 'குரல் உள்ளீட்டு மொழி'],
    'header.outputAria': ['Output language', 'उत्तर की भाषा', 'ಉತ್ತರದ ಭಾಷೆ', 'பதில் மொழி'],
    'header.outputTitle': ["Select output language for Chacha's response and neural voice", 'चाचा के जवाब और आवाज़ की भाषा चुनें', 'ಚಾಚಾ ಅವರ ಉತ್ತರ ಮತ್ತು ಧ್ವನಿಯ ಭಾಷೆಯನ್ನು ಆರಿಸಿ', 'சாச்சாவின் பதில் மற்றும் குரலுக்கான மொழியைத் தேர்ந்தெடுக்கவும்'],
    'header.voiceTitle': ['Select the language spoken into the microphone', 'माइक्रोफ़ोन में बोली जाने वाली भाषा चुनें', 'ಮೈಕ್ರೊಫೋನ್‌ನಲ್ಲಿ ಮಾತನಾಡುವ ಭಾಷೆಯನ್ನು ಆರಿಸಿ', 'ஒலிவாங்கியில் பேசும் மொழியைத் தேர்ந்தெடுக்கவும்'],
    'theme.switchDark': ['Switch to dark mode', 'डार्क मोड पर जाएँ', 'ಡಾರ್ಕ್ ಮೋಡ್‌ಗೆ ಬದಲಿಸಿ', 'இருண்ட பயன்முறைக்கு மாறவும்'],
    'theme.switchLight': ['Switch to light mode', 'लाइट मोड पर जाएँ', 'ಲೈಟ್ ಮೋಡ್‌ಗೆ ಬದಲಿಸಿ', 'ஒளி பயன்முறைக்கு மாறவும்'],
    'theme.change': ['Change theme', 'थीम बदलें', 'ಥೀಮ್ ಬದಲಿಸಿ', 'தோற்றத்தை மாற்றவும்'],
    'nav.main': ['Main Navigation', 'मुख्य नेविगेशन', 'ಮುಖ್ಯ ಸಂಚರಣೆ', 'முதன்மை வழிசெலுத்தல்'],
    'nav.home': ['Home', 'होम', 'ಮುಖಪುಟ', 'முகப்பு'],
    'nav.resources': ['Ganga Resources', 'गंगा संसाधन', 'ಗಂಗಾ ಸಂಪನ್ಮೂಲಗಳು', 'கங்கை வளங்கள்'],
    'nav.resourcesTitle': ['Ganga Knowledge Base', 'गंगा ज्ञान आधार', 'ಗಂಗಾ ಜ್ಞಾನಸಂಗ್ರಹ', 'கங்கை அறிவுத்தளம்'],
    'nav.awareness': ['Awareness', 'जागरूकता', 'ಜಾಗೃತಿ', 'விழிப்புணர்வு'],
    'nav.settings': ['Settings', 'सेटिंग्स', 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', 'அமைப்புகள்'],
    'nav.about': ['About', 'परिचय', 'ಕುರಿತು', 'எங்களைப் பற்றி'],
    'chat.title': ['Ganga River Basin Assistant', 'गंगा नदी बेसिन सहायक', 'ಗಂಗಾ ನದಿ ಜಲಾನಯನ ಸಹಾಯಕ', 'கங்கை நதிப் படுகை உதவியாளர்'],
    'chat.justNow': ['Just now', 'अभी', 'ಈಗಷ್ಟೇ', 'இப்போது'],
    'chat.streamAria': ['AI conversation stream', 'एआई बातचीत', 'ಎಐ ಸಂಭಾಷಣೆ', 'ஏஐ உரையாடல்'],
    'chat.guideTag': ['Ganga Official Guide', 'गंगा आधिकारिक मार्गदर्शक', 'ಗಂಗಾ ಅಧಿಕೃತ ಮಾರ್ಗದರ್ಶಕ', 'கங்கை அதிகாரப்பூர்வ வழிகாட்டி'],
    'chat.verifiedRag': ['Verified RAG', 'सत्यापित RAG', 'ಪರಿಶೀಲಿತ RAG', 'சரிபார்க்கப்பட்ட RAG'],
    'chat.gangaGuide': ['Ganga Guide', 'गंगा मार्गदर्शक', 'ಗಂಗಾ ಮಾರ್ಗದರ್ಶಕ', 'கங்கை வழிகாட்டி'],
    'chat.typedOutput': ['Typed: {input} | Output: {output}', 'टाइप की भाषा: {input} | उत्तर: {output}', 'ಟೈಪ್ ಭಾಷೆ: {input} | ಉತ್ತರ: {output}', 'தட்டச்சு மொழி: {input} | பதில்: {output}'],
    'chat.greeting': ['Namaste! I am Chacha Chaudhary, your Ganga guide. Ask me anything about River Ganga, conservation, and water quality!', 'नमस्ते! मैं चाचा चौधरी, आपका गंगा मार्गदर्शक हूँ। गंगा नदी, संरक्षण और जल गुणवत्ता के बारे में मुझसे पूछें!', 'ನಮಸ್ಕಾರ! ನಾನು ಚಾಚಾ ಚೌಧರಿ, ನಿಮ್ಮ ಗಂಗಾ ಮಾರ್ಗದರ್ಶಕ. ಗಂಗಾ ನದಿ, ಸಂರಕ್ಷಣೆ ಮತ್ತು ನೀರಿನ ಗುಣಮಟ್ಟದ ಬಗ್ಗೆ ಕೇಳಿ!', 'வணக்கம்! நான் சாச்சா சௌத்ரி, உங்கள் கங்கை வழிகாட்டி. கங்கை நதி, பாதுகாப்பு மற்றும் நீர்த் தரம் பற்றி கேளுங்கள்!'],
    'chat.welcome': ['Namaste! I am Chacha Chaudhary, your official Ganga River guide. Ask me anything about the River Ganga basin, Namami Gange conservation initiatives, water quality standards, or the Basin Management Plan (GRBMP).', 'नमस्ते! मैं चाचा चौधरी, आपका आधिकारिक गंगा नदी मार्गदर्शक हूँ। गंगा बेसिन, नमामि गंगे संरक्षण, जल गुणवत्ता मानकों या बेसिन प्रबंधन योजना (GRBMP) के बारे में पूछें।', 'ನಮಸ್ಕಾರ! ನಾನು ಚಾಚಾ ಚೌಧರಿ, ನಿಮ್ಮ ಅಧಿಕೃತ ಗಂಗಾ ನದಿ ಮಾರ್ಗದರ್ಶಕ. ಗಂಗಾ ಜಲಾನಯನ, ನಮಾಮಿ ಗಂಗೆ ಸಂರಕ್ಷಣೆ, ನೀರಿನ ಗುಣಮಟ್ಟದ ಮಾನದಂಡಗಳು ಅಥವಾ ಜಲಾನಯನ ನಿರ್ವಹಣಾ ಯೋಜನೆ (GRBMP) ಕುರಿತು ಕೇಳಿ.', 'வணக்கம்! நான் சாச்சா சௌத்ரி, உங்கள் அதிகாரப்பூர்வ கங்கை நதி வழிகாட்டி. கங்கைப் படுகை, நமாமி கங்கே பாதுகாப்பு, நீர்த் தர அளவுகோல்கள் அல்லது படுகை மேலாண்மைத் திட்டம் (GRBMP) பற்றி கேளுங்கள்.'],
    'chat.promptTip': ['You can click any of the suggested topics below or type your question:', 'கீழே உள்ள பரிந்துரைக்கப்பட்ட தலைப்பைத் தேர்ந்தெடுக்கவும் அல்லது உங்கள் கேள்வியைத் தட்டச்சு செய்யவும்:', 'ಕೆಳಗಿನ ಸೂಚಿಸಿದ ವಿಷಯವನ್ನು ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ:', 'கீழே உள்ள பரிந்துரைக்கப்பட்ட தலைப்பைத் தேர்ந்தெடுக்கவும் அல்லது உங்கள் கேள்வியைத் தட்டச்சு செய்யவும்:'],
    'chat.sampleNamami': ['What is the mission of Namami Gange?', 'नमामि गंगे का मिशन क्या है?', 'ನಮಾಮಿ ಗಂಗೆಯ ಉದ್ದೇಶವೇನು?', 'நமாமி கங்கே திட்டத்தின் நோக்கம் என்ன?'],
    'chat.sampleClean': ['What can we do to keep River Ganga clean?', 'गंगा नदी को स्वच्छ रखने के लिए हम क्या कर सकते हैं?', 'ಗಂಗಾ ನದಿಯನ್ನು ಸ್ವಚ್ಛವಾಗಿಡಲು ನಾವು ಏನು ಮಾಡಬಹುದು?', 'கங்கை நதியைத் தூய்மையாக வைத்திருக்க நாம் என்ன செய்யலாம்?'],
    'chat.sampleQuality': ['What is the water quality at Haridwar?', 'हरिद्वार में पानी की गुणवत्ता कैसी है?', 'ಹರಿದ್ವಾರದಲ್ಲಿ ನೀರಿನ ಗುಣಮಟ್ಟ ಹೇಗಿದೆ?', 'ஹரித்வாரில் நீரின் தரம் எப்படி உள்ளது?'],
    'chat.samplePollution': ['What are the major pollution sources in River Ganga?', 'गंगा नदी में प्रदूषण के मुख्य स्रोत क्या हैं?', 'ಗಂಗಾ ನದಿಯ ಪ್ರಮುಖ ಮಾಲಿನ್ಯ ಮೂಲಗಳು ಯಾವುವು?', 'கங்கை நதியின் முக்கிய மாசு மூலங்கள் யாவை?'],
    'chat.placeholder': ['Type your question about Ganga, GRBMP, or water quality...', 'गंगा, GRBMP या जल गुणवत्ता के बारे में अपना प्रश्न लिखें...', 'ಗಂಗಾ, GRBMP ಅಥವಾ ನೀರಿನ ಗುಣಮಟ್ಟದ ಬಗ್ಗೆ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ...', 'கங்கை, GRBMP அல்லது நீர்த் தரம் பற்றி உங்கள் கேள்வியைத் தட்டச்சு செய்யவும்...'],
    'chat.askAria': ['Ask Chacha a question', 'चाचा से प्रश्न पूछें', 'ಚಾಚಾ ಅವರಿಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ', 'சாச்சாவிடம் கேள்வி கேளுங்கள்'],
    'chat.micAria': ['Microphone voice input', 'माइक्रोफ़ोन से आवाज़ इनपुट', 'ಮೈಕ್ರೊಫೋನ್ ಧ್ವನಿ ಇನ್‌ಪುಟ್', 'ஒலிவாங்கி குரல் உள்ளீடு'],
    'chat.micTitle': ['Speak through the microphone', 'माइक्रोफ़ोन से बोलें', 'ಮೈಕ್ರೊಫೋನ್ ಮೂಲಕ ಮಾತನಾಡಿ', 'ஒலிவாங்கி மூலம் பேசுங்கள்'],
    'chat.keyboardToggle': ['Toggle multilingual on-screen keyboard', 'बहुभाषी स्क्रीन कीबोर्ड दिखाएँ या छिपाएँ', 'ಬಹುಭಾಷಾ ಪರದೆ ಕೀಬೋರ್ಡ್ ತೋರಿಸಿ ಅಥವಾ ಮರೆಮಾಡಿ', 'பல்மொழி திரை விசைப்பலகையைக் காட்டு அல்லது மறை'],
    'chat.sendAria': ['Send message', 'संदेश भेजें', 'ಸಂದೇಶ ಕಳುಹಿಸಿ', 'செய்தியை அனுப்பு'],
    'chat.sendTitle': ['Send question to Chacha', 'चाचा को प्रश्न भेजें', 'ಚಾಚಾಗೆ ಪ್ರಶ್ನೆ ಕಳುಹಿಸಿ', 'சாச்சாவிடம் கேள்வியை அனுப்பு'],
    'chat.consulting': ['Consulting verified GRBMP knowledge base...', 'सत्यापित GRBMP ज्ञान आधार खोजा जा रहा है...', 'ಪರಿಶೀಲಿತ GRBMP ಜ್ಞಾನಸಂಗ್ರಹವನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...', 'சரிபார்க்கப்பட்ட GRBMP அறிவுத்தளம் பார்க்கப்படுகிறது...'],
    'chat.noResponse': ['No response received.', 'कोई जवाब नहीं मिला।', 'ಯಾವುದೇ ಉತ್ತರ ಬಂದಿಲ್ಲ.', 'பதில் எதுவும் கிடைக்கவில்லை.'],
    'chat.notice': ['Notice', 'सूचना', 'ಸೂಚನೆ', 'அறிவிப்பு'],
    'chat.requestFailed': ['I could not retrieve a response just now. Please try again.', 'अभी जवाब नहीं मिल सका। कृपया फिर कोशिश करें।', 'ಈಗ ಉತ್ತರ ಪಡೆಯಲಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', 'இப்போது பதிலைப் பெற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.'],
    'chat.sources': ['Sources', 'स्रोत', 'ಮೂಲಗಳು', 'ஆதாரங்கள்'],
    'chat.verifiedSources': ['Verified Sources', 'सत्यापित स्रोत', 'ಪರಿಶೀಲಿತ ಮೂಲಗಳು', 'சரிபார்க்கப்பட்ட ஆதாரங்கள்'],
    'chat.externalSource': ['External source', 'बाहरी स्रोत', 'ಬಾಹ್ಯ ಮೂಲ', 'வெளிப்புற ஆதாரம்'],
    'chat.grbmpDocument': ['GRBMP Document', 'GRBMP दस्तावेज़', 'GRBMP ದಾಖಲೆ', 'GRBMP ஆவணம்'],
    'chat.playAudio': ['Play voice audio', 'आवाज़ चलाएँ', 'ಧ್ವನಿ ಪ್ಲೇ ಮಾಡಿ', 'குரலை இயக்கு'],
    'chat.downloadAudio': ['Download WAV', 'WAV डाउनलोड करें', 'WAV ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ', 'WAV பதிவிறக்கு'],
    'status.idle': ['Idle', 'तैयार', 'ಸಿದ್ಧ', 'தயார்'],
    'status.listening': ['Listening...', 'सुन रहा है...', 'ಕೇಳುತ್ತಿದೆ...', 'கேட்கிறது...'],
    'status.thinking': ['Thinking...', 'सोच रहा है...', 'ಯೋಚಿಸುತ್ತಿದೆ...', 'யோசிக்கிறது...'],
    'status.analyzing': ['Analyzing...', 'विश्लेषण कर रहा है...', 'ವಿಶ್ಲೇಷಿಸುತ್ತಿದೆ...', 'ஆய்வு செய்கிறது...'],
    'status.speaking': ['Speaking...', 'बोल रहा है...', 'ಮಾತನಾಡುತ್ತಿದೆ...', 'பேசுகிறது...'],
    'status.error': ['Error', 'त्रुटि', 'ದೋಷ', 'பிழை'],
    'voice.browserUnavailable': ['Browser speech playback is unavailable.', 'ब्राउज़र में आवाज़ चलाना उपलब्ध नहीं है।', 'ಬ್ರೌಸರ್ ಧ್ವನಿ ಪ್ಲೇಬ್ಯಾಕ್ ಲಭ್ಯವಿಲ್ಲ.', 'உலாவி குரல் இயக்கம் கிடைக்கவில்லை.'],
    'voice.noVoice': ['No {locale} browser voice is available; no other-language voice was used.', '{locale} ब्राउज़र आवाज़ उपलब्ध नहीं है; दूसरी भाषा की आवाज़ इस्तेमाल नहीं की गई।', '{locale} ಬ್ರೌಸರ್ ಧ್ವನಿ ಲಭ್ಯವಿಲ್ಲ; ಬೇರೆ ಭಾಷೆಯ ಧ್ವನಿ ಬಳಸಿಲ್ಲ.', '{locale} உலாவி குரல் இல்லை; வேறு மொழிக் குரல் பயன்படுத்தப்படவில்லை.'],
    'voice.playbackFailed': ['Browser speech playback failed. Please try again.', 'ब्राउज़र आवाज़ नहीं चला सका। फिर से कोशिश करें।', 'ಬ್ರೌಸರ್ ಧ್ವನಿ ಪ್ಲೇಬ್ಯಾಕ್ ವಿಫಲವಾಗಿದೆ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', 'உலாவி குரல் இயக்கம் தோல்வியடைந்தது. மீண்டும் முயற்சிக்கவும்.'],
    'voice.audioFailed': ['Audio playback could not start. Use the play control to try again.', 'ऑडियो नहीं चला। फिर से कोशिश करने के लिए प्ले बटन दबाएँ।', 'ಆಡಿಯೊ ಪ್ಲೇ ಆಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಲು ಪ್ಲೇ ಬಟನ್ ಬಳಸಿ.', 'ஒலியை இயக்க முடியவில்லை. மீண்டும் முயற்சிக்க இயக்க பொத்தானைப் பயன்படுத்தவும்.'],
    'voice.transcribing': ['Transcribing with the configured speech provider...', 'निर्धारित वॉइस सेवा से आवाज़ लिखित रूप में बदली जा रही है...', 'ನಿಗದಿತ ಧ್ವನಿ ಸೇವೆಯಿಂದ ಮಾತನ್ನು ಪಠ್ಯಗೊಳಿಸಲಾಗುತ್ತಿದೆ...', 'கட்டமைக்கப்பட்ட குரல் சேவையால் பேச்சு உரையாக மாற்றப்படுகிறது...'],
    'voice.listeningSend': ['Listening... Speak clearly, click mic again to send.', 'सुन रहा है... साफ़ बोलें और भेजने के लिए माइक्रोफ़ोन फिर दबाएँ।', 'ಕೇಳುತ್ತಿದೆ... ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ, ಕಳುಹಿಸಲು ಮೈಕ್ ಮತ್ತೆ ಒತ್ತಿ.', 'கேட்கிறது... தெளிவாகப் பேசவும், அனுப்ப மைக்கை மீண்டும் அழுத்தவும்.'],
    'voice.heard': ['Heard: “{text}”', 'सुना: “{text}”', 'ಕೇಳಿದ್ದು: “{text}”', 'கேட்டது: “{text}”'],
    'voice.transcribed': ['Speech transcribed.', 'आवाज़ को लिखित रूप में बदला गया।', 'ಮಾತನ್ನು ಪಠ್ಯಗೊಳಿಸಲಾಗಿದೆ.', 'பேச்சு உரையாக மாற்றப்பட்டது.'],
    'voice.backendFallback': ['Backend speech recognition is unavailable; trying this browser with the selected voice-input language.', 'सर्वर पर आवाज़ पहचान उपलब्ध नहीं है; चुनी गई भाषा के साथ ब्राउज़र में कोशिश कर रहे हैं।', 'ಸರ್ವರ್ ಮಾತು ಗುರುತಿಸುವಿಕೆ ಲಭ್ಯವಿಲ್ಲ; ಆಯ್ದ ಭಾಷೆಯಲ್ಲಿ ಬ್ರೌಸರ್ ಮೂಲಕ ಪ್ರಯತ್ನಿಸಲಾಗುತ್ತಿದೆ.', 'சேவையகப் பேச்சு அறிதல் கிடைக்கவில்லை; தேர்ந்த மொழியில் உலாவியில் முயற்சிக்கப்படுகிறது.'],
    'voice.noRecognition': ['Speech recognition is unavailable. You can type your question.', 'आवाज़ पहचान उपलब्ध नहीं है। आप प्रश्न लिख सकते हैं।', 'ಮಾತು ಗುರುತಿಸುವಿಕೆ ಲಭ್ಯವಿಲ್ಲ. ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಬಹುದು.', 'பேச்சு அறிதல் கிடைக்கவில்லை. உங்கள் கேள்வியைத் தட்டச்சு செய்யலாம்.'],
    'voice.micUnsupported': ['Microphone speech recognition is not supported in this browser.', 'इस ब्राउज़र में माइक्रोफ़ोन आवाज़ पहचान उपलब्ध नहीं है।', 'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಮೈಕ್ರೊಫೋನ್ ಮಾತು ಗುರುತಿಸುವಿಕೆ ಬೆಂಬಲಿತವಲ್ಲ.', 'இந்த உலாவியில் ஒலிவாங்கிப் பேச்சு அறிதல் ஆதரிக்கப்படவில்லை.'],
    'voice.speechUnsupported': ['Speech recognition is not supported in this browser.', 'इस ब्राउज़र में आवाज़ पहचान उपलब्ध नहीं है।', 'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಮಾತು ಗುರುತಿಸುವಿಕೆ ಬೆಂಬಲಿತವಲ್ಲ.', 'இந்த உலாவியில் பேச்சு அறிதல் ஆதரிக்கப்படவில்லை.'],
    'voice.recognitionFailed': ['Speech recognition failed. Please try again.', 'आवाज़ पहचान विफल हुई। फिर कोशिश करें।', 'ಮಾತು ಗುರುತಿಸುವಿಕೆ ವಿಫಲವಾಗಿದೆ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', 'பேச்சு அறிதல் தோல்வியடைந்தது. மீண்டும் முயற்சிக்கவும்.'],
    'voice.recognitionFailedWithError': ['{error} You can type your question.', '{error} आप अपना प्रश्न लिख सकते हैं।', '{error} ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಬಹುದು.', '{error} உங்கள் கேள்வியைத் தட்டச்சு செய்யலாம்.'],
    'voice.typeQuestion': ['You can type your question.', 'आप अपना प्रश्न लिख सकते हैं।', 'ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಬಹುದು.', 'உங்கள் கேள்வியைத் தட்டச்சு செய்யலாம்.'],
    'voice.browserListening': ['Listening via browser speech recognition...', 'ब्राउज़र से आवाज़ पहचानी जा रही है...', 'ಬ್ರೌಸರ್ ಮೂಲಕ ಮಾತು ಗುರುತಿಸಲಾಗುತ್ತಿದೆ...', 'உலாவி மூலம் பேச்சு அறியப்படுகிறது...'],
    'voice.recognitionError': ['Speech recognition error: {error}', 'आवाज़ पहचान त्रुटि: {error}', 'ಮಾತು ಗುರುತಿಸುವಿಕೆ ದೋಷ: {error}', 'பேச்சு அறிதல் பிழை: {error}'],
    'resources.eyebrow': ['THE GANGA KNOWLEDGE LIBRARY', 'गंगा ज्ञान पुस्तकालय', 'ಗಂಗಾ ಜ್ಞಾನ ಗ್ರಂಥಾಲಯ', 'கங்கை அறிவு நூலகம்'],
    'resources.title': ['Ganga Resources', 'गंगा संसाधन', 'ಗಂಗಾ ಸಂಪನ್ಮೂಲಗಳು', 'கங்கை வளங்கள்'],
    'resources.description': ['Browse approved reports and source sections from the Ganga River Basin collection.', 'गंगा नदी बेसिन संग्रह की स्वीकृत रिपोर्ट और स्रोत अनुभाग देखें।', 'ಗಂಗಾ ನದಿ ಜಲಾನಯನ ಸಂಗ್ರಹದ ಅನುಮೋದಿತ ವರದಿಗಳು ಮತ್ತು ಮೂಲ ವಿಭಾಗಗಳನ್ನು ವೀಕ್ಷಿಸಿ.', 'கங்கை நதிப் படுகைத் தொகுப்பின் அங்கீகரிக்கப்பட்ட அறிக்கைகள் மற்றும் ஆதாரப் பகுதிகளைப் பாருங்கள்.'],
    'resources.browseAria': ['Browse Ganga resources', 'गंगा संसाधन देखें', 'ಗಂಗಾ ಸಂಪನ್ಮೂಲಗಳನ್ನು ವೀಕ್ಷಿಸಿ', 'கங்கை வளங்களைப் பாருங்கள்'],
    'resources.selectedAria': ['Selected document', 'चयनित दस्तावेज़', 'ಆಯ್ದ ದಾಖಲೆ', 'தேர்ந்தெடுத்த ஆவணம்'],
    'resources.searchLabel': ['Search titles, topics or source text', 'शीर्षक, विषय या स्रोत पाठ खोजें', 'ಶೀರ್ಷಿಕೆ, ವಿಷಯ ಅಥವಾ ಮೂಲ ಪಠ್ಯವನ್ನು ಹುಡುಕಿ', 'தலைப்புகள், தலைப்புப் பொருள் அல்லது ஆதார உரையைத் தேடுங்கள்'],
    'resources.searchPlaceholder': ['Search the library by topic, title or phrase', 'विषय, शीर्षक या वाक्यांश से पुस्तकालय खोजें', 'ವಿಷಯ, ಶೀರ್ಷಿಕೆ ಅಥವಾ ಪದಗುಚ್ಛದ ಮೂಲಕ ಹುಡುಕಿ', 'தலைப்பு, பொருள் அல்லது சொற்றொடரால் நூலகத்தைத் தேடுங்கள்'],
    'resources.filterAria': ['Filter resources by topic', 'विषय के अनुसार संसाधन छाँटें', 'ವಿಷಯದ ಪ್ರಕಾರ ಸಂಪನ್ಮೂಲಗಳನ್ನು ವಿಂಗಡಿಸಿ', 'தலைப்பின் அடிப்படையில் வளங்களை வடிகட்டவும்'],
    'resources.all': ['All resources', 'सभी संसाधन', 'ಎಲ್ಲಾ ಸಂಪನ್ಮೂಲಗಳು', 'அனைத்து வளங்கள்'],
    'resources.cat.basin': ['River and Basin', 'नदी और बेसिन', 'ನದಿ ಮತ್ತು ಜಲಾನಯನ', 'நதி மற்றும் படுகை'],
    'resources.cat.quality': ['Water Quality', 'जल गुणवत्ता', 'ನೀರಿನ ಗುಣಮಟ್ಟ', 'நீர்த் தரம்'],
    'resources.cat.pollution': ['Pollution', 'प्रदूषण', 'ಮಾಲಿನ್ಯ', 'மாசு'],
    'resources.cat.ecology': ['Ecology and Biodiversity', 'पारिस्थितिकी और जैव विविधता', 'ಪರಿಸರ ಮತ್ತು ಜೀವವೈವಿಧ್ಯ', 'சூழலியல் மற்றும் பல்லுயிர்'],
    'resources.cat.conservation': ['Conservation and Restoration', 'संरक्षण और पुनर्स्थापन', 'ಸಂರಕ್ಷಣೆ ಮತ್ತು ಪುನಃಸ್ಥಾಪನೆ', 'பாதுகாப்பு மற்றும் மறுசீரமைப்பு'],
    'resources.cat.governance': ['Namami Gange and Governance', 'नमामि गंगे और शासन', 'ನಮಾಮಿ ಗಂಗೆ ಮತ್ತು ಆಡಳಿತ', 'நமாமி கங்கே மற்றும் நிர்வாகம்'],
    'resources.loading': ['Loading the approved Ganga collection…', 'स्वीकृत गंगा संग्रह लोड हो रहा है…', 'ಅನುಮೋದಿತ ಗಂಗಾ ಸಂಗ್ರಹ ಲೋಡ್ ಆಗುತ್ತಿದೆ…', 'அங்கீகரிக்கப்பட்ட கங்கைத் தொகுப்பு ஏற்றப்படுகிறது…'],
    'resources.loadedCount': ['{documents} documents · {sections} sections', '{documents} दस्तावेज़ · {sections} अनुभाग', '{documents} ದಾಖಲೆಗಳು · {sections} ವಿಭಾಗಗಳು', '{documents} ஆவணங்கள் · {sections} பிரிவுகள்'],
    'resources.approvedCount': ['{count} approved documents in the library.', 'पुस्तकालय में {count} स्वीकृत दस्तावेज़ हैं।', 'ಗ್ರಂಥಾಲಯದಲ್ಲಿ {count} ಅನುಮೋದಿತ ದಾಖಲೆಗಳಿವೆ.', 'நூலகத்தில் {count} அங்கீகரிக்கப்பட்ட ஆவணங்கள் உள்ளன.'],
    'resources.source': ['Source {id}', 'स्रोत {id}', 'ಮೂಲ {id}', 'ஆதாரம் {id}'],
    'resources.approvedSource': ['Approved source document', 'स्वीकृत स्रोत दस्तावेज़', 'ಅನುಮೋದಿತ ಮೂಲ ದಾಖಲೆ', 'அங்கீகரிக்கப்பட்ட ஆதார ஆவணம்'],
    'resources.sectionsCount': ['{count} approved sections', '{count} स्वीकृत अनुभाग', '{count} ಅನುಮೋದಿತ ವಿಭಾಗಗಳು', '{count} அங்கீகரிக்கப்பட்ட பிரிவுகள்'],
    'resources.sectionsAvailable': ['{count} approved sections available to browse.', 'देखने के लिए {count} स्वीकृत अनुभाग उपलब्ध हैं।', 'ವೀಕ್ಷಿಸಲು {count} ಅನುಮೋದಿತ ವಿಭಾಗಗಳು ಲಭ್ಯವಿವೆ.', 'பார்க்க {count} அங்கீகரிக்கப்பட்ட பிரிவுகள் உள்ளன.'],
    'resources.open': ['Open document', 'दस्तावेज़ खोलें', 'ದಾಖಲೆ ತೆರೆಯಿರಿ', 'ஆவணத்தைத் திறக்கவும்'],
    'resources.searching': ['Searching approved sections…', 'स्वीकृत अनुभाग खोजे जा रहे हैं…', 'ಅನುಮೋದಿತ ವಿಭಾಗಗಳನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ…', 'அங்கீகரிக்கப்பட்ட பிரிவுகள் தேடப்படுகின்றன…'],
    'resources.searchMatches': ['{count} documents have matching approved sections.', '{count} दस्तावेज़ों में मेल खाते स्वीकृत अनुभाग हैं।', '{count} ದಾಖಲೆಗಳಲ್ಲಿ ಹೊಂದಾಣಿಕೆಯ ಅನುಮೋದಿತ ವಿಭಾಗಗಳಿವೆ.', '{count} ஆவணங்களில் பொருந்தும் அங்கீகரிக்கப்பட்ட பிரிவுகள் உள்ளன.'],
    'resources.noMatches': ['No approved sections matched that search. Try a broader term.', 'इस खोज से कोई स्वीकृत अनुभाग नहीं मिला। व्यापक शब्द आज़माएँ।', 'ಈ ಹುಡುಕಾಟಕ್ಕೆ ಅನುಮೋದಿತ ವಿಭಾಗಗಳು ಹೊಂದಿಕೆಯಾಗಲಿಲ್ಲ. ವಿಶಾಲ ಪದ ಪ್ರಯತ್ನಿಸಿ.', 'இந்தத் தேடலுக்கு அங்கீகரிக்கப்பட்ட பிரிவுகள் இல்லை. பொதுவான சொல்லை முயற்சிக்கவும்.'],
    'resources.searchFailed': ['The library search could not be completed. Check the connection and try again.', 'पुस्तकालय खोज पूरी नहीं हो सकी। कनेक्शन जाँचकर फिर कोशिश करें।', 'ಗ್ರಂಥಾಲಯ ಹುಡುಕಾಟ ಪೂರ್ಣಗೊಳ್ಳಲಿಲ್ಲ. ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', 'நூலகத் தேடலை முடிக்க முடியவில்லை. இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.'],
    'resources.connectionError': ['Request failed ({status})', 'अनुरोध विफल ({status})', 'ವಿನಂತಿ ವಿಫಲವಾಗಿದೆ ({status})', 'கோரிக்கை தோல்வியடைந்தது ({status})'],
    'resources.documentsMatched': ['{count} documents matched approved sections for {category}.', '{category} के स्वीकृत अनुभागों से {count} दस्तावेज़ मेल खाते हैं।', '{category}ಯ ಅನುಮೋದಿತ ವಿಭಾಗಗಳಿಗೆ {count} ದಾಖಲೆಗಳು ಹೊಂದಿಕೆಯಾಗಿವೆ.', '{category} அங்கீகரிக்கப்பட்ட பிரிவுகளுடன் {count} ஆவணங்கள் பொருந்தின.'],
    'resources.back': ['← Back to library', '← पुस्तकालय पर लौटें', '← ಗ್ರಂಥಾಲಯಕ್ಕೆ ಹಿಂತಿರುಗಿ', '← நூலகத்திற்குத் திரும்பு'],
    'resources.pages': ['Pages {start}–{end}', '{start}–{end} पृष्ठ', '{start}–{end} ಪುಟಗಳು', '{start}–{end} பக்கங்கள்'],
    'resources.page': ['Page {page}', 'पृष्ठ {page}', '{page}ನೇ ಪುಟ', '{page}ஆம் பக்கம்'],
    'resources.pagesUnavailable': ['Pages unavailable', 'पृष्ठ उपलब्ध नहीं', 'ಪುಟಗಳು ಲಭ್ಯವಿಲ್ಲ', 'பக்கங்கள் கிடைக்கவில்லை'],
    'resources.pageUnavailable': ['Page reference unavailable', 'पृष्ठ संदर्भ उपलब्ध नहीं', 'ಪುಟ ಉಲ್ಲೇಖ ಲಭ್ಯವಿಲ್ಲ', 'பக்கக் குறிப்பு கிடைக்கவில்லை'],
    'resources.noReadableText': ['No readable text is available for this approved section.', 'इस स्वीकृत अनुभाग का पढ़ने योग्य पाठ उपलब्ध नहीं है।', 'ಈ ಅನುಮೋದಿತ ವಿಭಾಗಕ್ಕೆ ಓದಬಹುದಾದ ಪಠ್ಯ ಲಭ್ಯವಿಲ್ಲ.', 'இந்த அங்கீகரிக்கப்பட்ட பிரிவில் படிக்கக்கூடிய உரை இல்லை.'],
    'resources.noSections': ['This approved document has no readable sections in the current index.', 'वर्तमान सूची में इस स्वीकृत दस्तावेज़ के पढ़ने योग्य अनुभाग नहीं हैं।', 'ಪ್ರಸ್ತುತ ಸೂಚ್ಯಂಕದಲ್ಲಿ ಈ ಅನುಮೋದಿತ ದಾಖಲೆಯ ಓದಬಹುದಾದ ವಿಭಾಗಗಳಿಲ್ಲ.', 'தற்போதைய குறியீட்டில் இந்த அங்கீகரிக்கப்பட்ட ஆவணத்திற்கு வாசிக்கக்கூடிய பிரிவுகள் இல்லை.'],
    'resources.opening': ['Opening approved document…', 'स्वीकृत दस्तावेज़ खोला जा रहा है…', 'ಅನುಮೋದಿತ ದಾಖಲೆ ತೆರೆಯಲಾಗುತ್ತಿದೆ…', 'அங்கீகரிக்கப்பட்ட ஆவணம் திறக்கப்படுகிறது…'],
    'resources.openFailed': ['This approved document could not be opened. Check the connection and try again.', 'यह स्वीकृत दस्तावेज़ नहीं खुला। कनेक्शन जाँचकर फिर कोशिश करें।', 'ಈ ಅನುಮೋದಿತ ದಾಖಲೆ ತೆರೆಯಲಾಗಲಿಲ್ಲ. ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.', 'இந்த அங்கீகரிக்கப்பட்ட ஆவணத்தைத் திறக்க முடியவில்லை. இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.'],
    'resources.loadFailed': ['The approved library could not be loaded. Check the connection and select Resources to retry.', 'स्वीकृत पुस्तकालय लोड नहीं हुआ। कनेक्शन जाँचें और फिर से प्रयास करने के लिए संसाधन चुनें।', 'ಅನುಮೋದಿತ ಗ್ರಂಥಾಲಯ ಲೋಡ್ ಆಗಲಿಲ್ಲ. ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಲು ಸಂಪನ್ಮೂಲಗಳನ್ನು ಆಯ್ಕೆಮಾಡಿ.', 'அங்கீகரிக்கப்பட்ட நூலகம் ஏற்றப்படவில்லை. இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்க வளங்களைத் தேர்ந்தெடுக்கவும்.'],
    'resources.loadMore': ['Show more documents', 'और दस्तावेज़ दिखाएँ', 'ಇನ್ನಷ್ಟು ದಾಖಲೆಗಳನ್ನು ತೋರಿಸಿ', 'மேலும் ஆவணங்களைக் காட்டு'],
    'awareness.eyebrow': ['LEARN FROM APPROVED SOURCES', 'स्वीकृत स्रोतों से सीखें', 'ಅನುಮೋದಿತ ಮೂಲಗಳಿಂದ ಕಲಿಯಿರಿ', 'அங்கீகரிக்கப்பட்ட ஆதாரங்களில் கற்றுக்கொள்ளுங்கள்'],
    'awareness.title': ['Ganga Awareness', 'गंगा जागरूकता', 'ಗಂಗಾ ಜಾಗೃತಿ', 'கங்கை விழிப்புணர்வு'],
    'awareness.description': ['Short source-backed readings and a knowledge check, drawn from the approved project collection.', 'स्वीकृत परियोजना संग्रह से लिए गए छोटे स्रोत-आधारित पाठ और ज्ञान जाँच।', 'ಅನುಮೋದಿತ ಯೋಜನಾ ಸಂಗ್ರಹದಿಂದ ಚಿಕ್ಕ ಮೂಲಾಧಾರಿತ ಓದುಗಳು ಮತ್ತು ಜ್ಞಾನ ಪರೀಕ್ಷೆ.', 'அங்கீகரிக்கப்பட்ட திட்டத் தொகுப்பிலிருந்து சுருக்கமான ஆதார வாசிப்புகள் மற்றும் அறிவுச் சோதனை.'],
    'awareness.intro.ganga': ['Explore source-backed information about the river’s origin, course and basin.', 'नदी के उद्गम, प्रवाह और बेसिन की स्रोत-आधारित जानकारी देखें।', 'ನದಿಯ ಮೂಲ, ಹರಿವು ಮತ್ತು ಜಲಾನಯನದ ಮೂಲಾಧಾರಿತ ಮಾಹಿತಿಯನ್ನು ತಿಳಿಯಿರಿ.', 'ஆற்றின் தோற்றம், போக்கு மற்றும் படுகை பற்றிய ஆதாரத் தகவலைப் பாருங்கள்.'],
    'awareness.intro.pollution': ['Learn how approved Ganga Basin reports describe pollutant pathways and sources.', 'स्वीकृत गंगा बेसिन रिपोर्टों में बताए गए प्रदूषण के मार्ग और स्रोत जानें।', 'ಅನುಮೋದಿತ ಗಂಗಾ ಜಲಾನಯನ ವರದಿಗಳಲ್ಲಿ ವಿವರಿಸಿದ ಮಾಲಿನ್ಯ ಮಾರ್ಗಗಳು ಮತ್ತು ಮೂಲಗಳನ್ನು ತಿಳಿಯಿರಿ.', 'அங்கீகரிக்கப்பட்ட கங்கைப் படுகை அறிக்கைகள் கூறும் மாசு வழிகளையும் மூலங்களையும் அறியுங்கள்.'],
    'awareness.intro.protect': ['Review actions recommended in the approved ecological restoration material.', 'स्वीकृत पारिस्थितिकी पुनर्स्थापन सामग्री में सुझाए गए उपाय देखें।', 'ಅನುಮೋದಿತ ಪರಿಸರ ಪುನಃಸ್ಥಾಪನಾ ಮಾಹಿತಿಯಲ್ಲಿರುವ ಕ್ರಮಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.', 'அங்கீகரிக்கப்பட்ட சூழலியல் மறுசீரமைப்பு உள்ளடக்கத்தில் பரிந்துரைக்கப்பட்ட செயல்களைப் பாருங்கள்.'],
    'awareness.intro.myth': ['Check a reviewed statement against the cited GRBMP passage. This is a source check, not a claim about a widespread myth.', 'उद्धृत GRBMP अंश से कथन की जाँच करें। यह स्रोत-जाँच है, किसी प्रचलित मिथक का दावा नहीं।', 'ಉಲ್ಲೇಖಿತ GRBMP ಭಾಗದೊಂದಿಗೆ ಪರಿಶೀಲಿತ ಹೇಳಿಕೆಯನ್ನು ಹೋಲಿಸಿ. ಇದು ಮೂಲ ಪರಿಶೀಲನೆ ಮಾತ್ರ; ವ್ಯಾಪಕ ಮಿಥ್ಯೆಯ ಹೇಳಿಕೆಯಲ್ಲ.', 'மேற்கோள் காட்டிய GRBMP பகுதியுடன் கூற்றைச் சரிபார்க்கவும். இது ஆதாரச் சரிபார்ப்பு மட்டுமே; பரவலான கட்டுக்கதை பற்றிய கூற்று அல்ல.'],
    'awareness.topic.ganga': ['Know Your Ganga', 'अपनी गंगा को जानें', 'ನಿಮ್ಮ ಗಂಗೆಯನ್ನು ತಿಳಿಯಿರಿ', 'உங்கள் கங்கையை அறிந்துகொள்ளுங்கள்'],
    'awareness.topic.gangaDesc': ['Origins, course and basin', 'उद्गम, प्रवाह और बेसिन', 'ಮೂಲ, ಹರಿವು ಮತ್ತು ಜಲಾನಯನ', 'தோற்றம், போக்கு மற்றும் படுகை'],
    'awareness.topic.pollution': ['Pollution Awareness', 'प्रदूषण जागरूकता', 'ಮಾಲಿನ್ಯ ಜಾಗೃತಿ', 'மாசு விழிப்புணர்வு'],
    'awareness.topic.pollutionDesc': ['How pollutants enter rivers', 'प्रदूषक नदियों तक कैसे पहुँचते हैं', 'ಮಾಲಿನ್ಯಕಾರಕಗಳು ನದಿಗೆ ಹೇಗೆ ಸೇರುತ್ತವೆ', 'மாசுகள் ஆறுகளை எவ்வாறு அடைகின்றன'],
    'awareness.topic.protect': ['Protect the River', 'नदी की रक्षा करें', 'ನದಿಯನ್ನು ರಕ್ಷಿಸಿ', 'நதியைப் பாதுகாப்போம்'],
    'awareness.topic.protectDesc': ['Restoration actions in the plans', 'योजनाओं में दिए गए पुनर्स्थापन उपाय', 'ಯೋಜನೆಗಳಲ್ಲಿನ ಪುನಃಸ್ಥಾಪನಾ ಕ್ರಮಗಳು', 'திட்டங்களில் உள்ள மறுசீரமைப்பு நடவடிக்கைகள்'],
    'awareness.topic.myth': ['Myth vs Fact', 'मिथक और तथ्य', 'ಮಿಥ್ಯೆ ಮತ್ತು ಸತ್ಯ', 'கட்டுக்கதை மற்றும் உண்மை'],
    'awareness.topic.mythDesc': ['Check a claim against a source', 'स्रोत से दावे की जाँच करें', 'ಮೂಲದೊಂದಿಗೆ ಹೇಳಿಕೆಯನ್ನು ಪರಿಶೀಲಿಸಿ', 'ஆதாரத்துடன் கூற்றைச் சரிபார்க்கவும்'],
    'awareness.topic.quiz': ['Test Your Knowledge', 'अपना ज्ञान जाँचें', 'ನಿಮ್ಮ ಜ್ಞಾನ ಪರೀಕ್ಷಿಸಿ', 'உங்கள் அறிவைச் சோதிக்கவும்'],
    'awareness.topic.quizDesc': ['Open the existing Ganga quiz', 'गंगा प्रश्नोत्तरी खोलें', 'ಗಂಗಾ ರಸಪ್ರಶ್ನೆ ತೆರೆಯಿರಿ', 'கங்கை வினாடி வினாவைத் திறக்கவும்'],
    'awareness.topicsAria': ['Awareness topics', 'जागरूकता विषय', 'ಜಾಗೃತಿ ವಿಷಯಗಳು', 'விழிப்புணர்வு தலைப்புகள்'],
    'awareness.initial': ['Choose a topic to explore source-backed information.', 'स्रोत-आधारित जानकारी देखने के लिए विषय चुनें।', 'ಮೂಲಾಧಾರಿತ ಮಾಹಿತಿಗಾಗಿ ವಿಷಯ ಆಯ್ಕೆಮಾಡಿ.', 'ஆதாரத் தகவலைப் பார்க்க ஒரு தலைப்பைத் தேர்ந்தெடுக்கவும்.'],
    'awareness.loading': ['Finding approved learning sources…', 'स्वीकृत शिक्षण स्रोत खोजे जा रहे हैं…', 'ಅನುಮೋದಿತ ಕಲಿಕಾ ಮೂಲಗಳನ್ನು ಹುಡುಕಲಾಗುತ್ತಿದೆ…', 'அங்கீகரிக்கப்பட்ட கற்றல் ஆதாரங்கள் தேடப்படுகின்றன…'],
    'awareness.noLesson': ['The approved collection does not currently have a matching lesson for {topic}.', 'स्वीकृत संग्रह में अभी {topic} से जुड़ा पाठ उपलब्ध नहीं है।', 'ಅನುಮೋದಿತ ಸಂಗ್ರಹದಲ್ಲಿ ಈಗ {topic}ಗೆ ಹೊಂದುವ ಪಾಠವಿಲ್ಲ.', 'அங்கீகரிக்கப்பட்ட தொகுப்பில் தற்போது {topic} தொடர்பான பாடம் இல்லை.'],
    'awareness.notEnough': ['The matching passages did not contain enough clean readable text for a lesson.', 'मिले हुए अंशों में पाठ के लिए पर्याप्त स्पष्ट पाठ नहीं था।', 'ಹೊಂದಿದ ಭಾಗಗಳಲ್ಲಿ ಪಾಠಕ್ಕೆ ಸಾಕಷ್ಟು ಸ್ಪಷ್ಟ ಪಠ್ಯವಿಲ್ಲ.', 'பொருந்திய பகுதிகளில் பாடத்திற்குப் போதுமான தெளிவான உரை இல்லை.'],
    'awareness.loadFailed': ['Awareness sources could not be loaded. Check the connection and select this topic to retry.', 'जागरूकता स्रोत लोड नहीं हुए। कनेक्शन जाँचें और फिर कोशिश के लिए विषय चुनें।', 'ಜಾಗೃತಿ ಮೂಲಗಳು ಲೋಡ್ ಆಗಲಿಲ್ಲ. ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಲು ವಿಷಯ ಆಯ್ಕೆಮಾಡಿ.', 'விழிப்புணர்வு ஆதாரங்கள் ஏற்றப்படவில்லை. இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்க தலைப்பைத் தேர்ந்தெடுக்கவும்.'],
    'awareness.retry': ['Retry', 'फिर कोशिश करें', 'ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ', 'மீண்டும் முயற்சி'],
    'awareness.lessonEyebrow': ['SOURCE-BASED LESSON', 'स्रोत-आधारित पाठ', 'ಮೂಲಾಧಾರಿತ ಪಾಠ', 'ஆதார அடிப்படையிலான பாடம்'],
    'awareness.sourceSection': ['Approved source section', 'स्वीकृत स्रोत अनुभाग', 'ಅನುಮೋದಿತ ಮೂಲ ವಿಭಾಗ', 'அங்கீகரிக்கப்பட்ட ஆதாரப் பகுதி'],
    'awareness.source': ['Source: {source}', 'स्रोत: {source}', 'ಮೂಲ: {source}', 'ஆதாரம்: {source}'],
    'awareness.readSection': ['Read this approved section', 'यह स्वीकृत अनुभाग पढ़ें', 'ಈ ಅನುಮೋದಿತ ವಿಭಾಗ ಓದಿ', 'இந்த அங்கீகரிக்கப்பட்ட பகுதியைப் படிக்கவும்'],
    'awareness.readFullSection': ['Read the full source section', 'पूरा स्रोत अनुभाग पढ़ें', 'ಪೂರ್ಣ ಮೂಲ ವಿಭಾಗ ಓದಿ', 'முழு ஆதாரப் பகுதியைப் படிக்கவும்'],
    'awareness.claimEyebrow': ['Reviewed claim · answer using this source', 'समीक्षित दावा · इस स्रोत से उत्तर दें', 'ಪರಿಶೀಲಿತ ಹೇಳಿಕೆ · ಈ ಮೂಲದಿಂದ ಉತ್ತರಿಸಿ', 'மதிப்பாய்வு செய்யப்பட்ட கூற்று · இந்த ஆதாரத்தைக் கொண்டு பதிலளிக்கவும்'],
    'awareness.claimText': ['The GRBMP defines the Ganga as including six main Himalayan headstreams.', 'GRBMP के अनुसार गंगा में हिमालय की छह मुख्य धाराएँ शामिल हैं।', 'GRBMP ಪ್ರಕಾರ ಗಂಗೆಯು ಹಿಮಾಲಯದ ಆರು ಪ್ರಮುಖ ಉಪನದಿಗಳನ್ನು ಒಳಗೊಂಡಿದೆ.', 'GRBMP-இன்படி கங்கையில் இமயமலையின் ஆறு முக்கியத் தலைநீரோடைகள் அடங்கும்.'],
    'awareness.claimNote': ['This statement is checked against one cited passage; it is not presented as a widespread myth.', 'इस कथन की जाँच एक उद्धृत अंश से की गई है; इसे प्रचलित मिथक नहीं कहा जा रहा।', 'ಈ ಹೇಳಿಕೆಯನ್ನು ಒಂದು ಉಲ್ಲೇಖಿತ ಭಾಗದೊಂದಿಗೆ ಪರಿಶೀಲಿಸಲಾಗಿದೆ; ಇದು ವ್ಯಾಪಕ ಮಿಥ್ಯೆ ಎಂದು ಹೇಳಲಾಗುವುದಿಲ್ಲ.', 'இந்தக் கூற்று மேற்கோள் காட்டிய ஒரு பகுதியுடன் சரிபார்க்கப்படுகிறது; இது பரவலான கட்டுக்கதை என்று கூறப்படவில்லை.'],
    'awareness.choose': ['Choose Myth or Fact to reveal the source-based answer.', 'स्रोत-आधारित उत्तर देखने के लिए मिथक या तथ्य चुनें।', 'ಮೂಲಾಧಾರಿತ ಉತ್ತರಕ್ಕಾಗಿ ಮಿಥ್ಯೆ ಅಥವಾ ಸತ್ಯ ಆಯ್ಕೆಮಾಡಿ.', 'ஆதாரப் பதிலைக் காண கட்டுக்கதை அல்லது உண்மை என்பதைத் தேர்ந்தெடுக்கவும்.'],
    'awareness.myth': ['Myth', 'मिथक', 'ಮಿಥ್ಯೆ', 'கட்டுக்கதை'],
    'awareness.fact': ['Fact', 'तथ्य', 'ಸತ್ಯ', 'உண்மை'],
    'awareness.factResult': ['Fact — the cited GRBMP section states this.', 'तथ्य — उद्धृत GRBMP अनुभाग यही बताता है।', 'ಸತ್ಯ — ಉಲ್ಲೇಖಿತ GRBMP ವಿಭಾಗ ಇದನ್ನೇ ಹೇಳುತ್ತದೆ.', 'உண்மை — மேற்கோள் காட்டிய GRBMP பகுதி இதையே கூறுகிறது.'],
    'awareness.factSupported': ['The cited GRBMP section supports this as a fact.', 'उद्धृत GRBMP अनुभाग इसे तथ्य के रूप में समर्थन देता है।', 'ಉಲ್ಲೇಖಿತ GRBMP ವಿಭಾಗ ಇದನ್ನು ಸತ್ಯವೆಂದು ಬೆಂಬಲಿಸುತ್ತದೆ.', 'மேற்கோள் காட்டிய GRBMP பகுதி இதை உண்மையாக ஆதரிக்கிறது.'],
    'awareness.status': ['{topic} · learning points are taken from the cited approved sections.', '{topic} · सीखने के बिंदु उद्धृत स्वीकृत अनुभागों से लिए गए हैं।', '{topic} · ಕಲಿಕಾ ಅಂಶಗಳು ಉಲ್ಲೇಖಿತ ಅನುಮೋದಿತ ವಿಭಾಗಗಳಿಂದ ಪಡೆದವು.', '{topic} · கற்றல் குறிப்புகள் மேற்கோள் காட்டிய அங்கீகரிக்கப்பட்ட பகுதிகளிலிருந்து எடுக்கப்பட்டவை.'],
    'awareness.searchError': ['Search failed ({status})', 'खोज विफल ({status})', 'ಹುಡುಕಾಟ ವಿಫಲವಾಗಿದೆ ({status})', 'தேடல் தோல்வியடைந்தது ({status})'],
    'settings.eyebrow': ['YOUR PREFERENCES', 'आपकी प्राथमिकताएँ', 'ನಿಮ್ಮ ಆದ್ಯತೆಗಳು', 'உங்கள் விருப்பங்கள்'],
    'settings.title': ['Settings', 'सेटिंग्स', 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು', 'அமைப்புகள்'],
    'settings.description': ['These preferences are saved on this device and shared with the controls in the header.', 'ये प्राथमिकताएँ इस डिवाइस पर सहेजी जाती हैं और हेडर के नियंत्रणों से जुड़ी हैं।', 'ಈ ಆದ್ಯತೆಗಳು ಈ ಸಾಧನದಲ್ಲಿ ಉಳಿಯುತ್ತವೆ ಮತ್ತು ಹೆಡರ್ ನಿಯಂತ್ರಣಗಳೊಂದಿಗೆ ಹಂಚಿಕೊಳ್ಳಲ್ಪಡುತ್ತವೆ.', 'இந்த விருப்பங்கள் இந்தச் சாதனத்தில் சேமிக்கப்பட்டு தலைப்புப் பட்டி கட்டுப்பாடுகளுடன் பகிரப்படும்.'],
    'settings.appearance': ['Appearance', 'रूप', 'ನೋಟ', 'தோற்றம்'],
    'settings.appearanceDescription': ['Choose light or dark appearance. Your selection is saved across visits.', 'लाइट या डार्क रूप चुनें। आपकी पसंद अगली बार के लिए सहेजी जाएगी।', 'ಲೈಟ್ ಅಥವಾ ಡಾರ್ಕ್ ನೋಟ ಆರಿಸಿ. ನಿಮ್ಮ ಆಯ್ಕೆ ಉಳಿಸಲಾಗುತ್ತದೆ.', 'ஒளி அல்லது இருண்ட தோற்றத்தைத் தேர்ந்தெடுக்கவும். உங்கள் தேர்வு சேமிக்கப்படும்.'],
    'settings.defaultOutput': ['Default response language', 'डिफ़ॉल्ट उत्तर भाषा', 'ಡೀಫಾಲ್ಟ್ ಉತ್ತರ ಭಾಷೆ', 'இயல்புநிலை பதில் மொழி'],
    'settings.outputDescription': ["Sets the language used for Chacha's answers and speech.", 'चाचा के उत्तर और आवाज़ की भाषा तय करता है।', 'ಚಾಚಾ ಅವರ ಉತ್ತರ ಮತ್ತು ಮಾತಿನ ಭಾಷೆಯನ್ನು ಹೊಂದಿಸುತ್ತದೆ.', 'சாச்சாவின் பதில்கள் மற்றும் பேச்சுக்கான மொழியை அமைக்கிறது.'],
    'settings.voiceInput': ['Voice input language', 'आवाज़ इनपुट भाषा', 'ಧ್ವನಿ ಇನ್‌ಪುಟ್ ಭಾಷೆ', 'குரல் உள்ளீட்டு மொழி'],
    'settings.voiceDescription': ['Choose the language spoken into the microphone. Available recognition depends on the configured speech provider.', 'माइक्रोफ़ोन में बोली जाने वाली भाषा चुनें। पहचान की सुविधा निर्धारित वॉइस सेवा पर निर्भर है।', 'ಮೈಕ್ರೊಫೋನ್‌ನಲ್ಲಿ ಮಾತನಾಡುವ ಭಾಷೆಯನ್ನು ಆರಿಸಿ. ಗುರುತಿಸುವಿಕೆ ನಿಗದಿತ ಧ್ವನಿ ಸೇವೆಯನ್ನು ಅವಲಂಬಿಸಿದೆ.', 'ஒலிவாங்கியில் பேசும் மொழியைத் தேர்ந்தெடுக்கவும். அறிதல் வசதி கட்டமைக்கப்பட்ட குரல் வழங்குநரைப் பொறுத்தது.'],
    'settings.accessibility': ['Accessibility', 'सुलभता', 'ಪ್ರವೇಶಸಾಧ್ಯತೆ', 'அணுகல்தன்மை'],
    'settings.accessibilityDescription': ['Keyboard navigation, visible focus indicators, semantic labels and the multilingual on-screen keyboard are available throughout the application.', 'पूरे ऐप में कीबोर्ड नेविगेशन, स्पष्ट फ़ोकस संकेत, अर्थपूर्ण लेबल और बहुभाषी स्क्रीन कीबोर्ड उपलब्ध हैं।', 'ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಕೀಬೋರ್ಡ್ ಸಂಚರಣೆ, ಗೋಚರ ಫೋಕಸ್ ಸೂಚಕಗಳು, ಅರ್ಥಪೂರ್ಣ ಲೇಬಲ್‌ಗಳು ಮತ್ತು ಬಹುಭಾಷಾ ಪರದೆ ಕೀಬೋರ್ಡ್ ಲಭ್ಯವಿವೆ.', 'பயன்பாடு முழுவதும் விசைப்பலகை வழிசெலுத்தல், தெளிவான கவனக் குறியீடுகள், பொருள் கொண்ட லேபிள்கள் மற்றும் பல்மொழி திரை விசைப்பலகை கிடைக்கின்றன.'],
    'about.eyebrow': ['PROJECT INFORMATION', 'परियोजना जानकारी', 'ಯೋಜನಾ ಮಾಹಿತಿ', 'திட்டத் தகவல்'],
    'about.title': ['About Ganga AI Mascot', 'गंगा एआई मैस्कॉट के बारे में', 'ಗಂಗಾ ಎಐ ಮ್ಯಾಸ್ಕಾಟ್ ಕುರಿತು', 'கங்கை ஏஐ மாஸ்காட் பற்றி'],
    'about.projectId': ['Project ID:', 'परियोजना आईडी:', 'ಯೋಜನಾ ಐಡಿ:', 'திட்ட அடையாளம்:'],
    'about.officialTitle': ['Official title:', 'आधिकारिक शीर्षक:', 'ಅಧಿಕೃತ ಶೀರ್ಷಿಕೆ:', 'அதிகாரப்பூர்வ தலைப்பு:'],
    'about.description': ['The project brings together the Chacha Chaudhary digital avatar, a retrieval-augmented knowledge service, speech features and multilingual support.', 'यह परियोजना चाचा चौधरी डिजिटल अवतार, स्रोत-आधारित ज्ञान सेवा, वॉइस सुविधाओं और बहुभाषी सहायता को जोड़ती है।', 'ಈ ಯೋಜನೆ ಚಾಚಾ ಚೌಧರಿ ಡಿಜಿಟಲ್ ಅವತಾರ, ಆಧಾರಿತ ಜ್ಞಾನ ಸೇವೆ, ಧ್ವನಿ ವೈಶಿಷ್ಟ್ಯಗಳು ಮತ್ತು ಬಹುಭಾಷಾ ಬೆಂಬಲವನ್ನು ಒಟ್ಟುಗೂಡಿಸುತ್ತದೆ.', 'இந்தத் திட்டம் சாச்சா சௌத்ரி டிஜிட்டல் அவதாரம், ஆதார அறிவுச் சேவை, குரல் அம்சங்கள் மற்றும் பல்மொழி ஆதரவை ஒன்றிணைக்கிறது.'],
    'footer.brand': ['Ganga AI Mascot · Chacha Chaudhary', 'गंगा एआई मैस्कॉट · चाचा चौधरी', 'ಗಂಗಾ ಎಐ ಮ್ಯಾಸ್ಕಾಟ್ · ಚಾಚಾ ಚೌಧರಿ', 'கங்கை ஏஐ மாஸ்காட் · சாச்சா சௌத்ரி'],
    'quiz.eyebrow': ['NAMAMI GANGE AWARENESS', 'नमामि गंगे जागरूकता', 'ನಮಾಮಿ ಗಂಗೆ ಜಾಗೃತಿ', 'நமாமி கங்கே விழிப்புணர்வு'],
    'quiz.title': ['Ganga River Knowledge Quiz', 'गंगा नदी ज्ञान प्रश्नोत्तरी', 'ಗಂಗಾ ನದಿ ಜ್ಞಾನ ರಸಪ್ರಶ್ನೆ', 'கங்கை நதி அறிவு வினாடி வினா'],
    'quiz.back': ['✕ Back to Chat', '✕ चैट पर लौटें', '✕ ಚಾಟ್‌ಗೆ ಹಿಂತಿರುಗಿ', '✕ உரையாடலுக்குத் திரும்பு'],
    'quiz.choose': ['Choose one answer', 'एक उत्तर चुनें', 'ಒಂದು ಉತ್ತರ ಆಯ್ಕೆಮಾಡಿ', 'ஒரு பதிலைத் தேர்ந்தெடுக்கவும்'],
    'quiz.questionCount': ['Question {number} of {total}', 'प्रश्न {number} / {total}', 'ಪ್ರಶ್ನೆ {number} / {total}', 'கேள்வி {number} / {total}'],
    'quiz.score': ['Score {score} / {total}', 'अंक {score} / {total}', 'ಅಂಕ {score} / {total}', 'மதிப்பெண் {score} / {total}'],
    'quiz.answered': ['{count} of {total} questions answered', '{total} में से {count} प्रश्नों के उत्तर दिए', '{total}ರಲ್ಲಿ {count} ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಲಾಗಿದೆ', '{total} கேள்விகளில் {count}க்கு பதிலளிக்கப்பட்டது'],
    'quiz.correctAnswer': ['Correct answer', 'सही उत्तर', 'ಸರಿಯಾದ ಉತ್ತರ', 'சரியான பதில்'],
    'quiz.yourAnswer': ['Your answer', 'आपका उत्तर', 'ನಿಮ್ಮ ಉತ್ತರ', 'உங்கள் பதில்'],
    'quiz.correct': ['Correct!', 'सही!', 'ಸರಿ!', 'சரி!'],
    'quiz.notQuite': ['Not quite', 'पूरी तरह सही नहीं', 'ಅಷ್ಟು ಸರಿಯಲ್ಲ', 'சரியில்லை'],
    'quiz.answerPrefix': ['Correct answer: {answer}', 'सही उत्तर: {answer}', 'ಸರಿಯಾದ ಉತ್ತರ: {answer}', 'சரியான பதில்: {answer}'],
    'quiz.source': ['Source: {source}', 'स्रोत: {source}', 'ಮೂಲ: {source}', 'ஆதாரம்: {source}'],
    'quiz.submit': ['Submit Answer', 'उत्तर जमा करें', 'ಉತ್ತರ ಸಲ್ಲಿಸಿ', 'பதிலைச் சமர்ப்பிக்கவும்'],
    'quiz.next': ['Next Question', 'अगला प्रश्न', 'ಮುಂದಿನ ಪ್ರಶ್ನೆ', 'அடுத்த கேள்வி'],
    'quiz.results': ['See Results', 'परिणाम देखें', 'ಫಲಿತಾಂಶ ನೋಡಿ', 'முடிவுகளைக் காண்க'],
    'quiz.complete': ['Quiz complete!', 'प्रश्नोत्तरी पूरी हुई!', 'ರಸಪ್ರಶ್ನೆ ಪೂರ್ಣಗೊಂಡಿದೆ!', 'வினாடி வினா முடிந்தது!'],
    'quiz.yourScore': ['Your score: {score} out of {total}', 'आपका अंक: {total} में से {score}', 'ನಿಮ್ಮ ಅಂಕ: {total}ರಲ್ಲಿ {score}', 'உங்கள் மதிப்பெண்: {total}ல் {score}'],
    'quiz.thanks': ['Thanks for learning about the Ganga. Keep exploring and sharing what you learned!', 'गंगा के बारे में सीखने के लिए धन्यवाद। सीखते रहें और जानकारी साझा करें!', 'ಗಂಗೆಯ ಕುರಿತು ಕಲಿತಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದ. ಅನ್ವೇಷಿಸಿ, ಕಲಿತದ್ದನ್ನು ಹಂಚಿಕೊಳ್ಳಿ!', 'கங்கை பற்றி கற்றதற்கு நன்றி. தொடர்ந்து அறிந்து கற்றதைப் பகிருங்கள்!'],
    'quiz.retry': ['Retry Quiz', 'फिर से खेलें', 'ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ', 'மீண்டும் விளையாடு'],
    'quiz.restarted': ['Quiz restarted.', 'प्रश्नोत्तरी फिर शुरू हुई।', 'ರಸಪ್ರಶ್ನೆ ಮರುಪ್ರಾರಂಭಿಸಲಾಗಿದೆ.', 'வினாடி வினா மீண்டும் தொடங்கப்பட்டது.'],
    'quiz.correctAnnounce': ['Correct answer.', 'सही उत्तर।', 'ಸರಿಯಾದ ಉತ್ತರ.', 'சரியான பதில்.'],
    'quiz.incorrectAnnounce': ['Incorrect answer.', 'गलत उत्तर।', 'ತಪ್ಪಾದ ಉತ್ತರ.', 'தவறான பதில்.'],
    'quiz.scoreAnnounce': ['Quiz score: {score} out of {total}.', 'प्रश्नोत्तरी अंक: {total} में से {score}.', 'ರಸಪ್ರಶ್ನೆ ಅಂಕ: {total}ರಲ್ಲಿ {score}.', 'வினாடி வினா மதிப்பெண்: {total}ல் {score}.'],
    'keyboard.title': ['Multilingual Keyboard', 'बहुभाषी कीबोर्ड', 'ಬಹುಭಾಷಾ ಕೀಬೋರ್ಡ್', 'பல்மொழி விசைப்பலகை'],
    'keyboard.onScreen': ['On-Screen Keyboard', 'स्क्रीन कीबोर्ड', 'ಪರದೆ ಕೀಬೋರ್ಡ್', 'திரை விசைப்பலகை'],
    'keyboard.close': ['Close on-screen keyboard', 'स्क्रीन कीबोर्ड बंद करें', 'ಪರದೆ ಕೀಬೋರ್ಡ್ ಮುಚ್ಚಿ', 'திரை விசைப்பலகையை மூடவும்'],
    'keyboard.closeTitle': ['Close Keyboard', 'कीबोर्ड बंद करें', 'ಕೀಬೋರ್ಡ್ ಮುಚ್ಚಿ', 'விசைப்பலகையை மூடு'],
    'keyboard.numbers': ['Numbers and Symbols', 'अंक और चिह्न', 'ಅಂಕಿಗಳು ಮತ್ತು ಚಿಹ್ನೆಗಳು', 'எண்கள் மற்றும் குறியீடுகள்'],
    'keyboard.shift': ['Vowels / Matras or Shift', 'स्वर / मात्राएँ या शिफ्ट', 'ಸ್ವರಗಳು / ಮಾತ್ರೆಗಳು ಅಥವಾ ಶಿಫ್ಟ್', 'உயிரெழுத்துகள் / குறியீடுகள் அல்லது ஷிப்ட்'],
    'keyboard.emojis': ['Ganga Emojis & Quick Words', 'गंगा इमोजी और त्वरित शब्द', 'ಗಂಗಾ ಎಮೋಜಿ ಮತ್ತು ತ್ವರಿತ ಪದಗಳು', 'கங்கை எமோஜிகள் மற்றும் விரைவு சொற்கள்'],
    'keyboard.space': ['Space', 'स्पेस', 'ಸ್ಪೇಸ್', 'இடைவெளி'],
    'keyboard.left': ['Cursor Left', 'कर्सर बाएँ', 'ಕರ್ಸರ್ ಎಡಕ್ಕೆ', 'சுட்டியை இடப்புறம் நகர்த்து'],
    'keyboard.right': ['Cursor Right', 'कर्सर दाएँ', 'ಕರ್ಸರ್ ಬಲಕ್ಕೆ', 'சுட்டியை வலப்புறம் நகர்த்து'],
    'keyboard.send': ['Send Question', 'प्रश्न भेजें', 'ಪ್ರಶ್ನೆ ಕಳುಹಿಸಿ', 'கேள்வியை அனுப்பு'],
    'modal.closeCpcb': ['Close CPCB Table', 'CPCB तालिका बंद करें', 'CPCB ಕೋಷ್ಟಕ ಮುಚ್ಚಿ', 'CPCB அட்டவணையை மூடவும்'],
    'modal.cpcbTitle': ['CPCB Water Quality Classification Criteria', 'CPCB जल गुणवत्ता वर्गीकरण मानदंड', 'CPCB ನೀರಿನ ಗುಣಮಟ್ಟ ವರ್ಗೀಕರಣ ಮಾನದಂಡಗಳು', 'CPCB நீர்த் தர வகைப்பாட்டு அளவுகோல்கள்'],
    'table.waterQuality': ['Water quality', 'जल गुणवत्ता', 'ನೀರಿನ ಗುಣಮಟ್ಟ', 'நீர்த் தரம்'],
    'table.waterLevel': ['Water level and depth', 'जल स्तर और गहराई', 'ನೀರಿನ ಮಟ್ಟ ಮತ್ತು ಆಳ', 'நீர் மட்டம் மற்றும் ஆழம்'],
    'table.station': ['Station', 'केंद्र', 'ನಿಲ್ದಾಣ', 'நிலையம்'],
    'table.parameter': ['Parameter', 'मापदंड', 'ನಿಯತಾಂಕ', 'அளவுரு'],
    'table.value': ['Value', 'मान', 'ಮೌಲ್ಯ', 'மதிப்பு'],
    'table.status': ['Status', 'स्थिति', 'ಸ್ಥಿತಿ', 'நிலை'],
    'table.timestamp': ['Timestamp', 'समय-मुद्रा', 'ಸಮಯಮುದ್ರೆ', 'நேரமுத்திரை'],
    'table.source': ['Source', 'स्रोत', 'ಮೂಲ', 'ஆதாரம்'],
    'table.riverStage': ['River stage (m)', 'नदी का जलस्तर (m)', 'ನದಿಯ ನೀರಿನ ಮಟ್ಟ (m)', 'ஆற்றின் நீர்மட்டம் (m)'],
    'table.depth': ['Depth (m)', 'गहराई (m)', 'ಆಳ (m)', 'ஆழம் (m)'],
    'table.na': ['N/A', 'उपलब्ध नहीं', 'ಲಭ್ಯವಿಲ್ಲ', 'கிடைக்கவில்லை'],
    'table.meetsClassB': ['Meets Class B', 'Class B मानदंड पूरा', 'Class B ಮಾನದಂಡ ಪೂರೈಸುತ್ತದೆ', 'Class B அளவுகோலைப் பூர்த்தி செய்கிறது'],
    'table.outsideClassB': ['Outside Class B', 'Class B से बाहर', 'Class B ವ್ಯಾಪ್ತಿಗೆ ಹೊರಗೆ', 'Class B வரம்பிற்கு வெளியே'],
    'table.unavailable': ['Unavailable', 'उपलब्ध नहीं', 'ಲಭ್ಯವಿಲ್ಲ', 'கிடைக்கவில்லை'],
    'table.stale': ['Stale reading', 'पुरानी रीडिंग', 'ಹಳೆಯ ಅಳತೆ', 'பழைய அளவீடு'],
    'table.belowWarning': ['Below warning', 'चेतावनी स्तर से नीचे', 'ಎಚ್ಚರಿಕೆ ಮಟ್ಟಕ್ಕಿಂತ ಕೆಳಗೆ', 'எச்சரிக்கை நிலைக்குக் கீழே'],
    'table.warning': ['Warning', 'चेतावनी', 'ಎಚ್ಚರಿಕೆ', 'எச்சரிக்கை'],
    'table.danger': ['Danger', 'खतरा', 'ಅಪಾಯ', 'ஆபத்து'],
    'table.atDanger': ['At/above danger', 'खतरे के स्तर पर या ऊपर', 'ಅಪಾಯದ ಮಟ್ಟದಲ್ಲಿ ಅಥವಾ ಮೇಲಿದೆ', 'ஆபத்து நிலையில் அல்லது அதற்கு மேல்'],
    'table.fresh': ['Fresh', 'ताज़ा रीडिंग', 'ಹೊಸ ಅಳತೆ', 'புதிய அளவீடு'],
    'cpcb.readings': ['CPCB readings', 'CPCB रीडिंग', 'CPCB ವಾಚನಗಳು', 'CPCB அளவீடுகள்'],
    'cpcb.source': ['Source: {source}', 'स्रोत: {source}', 'ಮೂಲ: {source}', 'ஆதாரம்: {source}'],
    'quiz.category.ganga': ['Ganga Knowledge', 'गंगा का ज्ञान', 'ಗಂಗಾ ಜ್ಞಾನ', 'கங்கை அறிவு'],
    'quiz.category.namami': ['Namami Gange', 'नमामि गंगे', 'ನಮಾಮಿ ಗಂಗೆ', 'நமாமி கங்கே'],
    'quiz.category.pollution': ['River Pollution', 'नदी प्रदूषण', 'ನದಿ ಮಾಲಿನ್ಯ', 'நதி மாசு'],
    'quiz.category.quality': ['Water Quality', 'जल गुणवत्ता', 'ನೀರಿನ ಗುಣಮಟ್ಟ', 'நீர்த் தரம்'],
    'quiz.groupCorrect': ['Correct answer.', 'सही उत्तर।', 'ಸರಿಯಾದ ಉತ್ತರ.', 'சரியான பதில்.'],
    'quiz.groupIncorrect': ['Incorrect answer.', 'गलत उत्तर।', 'ತಪ್ಪಾದ ಉತ್ತರ.', 'தவறான பதில்.'],
    'quiz.groupScore': ['Quiz score: {score} out of {total}.', 'प्रश्नोत्तरी अंक: {total} में से {score}.', 'ರಸಪ್ರಶ್ನೆ ಅಂಕ: {total}ರಲ್ಲಿ {score}.', 'வினாடி வினா மதிப்பெண்: {total}ல் {score}.'],
    'about.officialProject': ['Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange.', 'Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange.', 'Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange.', 'Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange.'],
  };

  // Curated quiz wording is localized; source titles and citations remain exactly as published.
  const QUIZ = {
    hi: {
      'ganga-headstreams': ['गंगा का ज्ञान', 'GRBMP की परिभाषा के अनुसार गंगा नदी में हिमालय की कितनी मुख्य धाराएँ शामिल हैं?', ['चार', 'पाँच', 'छह', 'आठ'], 'GRBMP विस्तारित सारांश में अलकनंदा से भागीरथी तक छह मुख्य धाराएँ बताई गई हैं।'],
      'ganga-middle-segment': ['गंगा का ज्ञान', 'GRBMP की परिभाषा में मध्य गंगा खंड कौन-सा है?', ['गौमुख से ऋषिकेश', 'ऋषिकेश से वाराणसी', 'वाराणसी से गंगा सागर', 'अलकनंदा से भागीरथी संगम'], 'परिभाषा में ऋषिकेश से वाराणसी तक की मुख्य धारा को मध्य गंगा खंड बताया गया है।'],
      'ganga-lower-segment': ['गंगा का ज्ञान', 'GRBMP की परिभाषा में निम्न गंगा खंड कहाँ तक फैला है?', ['ऋषिकेश से प्रयागराज', 'हरिद्वार से वाराणसी', 'वाराणसी से गंगा सागर', 'गौमुख से ऋषिकेश'], 'GRBMP वाराणसी से गंगा सागर तक के अंतिम हिस्से को निम्न गंगा खंड कहता है।'],
      'nmcg-expansion': ['नमामि गंगे', 'Vision Ganga दस्तावेज़ में NMCG का पूरा नाम क्या है?', ['नेशनल मिशन फॉर क्लीन गंगा', 'नेशनल मॉनिटरिंग काउंसिल फॉर ग्राउंडवॉटर', 'नेशनल मैनेजमेंट सेंटर फॉर ग्लेशियर्स', 'नेशनल मिनिस्ट्री फॉर कंज़र्वेशन एंड गवर्नेंस'], 'दस्तावेज़ के शीर्षक में NMCG का पूरा नाम नेशनल मिशन फॉर क्लीन गंगा दिया गया है।'],
      'nmcg-role-2018': ['नमामि गंगे', '2018 के Vision Ganga दस्तावेज़ में NMCG की क्या भूमिका बताई गई है?', ['नेशनल गंगा काउंसिल की कार्यान्वयन शाखा', 'हर गंगा जल नमूने की वैज्ञानिक प्रयोगशाला', 'सभी नगर उपचार संयंत्रों का प्राधिकरण', 'हिमालयी हिमनदों का प्रबंधन करने वाला संगठन'], 'यह उस 2018 दस्तावेज़ में बताई गई भूमिका है; यह वर्तमान संगठनात्मक व्यवस्था का दावा नहीं है।'],
      'pollution-town-waste': ['नदी प्रदूषण', 'GRBMP Mission 2 के सारांश में प्रदूषण के बिंदु स्रोत कौन-से बताए गए हैं?', ['कस्बों, गाँवों और उद्योगों का तरल व ठोस कचरा', 'केवल पहाड़ी धाराओं की प्राकृतिक तलछट', 'केवल वन क्षेत्रों पर वर्षा', 'केवल नदी के तापमान में मौसमी बदलाव'], 'Mission 2 बेसिन में कस्बों, गाँवों और उद्योगों के कचरे को बिंदु स्रोत बताता है।'],
      'pollution-agricultural-runoff': ['नदी प्रदूषण', 'GRBMP Mission 2 के अनुसार कृषि उर्वरक और कीटनाशक नदी तंत्र तक कैसे पहुँच सकते हैं?', ['सिंचाई के वापसी प्रवाह या वर्षा के बहाव से', 'केवल हिमनद पिघलने से', 'केवल नगर पेयजल पाइपों से', 'बहाव के बिना प्राकृतिक तलछट का हिस्सा बनकर'], 'रिपोर्ट में उर्वरकों और कीटनाशकों के सिंचाई वापसी प्रवाह या वर्षा बहाव में रिसने का वर्णन है।'],
      'water-quality-nirmal-dhara': ['जल गुणवत्ता', 'मिशन निर्मल धारा का घोषित उद्देश्य क्या है?', ['गंगा नदी तंत्र को मानव-जनित प्रदूषण से मुक्त रखना', 'नदी किनारे सड़कों की संख्या बढ़ाना', 'सभी सहायक नदियों को एक धारा में मोड़ना', 'केवल नदी की गहराई मापना'], 'Mission 2 का उद्देश्य गंगा नदी तंत्र में मानव-निर्मित प्रदूषण से रहित प्रवाह है।'],
      'water-quality-waste-types': ['जल गुणवत्ता', 'GRBMP Mission 2 के सारांश के अनुसार कौन-से कचरे गंगा नदी तंत्र की जल गुणवत्ता को प्रभावित करते हैं?', ['घरेलू, औद्योगिक और कृषि कचरा', 'केवल घरों का पेयजल', 'केवल प्राकृतिक झरने का पानी', 'केवल मनोरंजन नौकाओं का कचरा'], 'सारांश में घरेलू, औद्योगिक और कृषि स्रोतों के कचरे का उल्लेख है।'],
      'ganga-aviral-dhara': ['गंगा का ज्ञान', 'GRBMP Mission 1 के उद्देश्य के अनुसार गंगा नदी जाल में क्या लगातार और पर्याप्त मात्रा में बहना चाहिए?', ['प्राकृतिक घटकों सहित पानी, तलछट और पोषक तत्व', 'हर कस्बे का उपचारित मलजल', 'केवल मानसून में छोड़ा गया पानी', 'पतला किया गया औद्योगिक अपशिष्ट'], 'Mission 1, अविरल धारा, पानी के साथ तलछट, पोषक तत्वों और अन्य प्राकृतिक घटकों के निरंतर पर्याप्त प्रवाह का वर्णन करता है।'],
    },
    kn: {
      'ganga-headstreams': ['ಗಂಗಾ ಜ್ಞಾನ', 'GRBMP ವ್ಯಾಖ್ಯಾನದ ಪ್ರಕಾರ ಗಂಗಾ ನದಿಯಲ್ಲಿ ಹಿಮಾಲಯದ ಎಷ್ಟು ಪ್ರಮುಖ ಮೂಲಧಾರೆಗಳು ಸೇರಿವೆ?', ['ನಾಲ್ಕು', 'ಐದು', 'ಆರು', 'ಎಂಟು'], 'GRBMP ವಿಸ್ತೃತ ಸಾರಾಂಶವು ಅಲಕನಂದದಿಂದ ಭಾಗೀರಥಿವರೆಗೆ ಆರು ಪ್ರಮುಖ ಮೂಲಧಾರೆಗಳನ್ನು ಹೆಸರಿಸುತ್ತದೆ.'],
      'ganga-middle-segment': ['ಗಂಗಾ ಜ್ಞಾನ', 'GRBMP ವ್ಯಾಖ್ಯಾನದಲ್ಲಿ ಮಧ್ಯ ಗಂಗಾ ವಿಭಾಗವೆಂದು ಗುರುತಿಸಲಾದ ಹರಿವು ಯಾವುದು?', ['ಗೌಮುಖದಿಂದ ಋಷಿಕೇಶ', 'ಋಷಿಕೇಶದಿಂದ ವಾರಾಣಸಿ', 'ವಾರಾಣಸಿಯಿಂದ ಗಂಗಾಸಾಗರ', 'ಅಲಕನಂದದಿಂದ ಭಾಗೀರಥಿ ಸಂಗಮ'], 'ಋಷಿಕೇಶದಿಂದ ವಾರಾಣಸಿವರೆಗಿನ ಮುಖ್ಯ ಹರಿವನ್ನು ಮಧ್ಯ ಗಂಗಾ ವಿಭಾಗವೆಂದು ವ್ಯಾಖ್ಯಾನಿಸಲಾಗಿದೆ.'],
      'ganga-lower-segment': ['ಗಂಗಾ ಜ್ಞಾನ', 'GRBMP ವ್ಯಾಖ್ಯಾನದಲ್ಲಿ ಕೆಳ ಗಂಗಾ ವಿಭಾಗ ಎಲ್ಲಿಂದ ಎಲ್ಲಿಯವರೆಗೆ ವಿಸ್ತರಿಸುತ್ತದೆ?', ['ಋಷಿಕೇಶದಿಂದ ಪ್ರಯಾಗರಾಜ್', 'ಹರಿದ್ವಾರದಿಂದ ವಾರಾಣಸಿ', 'ವಾರಾಣಸಿಯಿಂದ ಗಂಗಾಸಾಗರ', 'ಗೌಮುಖದಿಂದ ಋಷಿಕೇಶ'], 'ವಾರಾಣಸಿಯಿಂದ ಗಂಗಾಸಾಗರವರೆಗಿನ ಅಂತಿಮ ಭಾಗವನ್ನು GRBMP ಕೆಳ ಗಂಗಾ ವಿಭಾಗವೆಂದು ಹೇಳುತ್ತದೆ.'],
      'nmcg-expansion': ['ನಮಾಮಿ ಗಂಗೆ', 'Vision Ganga ದಾಖಲೆಯಲ್ಲಿ NMCG ಎಂಬುದರ ಪೂರ್ಣ ರೂಪವೇನು?', ['National Mission for Clean Ganga', 'National Monitoring Council for Groundwater', 'National Management Centre for Glaciers', 'National Ministry for Conservation and Governance'], 'ದಾಖಲೆಯ ಶೀರ್ಷಿಕೆ NMCG ಅನ್ನು National Mission for Clean Ganga ಎಂದು ವಿಸ್ತರಿಸುತ್ತದೆ.'],
      'nmcg-role-2018': ['ನಮಾಮಿ ಗಂಗೆ', '2018ರ Vision Ganga ದಾಖಲೆಯು NMCGಗೆ ಯಾವ ಪಾತ್ರ ನೀಡುತ್ತದೆ?', ['National Ganga Council‌ನ ಅನುಷ್ಠಾನ ವಿಭಾಗ', 'ಪ್ರತಿ ಗಂಗಾ ನೀರಿನ ಮಾದರಿಯ ವೈಜ್ಞಾನಿಕ ಪ್ರಯೋಗಾಲಯ', 'ಎಲ್ಲಾ ನಗರ ಸಂಸ್ಕರಣಾ ಘಟಕಗಳ ಪ್ರಾಧಿಕಾರ', 'ಹಿಮಾಲಯದ ಹಿಮನದಿಗಳನ್ನು ನಿರ್ವಹಿಸುವ ಸಂಸ್ಥೆ'], 'ಇದು 2018ರ ದಾಖಲೆಯಲ್ಲಿ ವಿವರಿಸಿದ ಪಾತ್ರ; ಪ್ರಸ್ತುತ ವ್ಯವಸ್ಥೆಯ ಕುರಿತು ಹೇಳಿಕೆಯಲ್ಲ.'],
      'pollution-town-waste': ['ನದಿ ಮಾಲಿನ್ಯ', 'GRBMP Mission 2 ಸಾರಾಂಶವು ಮಾಲಿನ್ಯದ ಬಿಂದು ಮೂಲಗಳೆಂದು ಯಾವುವನ್ನು ಗುರುತಿಸುತ್ತದೆ?', ['ಪಟ್ಟಣ, ಹಳ್ಳಿ ಮತ್ತು ಕೈಗಾರಿಕೆಗಳ ದ್ರವ ಹಾಗೂ ಘನ ತ್ಯಾಜ್ಯ', 'ಪರ್ವತ ಹೊಳೆಗಳ ನೈಸರ್ಗಿಕ ಕೆಸರು ಮಾತ್ರ', 'ಅರಣ್ಯ ಪ್ರದೇಶದ ಮೇಲಿನ ಮಳೆ ಮಾತ್ರ', 'ನದಿಯ ತಾಪಮಾನದಲ್ಲಿನ ಋತುಮಾನದ ಬದಲಾವಣೆ ಮಾತ್ರ'], 'Mission 2 ಪಟ್ಟಣ, ಹಳ್ಳಿ ಮತ್ತು ಕೈಗಾರಿಕೆಗಳ ತ್ಯಾಜ್ಯವನ್ನು ಜಲಾನಯನದ ಬಿಂದು ಮೂಲಗಳೆಂದು ಗುರುತಿಸುತ್ತದೆ.'],
      'pollution-agricultural-runoff': ['ನದಿ ಮಾಲಿನ್ಯ', 'GRBMP Mission 2 ಪ್ರಕಾರ ಕೃಷಿ ಗೊಬ್ಬರ ಮತ್ತು ಕೀಟನಾಶಕಗಳು ನದಿ ವ್ಯವಸ್ಥೆಗೆ ಹೇಗೆ ತಲುಪಬಹುದು?', ['ನೀರಾವರಿ ಹಿಂತಿರುಗುವ ಹರಿವು ಅಥವಾ ಮಳೆನೀರಿನ ಹರಿವಿನಿಂದ', 'ಹಿಮನದಿ ಕರಗುವಿಕೆಯಿಂದ ಮಾತ್ರ', 'ನಗರ ಕುಡಿಯುವ ನೀರಿನ ಕೊಳವೆಗಳಿಂದ ಮಾತ್ರ', 'ಹರಿವು ಇಲ್ಲದೆ ನೈಸರ್ಗಿಕ ಕೆಸರಿನ ಭಾಗವಾಗಿ'], 'ಗೊಬ್ಬರ ಮತ್ತು ಕೀಟನಾಶಕಗಳು ನೀರಾವರಿ ಹಿಂತಿರುಗುವ ಹರಿವು ಅಥವಾ ಮಳೆನೀರಿನಲ್ಲಿ ಸೇರಬಹುದು ಎಂದು ವರದಿ ಹೇಳುತ್ತದೆ.'],
      'water-quality-nirmal-dhara': ['ನೀರಿನ ಗುಣಮಟ್ಟ', 'ನಿರ್ಮಲ್ ಧಾರಾ ಮಿಷನ್‌ನ ಘೋಷಿತ ಉದ್ದೇಶವೇನು?', ['ಗಂಗಾ ನದಿ ವ್ಯವಸ್ಥೆಯನ್ನು ಮಾನವಸೃಷ್ಟಿ ಮಾಲಿನ್ಯದಿಂದ ಮುಕ್ತವಾಗಿಡುವುದು', 'ನದಿತೀರದ ರಸ್ತೆಗಳನ್ನು ಹೆಚ್ಚಿಸುವುದು', 'ಎಲ್ಲಾ ಉಪನದಿಗಳನ್ನು ಒಂದೇ ಕಾಲುವೆಗೆ ತಿರುಗಿಸುವುದು', 'ನದಿಯ ಆಳವನ್ನು ಮಾತ್ರ ಅಳೆಯುವುದು'], 'Mission 2 ಮಾನವಸೃಷ್ಟಿ ಮಾಲಿನ್ಯವಿಲ್ಲದ ಗಂಗಾ ನದಿ ಹರಿವನ್ನು ಗುರಿಯಾಗಿಸುತ್ತದೆ.'],
      'water-quality-waste-types': ['ನೀರಿನ ಗುಣಮಟ್ಟ', 'GRBMP Mission 2 ಪ್ರಕಾರ ಯಾವ ತ್ಯಾಜ್ಯಗಳು ಗಂಗಾ ನದಿ ವ್ಯವಸ್ಥೆಯ ನೀರಿನ ಗುಣಮಟ್ಟದ ಮೇಲೆ ಪರಿಣಾಮ ಬೀರುತ್ತವೆ?', ['ಮನೆಯ, ಕೈಗಾರಿಕಾ ಮತ್ತು ಕೃಷಿ ತ್ಯಾಜ್ಯಗಳು', 'ಮನೆಯ ಕುಡಿಯುವ ನೀರು ಮಾತ್ರ', 'ನೈಸರ್ಗಿಕ ಬುಗ್ಗೆಯ ನೀರು ಮಾತ್ರ', 'ಮನರಂಜನಾ ದೋಣಿಗಳ ತ್ಯಾಜ್ಯ ಮಾತ್ರ'], 'ಸಾರಾಂಶವು ಮನೆ, ಕೈಗಾರಿಕೆ ಮತ್ತು ಕೃಷಿ ಮೂಲದ ತ್ಯಾಜ್ಯಗಳನ್ನು ಹೆಸರಿಸುತ್ತದೆ.'],
      'ganga-aviral-dhara': ['ಗಂಗಾ ಜ್ಞಾನ', 'GRBMP Mission 1 ಉದ್ದೇಶದ ಪ್ರಕಾರ ಗಂಗಾ ನದಿ ಜಾಲದಲ್ಲಿ ನಿರಂತರವಾಗಿ ಮತ್ತು ಸಮರ್ಪಕವಾಗಿ ಹರಿಯಬೇಕಾದವು ಯಾವುವು?', ['ನೀರು, ಕೆಸರು, ಪೋಷಕಾಂಶಗಳು ಮತ್ತು ಇತರ ನೈಸರ್ಗಿಕ ಘಟಕಗಳು', 'ಪ್ರತಿ ಪಟ್ಟಣದ ಸಂಸ್ಕರಿಸಿದ ಕೊಳಚೆ ನೀರು', 'ಮಳೆಗಾಲದಲ್ಲಿ ಬಿಡುವ ನೀರು ಮಾತ್ರ', 'ದುರ್ಬಲಗೊಳಿಸಿದ ಕೈಗಾರಿಕಾ ಹೊರಸ್ರಾವ'], 'Mission 1 ಅವಿರಲ್ ಧಾರಾ, ನೀರಿನೊಂದಿಗೆ ಕೆಸರು, ಪೋಷಕಾಂಶಗಳು ಮತ್ತು ಇತರ ನೈಸರ್ಗಿಕ ಘಟಕಗಳ ನಿರಂತರ ಸಮರ್ಪಕ ಹರಿವನ್ನು ವಿವರಿಸುತ್ತದೆ.'],
    },
    ta: {
      'ganga-headstreams': ['கங்கை அறிவு', 'GRBMP வரையறைப்படி கங்கை நதியில் இமயமலையின் எத்தனை முக்கியத் தலைநீரோடைகள் அடங்கும்?', ['நான்கு', 'ஐந்து', 'ஆறு', 'எட்டு'], 'GRBMP விரிவான சுருக்கம் அலக்நந்தா முதல் பாகீரதி வரை ஆறு முக்கியத் தலைநீரோடைகளைக் குறிப்பிடுகிறது.'],
      'ganga-middle-segment': ['கங்கை அறிவு', 'GRBMP வரையறையில் நடு கங்கைப் பகுதியாகக் குறிப்பிடப்படும் நீரோட்டம் எது?', ['கோமுக்கிலிருந்து ரிஷிகேஷ்', 'ரிஷிகேஷிலிருந்து வாரணாசி', 'வாரணாசியிலிருந்து கங்காசாகர்', 'அலக்நந்தா முதல் பாகீரதி சங்கமம்'], 'ரிஷிகேஷிலிருந்து வாரணாசி வரையிலான முக்கிய நீரோட்டம் நடு கங்கைப் பகுதியாக வரையறுக்கப்படுகிறது.'],
      'ganga-lower-segment': ['கங்கை அறிவு', 'GRBMP வரையறையில் கீழ் கங்கைப் பகுதி எங்கு வரை நீள்கிறது?', ['ரிஷிகேஷிலிருந்து பிரயாக்ராஜ்', 'ஹரித்வாரிலிருந்து வாரணாசி', 'வாரணாசியிலிருந்து கங்காசாகர்', 'கோமுக்கிலிருந்து ரிஷிகேஷ்'], 'வாரணாசியிலிருந்து கங்காசாகர் வரையிலான இறுதிப் பகுதியை GRBMP கீழ் கங்கைப் பகுதி என்கிறது.'],
      'nmcg-expansion': ['நமாமி கங்கே', 'Vision Ganga ஆவணத்தில் NMCG என்பதன் விரிவாக்கம் என்ன?', ['National Mission for Clean Ganga', 'National Monitoring Council for Groundwater', 'National Management Centre for Glaciers', 'National Ministry for Conservation and Governance'], 'ஆவணத்தின் தலைப்பு NMCG-ஐ National Mission for Clean Ganga என விரிவாக்குகிறது.'],
      'nmcg-role-2018': ['நமாமி கங்கே', '2018 Vision Ganga ஆவணம் NMCG-க்கு என்ன பங்கு அளிக்கிறது?', ['National Ganga Council-இன் செயலாக்கப் பிரிவு', 'ஒவ்வொரு கங்கை நீர் மாதிரிக்கும் அறிவியல் ஆய்வகம்', 'அனைத்து நகர சுத்திகரிப்பு நிலையங்களின் அதிகாரம்', 'இமயமலை பனிப்பாறைகளை நிர்வகிக்கும் அமைப்பு'], 'இது 2018 ஆவணத்தில் கூறப்பட்ட பங்கு; தற்போதைய அமைப்பு குறித்த கூற்று அல்ல.'],
      'pollution-town-waste': ['நதி மாசு', 'GRBMP Mission 2 சுருக்கம் மாசின் புள்ளி மூலங்களாக எவற்றைக் குறிப்பிடுகிறது?', ['நகரங்கள், கிராமங்கள், தொழில்களின் திரவ மற்றும் திடக் கழிவுகள்', 'மலை ஓடைகளின் இயற்கை வண்டல் மட்டும்', 'காடுகளில் பெய்யும் மழை மட்டும்', 'நதியின் வெப்பநிலை மாற்றம் மட்டும்'], 'Mission 2 நகரங்கள், கிராமங்கள் மற்றும் தொழில்களின் கழிவுகளைப் படுகையின் புள்ளி மூலங்களாகக் குறிப்பிடுகிறது.'],
      'pollution-agricultural-runoff': ['நதி மாசு', 'GRBMP Mission 2 படி வேளாண் உரங்களும் பூச்சிக்கொல்லிகளும் நதி அமைப்பை எவ்வாறு அடையலாம்?', ['பாசனத் திரும்போட்டம் அல்லது மழைநீர் ஓட்டம் வழியாக', 'பனிப்பாறை உருகுவதால் மட்டும்', 'நகரக் குடிநீர்க் குழாய்கள் வழியாக மட்டும்', 'ஓட்டமின்றி இயற்கை வண்டலாக மாறி'], 'உரங்களும் பூச்சிக்கொல்லிகளும் பாசனத் திரும்போட்டம் அல்லது மழைநீர் ஓட்டத்தில் கலக்கலாம் என அறிக்கை கூறுகிறது.'],
      'water-quality-nirmal-dhara': ['நீர்த் தரம்', 'நிர்மல் தாரா திட்டத்தின் அறிவிக்கப்பட்ட நோக்கம் என்ன?', ['கங்கை நதி அமைப்பை மனிதச் செயலால் ஏற்படும் மாசிலிருந்து விடுவித்தல்', 'நதிக்கரைச் சாலைகளின் எண்ணிக்கையை உயர்த்துதல்', 'அனைத்து துணைநதிகளையும் ஒரே கால்வாயில் திருப்புதல்', 'நதியின் ஆழத்தை மட்டும் அளவிடுதல்'], 'மனிதச் செயலால் ஏற்படும் மாசில்லாத கங்கை நதி ஓட்டமே Mission 2-இன் நோக்கம்.'],
      'water-quality-waste-types': ['நீர்த் தரம்', 'GRBMP Mission 2 படி கங்கை நதி அமைப்பின் நீர்த் தரத்தை எந்தக் கழிவுகள் பாதிக்கின்றன?', ['வீட்டு, தொழில்துறை மற்றும் வேளாண் கழிவுகள்', 'வீட்டுக் குடிநீர் மட்டும்', 'இயற்கை ஊற்று நீர் மட்டும்', 'பொழுதுபோக்குப் படகுக் கழிவு மட்டும்'], 'வீட்டு, தொழில்துறை மற்றும் வேளாண் மூலக் கழிவுகளைச் சுருக்கம் குறிப்பிடுகிறது.'],
      'ganga-aviral-dhara': ['கங்கை அறிவு', 'GRBMP Mission 1 நோக்கப்படி கங்கை நதி வலையமைப்பில் தொடர்ச்சியாகவும் போதுமான அளவிலும் எவை பாய வேண்டும்?', ['நீர், வண்டல், ஊட்டச்சத்துகள் மற்றும் பிற இயற்கைக் கூறுகள்', 'ஒவ்வொரு நகரத்தின் சுத்திகரிக்கப்பட்ட கழிவுநீர்', 'மழைக்காலத்தில் விடப்படும் நீர் மட்டும்', 'நீர்த்தொழிக்கப்பட்ட தொழிற்சாலை வெளியேற்றம்'], 'Mission 1, Aviral Dhara, நீருடன் வண்டல், ஊட்டச்சத்துகள் மற்றும் பிற இயற்கைக் கூறுகளின் தொடர்ச்சியான போதுமான ஓட்டத்தை விவரிக்கிறது.'],
    },
  };

  let language = 'en';
  let initialized = false;

  function interpolate(value, values = {}) {
    return String(value).replace(/\{([a-zA-Z0-9_]+)\}/g, (match, key) => values[key] === undefined ? match : String(values[key]));
  }

  function t(key, values = {}) {
    const entry = MESSAGES[key];
    if (!entry) return key;
    const index = LANGUAGES.findIndex(item => item.code === language);
    return interpolate(entry[index < 0 ? 0 : index] || entry[0], values);
  }

  function translateQuiz(question, locale = language) {
    const row = QUIZ[locale] && QUIZ[locale][question && question.id];
    if (!row) return question;
    return { ...question, category: row[0], question: row[1], options: question.options.map((option, index) => ({ ...option, text: row[2][index] || option.text })), explanation: row[3] };
  }

  function translateElement(element) {
    if (!element || typeof element.getAttribute !== 'function') return;
    const textKey = element.getAttribute('data-i18n');
    let values = {};
    try { values = JSON.parse(element.getAttribute('data-i18n-values') || '{}'); } catch (_) {}
    if (textKey) element.textContent = t(textKey, values);
    ['placeholder', 'title', 'aria-label', 'alt'].forEach(attribute => {
      const key = element.getAttribute(`data-i18n-${attribute}`);
      if (key) element.setAttribute(attribute, t(key, values));
    });
  }

  function applySubtree(node) {
    if (!node) return;
    if (typeof node.matches === 'function' && node.matches('[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label], [data-i18n-alt]')) translateElement(node);
    if (typeof node.querySelectorAll === 'function') {
      node.querySelectorAll('[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label], [data-i18n-alt]').forEach(translateElement);
    }
  }

  function setText(element, key, values = {}) {
    if (!element) return;
    element.setAttribute('data-i18n', key);
    if (Object.keys(values).length) element.setAttribute('data-i18n-values', JSON.stringify(values));
    else element.removeAttribute('data-i18n-values');
    element.textContent = t(key, values);
  }

  function apply(documentObject) {
    if (!documentObject) return;
    documentObject.documentElement.lang = language;
    if (typeof documentObject.querySelectorAll === 'function') {
      documentObject.querySelectorAll('[data-i18n], [data-i18n-placeholder], [data-i18n-title], [data-i18n-aria-label], [data-i18n-alt]').forEach(translateElement);
    }
    const selector = documentObject.getElementById && documentObject.getElementById('websiteLangSelect');
    if (selector) selector.value = language;
    if (documentObject.title !== undefined) documentObject.title = t('site.title');
    const description = documentObject.querySelector && documentObject.querySelector('meta[name="description"]');
    if (description) description.setAttribute('content', t('site.description'));
  }

  function setLanguage(code, { persist = true, document: documentObject = globalThis.document, window: windowObject = globalThis } = {}) {
    if (!LANGUAGE_CODES.has(code)) return language;
    language = code;
    if (persist) {
      try { windowObject.localStorage && windowObject.localStorage.setItem(STORAGE_KEY, code); } catch (_) {}
    }
    apply(documentObject);
    if (windowObject && typeof windowObject.dispatchEvent === 'function') {
      const EventCtor = windowObject.CustomEvent || (typeof CustomEvent !== 'undefined' ? CustomEvent : null);
      if (EventCtor) windowObject.dispatchEvent(new EventCtor('ganga-website-language-change', { detail: { language } }));
    }
    return language;
  }

  function initialize(documentObject, windowObject) {
    if (initialized || !documentObject) return api;
    initialized = true;
    const win = windowObject || globalThis;
    try {
      const saved = win.localStorage && win.localStorage.getItem(STORAGE_KEY);
      if (LANGUAGE_CODES.has(saved)) language = saved;
    } catch (_) {}
    const start = () => {
      apply(documentObject);
      const selector = documentObject.getElementById('websiteLangSelect');
      selector?.addEventListener('change', () => setLanguage(selector.value, { document: documentObject, window: win }));
    };
    if (documentObject.readyState === 'loading') documentObject.addEventListener('DOMContentLoaded', start, { once: true });
    else start();
    return api;
  }

  const api = {
    languages: LANGUAGES,
    storageKey: STORAGE_KEY,
    t,
    translateQuiz,
    setText,
    applySubtree,
    getLanguage: () => language,
    setLanguage,
    apply,
    initialize,
    missingKeys(locale) {
      if (!LANGUAGES.some(item => item.code === locale)) return Object.keys(MESSAGES);
      const index = LANGUAGES.findIndex(item => item.code === locale);
      return Object.entries(MESSAGES).filter(([, values]) => !values[index]).map(([key]) => key);
    },
    messageKeys: () => Object.keys(MESSAGES),
  };
  return api;
});
