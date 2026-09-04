# Research Log

## PRJ_316 - Ganga AI Mascot

This research log records research papers, related projects, and technical resources reviewed for PRJ_316. It supports systematic comparison of existing work relevant to an AI-powered, source-grounded conversational agent and interactive digital mascot for Ganga and river conservation awareness.

## Paper Analysis Template

### Paper ID

**Paper ID:**

### Title

**Title:**

### Authors

**Authors:**

### Year

**Year:**

### Publication / Conference / Journal

**Publication / Conference / Journal:**

### Link / DOI

**Link / DOI:**

### Research Problem

**Summary:**

### Proposed Approach

**Summary:**

### Technologies / Models Used

**Details:**

### Dataset / Knowledge Source

**Details:**

### Key Contributions

- **Contribution 1:**
- **Contribution 2:**
- **Contribution 3:**

### Main Results

**Summary:**

### Limitations

**Details:**

### Relevance to PRJ_316

**Analysis:**

### Ideas for PRJ_316

- **Idea 1:**
- **Idea 2:**
- **Idea 3:**

### Research Category

**Category or categories:**

Possible categories include:

- Ganga / River Conservation
- Environmental Education
- Conversational AI
- Retrieval-Augmented Generation
- AI Agents
- Digital Avatars
- Pedagogical Agents
- Voice Interaction
- Adaptive Learning
- Evaluation

## Research Papers to Review

The following entries are placeholders. Detailed authors, publication information, methods, results, datasets, and citations must be added only after each source has been verified.

### R1 - AI-Powered Chacha Chaudhary Mascot for Ganga Conservation Awareness

**Status:** Completed

### Paper Information

- **Paper ID:** R1
- **Title:** AI-Powered Chacha Chaudhary Mascot for Ganga Conservation Awareness
- **Authors:** J. Narmada, A. C. PriyaRanjani, K. Sruthi, P. Harshitha, D. Suchitha, and D. Veera Reddy
- **Year:** 2025
- **Publication:** *Metallurgical and Materials Engineering*, Vol. 31(5), pp. 761–766

### Research Problem

The paper addresses the challenge of improving public awareness, engagement, and environmental education related to Ganga River conservation. It proposes using an AI-powered interactive mascot and digital avatar to communicate information about the Ganga and Namami Gange in a more engaging, accessible, and culturally relatable manner.

### Proposed Approach

The proposed system combines:

- An interactive robot mascot
- A digital avatar
- Conversational chatbot interaction
- Text and voice interaction
- Multilingual communication
- Quizzes and storytelling
- Gamified environmental education
- Personalized interaction
- Potential IoT-based environmental monitoring

### Technologies and Models Mentioned

The paper mentions Natural Language Processing, Machine Learning, Deep Learning, Large Language Models, Speech Recognition / Speech-to-Text, Text-to-Speech, image-based interactions, IoT sensors, and cloud infrastructure. These technologies are discussed generally; the paper does not clearly identify specific AI model names, frameworks, or implementations.

The NLP discussion includes general concepts such as:

- Tokenization
- Part-of-Speech Tagging
- Syntactic Analysis
- Semantic Analysis
- Intent Recognition
- Entity Recognition
- Response Generation

### Knowledge and Data Sources

The paper discusses answering questions related to the Ganga River, pollution, conservation, and Namami Gange initiatives. However, it does not clearly specify:

- A dataset
- A government document collection
- A PDF knowledge base
- A vector database
- A retrieval system
- A data ingestion pipeline
- A knowledge update mechanism

### RAG Analysis

The paper describes a general LLM response generation process involving input encoding, embeddings, contextual understanding, attention mechanisms, and response generation. Embeddings alone do not indicate Retrieval-Augmented Generation.

The paper does not clearly describe document ingestion, document chunking, vector databases, semantic retrieval, retrievers or rerankers, passing retrieved document context to the LLM, or source citations in generated responses.

**The baseline paper does not clearly describe or demonstrate a Retrieval-Augmented Generation architecture.** RAG is therefore not marked as implemented in the baseline paper; it is considered a potential improvement and research direction for PRJ_316.

### Key Contributions

1. Proposing a culturally recognizable mascot for Ganga conservation awareness.
2. Combining AI and ML-based conversational interaction.
3. Including a digital avatar.
4. Supporting multilingual and voice interaction.
5. Using quizzes, games, and storytelling for environmental education.
6. Proposing potential IoT-based environmental monitoring.

### Results

The paper reports promising outcomes related to public engagement, environmental awareness, accessibility, youth engagement, and regional communication. It also suggests that storytelling, games, and quizzes improve the learning experience. No quantitative performance results are stated here because they are not clearly provided in the available description.

### Evaluation Analysis

The paper provides limited detail regarding quantitative evaluation methodology. The available description does not clearly provide:

- Number of participants
- Accuracy metrics
- User engagement metrics
- Detailed survey methodology
- Baseline comparisons
- Benchmark datasets
- Statistical analysis

This indicates that the evaluation details are limited in the available description; it does not establish that the system performed poorly.

### Limitations and Research Gaps

#### 1. No Clearly Defined RAG Architecture

The paper describes LLM response generation but does not clearly describe document retrieval or a RAG pipeline.

#### 2. Knowledge Sources Are Not Clearly Defined

The paper does not clearly identify how authoritative Ganga-related information is collected, stored, maintained, or updated.

#### 3. Limited Source Traceability

The paper does not clearly explain how users can verify the source of AI-generated answers.

#### 4. Specific Models Are Not Clearly Identified

The paper discusses NLP, ML, Deep Learning, and LLMs generally but does not clearly identify specific models or frameworks used.

#### 5. Limited Evaluation Details

The paper reports positive outcomes but provides limited quantitative evaluation details.

### Relevance to PRJ_316

This is the closest baseline project to PRJ_316 because both projects focus on using an AI-powered mascot and digital avatar to promote Ganga conservation awareness.

### Ideas and Improvements for PRJ_316

1. RAG-based knowledge system using authoritative documents.
2. Clearly defined and curated knowledge sources.
3. Source-grounded and traceable AI responses.
4. Modular document ingestion and retrieval architecture.
5. Structured evaluation of retrieval quality, response relevance, groundedness, and response time.

### Research Category

- Ganga / River Conservation
- Environmental Education
- Conversational AI
- AI Agents
- Digital Avatars
- Voice Interaction
- Adaptive Learning

### R2 - Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

**Status:** Completed

**Paper ID:** R2

**Title:** Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

**Authors:** Patrick Lewis et al.

**Year:** 2020

**Publication:** NeurIPS 2020

**Link/DOI:** https://arxiv.org/abs/2005.11401

### Research Problem

Large pretrained language models store substantial factual knowledge in their parameters, but have limitations in precisely accessing and manipulating that knowledge, updating it, providing provenance, and avoiding hallucinations. The paper investigates improving language generation by combining parametric memory inside a pretrained language model with an explicit non-parametric external memory.

### Proposed Approach

Retrieval-Augmented Generation (RAG) combines:

1. A pretrained parametric sequence-to-sequence generator.
2. A non-parametric external knowledge store represented as a dense vector index.
3. A neural retriever that retrieves relevant passages for a query.
4. A generator that produces the final response using the original input and retrieved passages.

The basic flow is:

**User Query → Query Encoder → Retrieve Top-K Relevant Documents → Retrieved Knowledge/Context → Generator → Final Answer**

Retrieval is an additional knowledge-access mechanism rather than reliance only on the language model's internal parameters.

### RAG Variants

1. **RAG-Sequence:** Uses the same retrieved document to generate the complete output sequence and marginalizes over retrieved documents when calculating the final sequence probability.
2. **RAG-Token:** Allows different retrieved documents to contribute to different generated tokens and marginalizes over retrieved documents at the token level.

Neither variant is universally better; performance depends on the task.

### Retriever

The paper uses Dense Passage Retrieval (DPR). DPR uses separate BERT-based query and document encoders to represent queries and documents as dense vectors. Inner-product similarity and Maximum Inner Product Search (MIPS) retrieve the highest-scoring documents. The retriever is initialized using a pretrained DPR model.

DPR is the retrieval and encoding approach used by the paper, whereas ChromaDB is a vector database/tool that PRJ_316 may use to store and retrieve embeddings. They are not the same thing.

### Generator

The paper uses BART-large as the sequence-to-sequence generator. BART-large has approximately 400M parameters. Retrieved content is combined with the original input before generation, and the generator provides the parametric memory component. BART is an implementation choice made by the paper and is not mandatory for PRJ_316.

### Knowledge Source / Dataset

The non-parametric knowledge source is a December 2018 Wikipedia dump. Articles are split into disjoint 100-word passages, producing approximately 21 million passages. Passage embeddings are generated using the document encoder, and FAISS constructs a dense MIPS index for efficient retrieval. The system retrieves a configurable number of top documents.

Wikipedia is the source used in R2, not a recommended knowledge source for PRJ_316. PRJ_316 could instead use a curated collection of authoritative Ganga and environmental documents, including appropriate official government, NMCG, CPCB, and Ministry sources.

### Training Approach

The paper trains the retriever and generator jointly/end-to-end using input/output training pairs. The document encoder and document index remain fixed during training because updating the index would be expensive. The query encoder and generator are fine-tuned.

PRJ_316 does not need to train an entire RAG model from scratch; a pretrained embedding/retrieval system and pretrained LLM can be used with a curated knowledge base.

### Experiments / Evaluation

RAG is evaluated on Natural Questions, TriviaQA, WebQuestions, CuratedTrec, MS MARCO, Jeopardy question generation, and FEVER fact verification. These experiments cover open-domain question answering and knowledge-intensive generation/classification.

The paper reports state-of-the-art results on the four open-domain QA tasks in Table 1, with the stated T5-comparable TriviaQA split qualification. RAG-Sequence outperformed BART on Open MS MARCO NLG by 2.6 BLEU points and 2.6 ROUGE-L points. RAG models generated more factual and specific language than the BART-only baseline, and reported human evaluation for Jeopardy question generation preferred RAG over BART for factuality. Replacing the external index can update system knowledge without retraining the generator. These are results from R2, not PRJ_316.

### Key Contributions

1. Introduced a general framework combining parametric and non-parametric memory.
2. Combined a pretrained neural retriever with a pretrained sequence-to-sequence generator.
3. Proposed RAG-Sequence and RAG-Token formulations.
4. Demonstrated strong performance across multiple knowledge-intensive NLP tasks.
5. Showed that external memory can be inspected and updated independently from the generator.
6. Demonstrated that retrieval can improve factuality and specificity compared with a parametric-only baseline.

### Limitations / Considerations

1. The external knowledge source can contain errors or biases; Wikipedia and other external sources may not be completely factual or bias-free.
2. Retrieval quality is important because missing relevant information can affect generation.
3. The approximately 21-million-passage Wikipedia index is substantially larger than the knowledge base expected for a college mini-project.
4. The architecture and experiments use DPR, BART-large, FAISS, and related infrastructure, so PRJ_316 should adapt the RAG principle rather than copy the exact implementation.
5. The paper focuses on broad knowledge-intensive benchmarks rather than Ganga or environmental education, so its results do not directly establish performance for PRJ_316.
6. The paper discusses future work around jointly pre-training the retriever and generator, indicating open research directions.

### Relevance to PRJ_316

R2 is a foundational paper for the Brain component of PRJ_316. PRJ_316 needs to answer Ganga conservation questions using a controlled and updateable knowledge base rather than relying entirely on the language model's internal knowledge.

**R2:** User Query → DPR Query Encoder → Wikipedia Dense Index → Retrieved Passages → BART Generator → Answer

**PRJ_316:** User Query → Query Embedding → Ganga/Environmental Knowledge Base → Vector Similarity Search → Relevant Official Document Chunks → LLM → Grounded Answer → Source/Document Reference

PRJ_316 can use a vector database such as ChromaDB for its knowledge store, but ChromaDB was not used in the R2 paper.

### Ideas for PRJ_316

1. Build a curated knowledge base from authoritative Ganga and environmental documents.
2. Convert documents into meaningful chunks and generate embeddings.
3. Store embeddings with metadata such as document title, organization, year, source URL, and section/page where applicable.
4. Retrieve the most relevant chunks for each user question and provide them to the LLM as context.
5. Instruct the LLM to answer using retrieved evidence and provide source references where practical.
6. Keep the knowledge base separate from the LLM so documents can be updated without retraining the LLM.
7. Evaluate retrieval quality and answer groundedness separately.

**Important distinction for PRJ_316:** R2 provides the scientific foundation for the RAG concept, but it does not prescribe the exact technology stack for PRJ_316.

- RAG ≠ ChromaDB
- Embeddings ≠ RAG by themselves
- Vector database ≠ LLM
- Retriever ≠ generator
- Knowledge base ≠ model parameters

The PRJ_316 RAG pipeline should conceptually be:

**Official Documents → Text Extraction → Chunking → Embedding Generation → Vector Database → Semantic Retrieval → Context Construction → LLM Generation → Grounded Response**

### Research Gap Identified for PRJ_316

R2 establishes that RAG can improve access to external knowledge, factuality, and updateability, but it does not address the specific requirements of a Ganga conservation education system.

**Potential PRJ_316 research gap:** How can a retrieval-augmented conversational AI system use a curated, authoritative Ganga/environmental knowledge base to provide reliable, understandable, and source-grounded conservation awareness responses for users?

Possible extensions include authoritative Indian environmental sources rather than general Wikipedia, domain-specific retrieval, source traceability, educational explanations, multilingual interaction, conversational personalization, quiz/learning interaction, and evaluation of retrieval relevance and answer groundedness.

### R2 Summary

R2 establishes the core scientific foundation for Retrieval-Augmented Generation by combining parametric language-model knowledge with an external non-parametric memory accessed through neural retrieval. The study demonstrates that retrieved knowledge can improve performance, factuality, and specificity across knowledge-intensive NLP tasks, while allowing the external knowledge index to be updated independently of the generator. For PRJ_316, this provides the theoretical basis for developing a domain-specific RAG Brain using a curated Ganga and environmental knowledge base. However, DPR, BART, and FAISS should be treated as examples rather than mandatory technologies.

### R3 - Conversational AI Agents in Education: An Umbrella Review of Current Utilization, Challenges, and Future Directions for Ethical and Responsible Use

**Status:** Completed

**Paper ID:** R3

**Title:** Conversational AI agents in education: an umbrella review of current utilization, challenges, and future directions for ethical and responsible use

**Authors:** Amrita Ganguly, Nafisa Mehjabin, Aqdas Malik, Aditya Johri

**Year:** 2025

**Publication:** *AI and Ethics*, Springer Nature, Volume 6, Article 72 (2026)

**DOI:** https://doi.org/10.1007/s43681-025-00916-0

**Research Category:** Conversational AI / Educational AI / Pedagogical Agents / Responsible AI / Human-AI Interaction

### Research Problem

Conversational AI (CAI) has increasingly been integrated into education, particularly with the rise of generative AI and LLM-based systems. Existing literature is fragmented across educational domains, chatbot types, learner groups, and applications. Since individual reviews often focus on narrow areas, this paper conducts an umbrella review to synthesize how CAI is used in education, its identified challenges and limitations, ethical and responsible-use issues, and future directions for responsible CAI frameworks.

### Research Questions

- **RQ1:** How is CAI currently utilized across different educational domains?
- **RQ2:** What challenges and limitations of using CAI in education have been identified?
- **RQ3:** What ethical and responsible-use aspects of CAI in education are discussed?
- **RQ4:** What are the future directions for developing frameworks that support the productive use of CAI agents in education?

### Methodology

This is an umbrella review rather than a primary implementation study. The researchers followed PRISMA guidelines and searched Web of Science Core Collection, Scopus, ERIC, ScienceDirect, and Google Scholar using terms covering AI chatbots, AI agents, conversational agents, generative AI, LLMs, pedagogical agents, AI tutors, AI teaching assistants, and education-related terms. Searches were conducted between March 11, 2025 and April 6, 2025.

The initial database search produced 1,263 records, while 47 additional articles were identified through Google Scholar, resulting in 1,310 records before duplicate removal. After screening and eligibility assessment, 34 review articles were included. The JBI Critical Appraisal Checklist was used to assess methodological quality. Two reviewers independently performed the quality assessment, with Cohen's kappa of 0.84 for the overall JBI appraisal. Two researchers independently coded the literature for thematic analysis, with Cohen's kappa of 0.79 for key themes and 0.71 for codes under the key themes. These kappa values measure reviewer agreement, not model accuracy.

### Understanding Conversational AI

The paper treats CAI as an umbrella term for AI-driven speech-based or text-based agents that simulate and automate conversations. It discusses the evolution from traditional rule-based or static chatbots toward NLP/ML-based systems and newer generative-AI/LLM-based systems. Modalities include text-based, voice-based, multimodal, and gesture-based agents. The review primarily focuses on NLP-based and hybrid conversational systems because of their relevance to complex educational interactions.

### CAI Utilization in Education

The review identifies ten major application themes:

1. Teaching and learning support
2. Language acquisition and communication
3. Assessment and feedback
4. Metacognitive and personal development
5. Psychological and motivational support
6. Research and information support
7. Administrative support
8. Healthcare and medical education support
9. Professional development
10. Inclusivity and accessibility

The reported frequencies are:

- Teaching and learning support: 97.1%
- Psychological and motivational support: 91.2%
- Metacognitive and personal development: 88.2%
- Language learning and communication: 85.3%
- Assessment and feedback: 85.3%
- Inclusivity and accessibility: 79.4%
- Professional development: 67.6%
- Research and information management: 52.9%
- Administrative support: 50.0%
- Healthcare and medical education: 41.2%

These percentages describe the proportion of reviewed articles discussing each application theme, not the percentage of students or systems using CAI.

### Challenges and Limitations

The review identifies six major challenge categories:

1. **Technical limitations:** Computational resources, training requirements, technology literacy, voice-generation quality, and maintenance.
2. **Ethical and privacy concerns:** Risks associated with student data, sensitive data collection, privacy, and security.
3. **Interaction and usability challenges:** Communication breakdowns, off-topic responses, and limitations of ASR/NLP systems.
4. **Educational impact and cognitive concerns:** Over-reliance on AI, reduced independent thinking, metacognitive dependency, and possible effects on learning.
5. **Information quality:** Inaccurate information, hallucinations, misleading outputs, and reliability problems.
6. **Language, cultural, and accessibility barriers:** Differences in language, cultural context, abilities, and access conditions.

### Ethical and Responsible AI Issues

The paper identifies five major ethical concern themes:

1. Academic integrity
2. Data privacy and security
3. Bias, fairness, and accuracy
4. Equity and access
5. Human-AI relationship

The concerns extend beyond simple chatbot accuracy and include student data privacy, sensitive data collection, bias in generated information, unequal access, academic misconduct, over-reliance on AI, reduced human interaction, transparency, accountability, and the potential replacement rather than augmentation of human educators. These issues are not automatically solved by RAG.

### Responsible-Use Directions

The paper identifies six broad directions for responsible CAI:

1. Ethical governance and policy frameworks
2. Privacy and data protection measures
3. Academic integrity and fair-use practices
4. AI literacy, training, and awareness
5. Design and technical solutions
6. Equity, inclusion, and human oversight

Responsible CAI therefore requires more than model development. It should involve user-centered design, appropriate governance, privacy protection, AI literacy, and continuous evaluation.

### Traditional CAI and Generative AI

Traditional CAI research places substantial emphasis on interaction quality and usability. GenAI/LLM-based CAI introduces stronger concerns around ethical and privacy issues, hallucination, information quality, bias, academic integrity, and misleading generated content. The rise of GenAI has not eliminated traditional CAI concerns; it has introduced additional and more complex risks.

### Educational Design Gaps

The review highlights:

1. Lack of comprehensive end-to-end design guidance for educational CAI.
2. Weak CAI-specific usability evaluation methods.
3. Insufficiently detailed pedagogical guidance.
4. Lack of concrete classroom implementation strategies.
5. Limited guidance on AI literacy curriculum and assessment.
6. Need for stronger human-centered and HCI-based design.
7. Need for empirical evaluation of critical thinking and self-regulated learning.
8. Need for more research across diverse cultural and educational contexts.

Many CAI implementations are fragmented or overly technical and do not sufficiently connect technology, pedagogy, user experience, and responsible AI.

### Findings Relevant to Multimodal Interaction

The review discusses text, voice, and multimodal agents and identifies a need for comparative research across modalities and educational contexts. This is relevant to a possible PRJ_316 interaction flow:

**User → Voice/Text Input → AI Brain → Response → Voice/Text Output → Digital Avatar**

This is a possible project direction, not an architecture already implemented by PRJ_316.

### Results / Main Conclusions

As a literature synthesis, the paper reports thematic findings rather than model-performance benchmarks. It concludes that CAI has substantial potential in teaching, learning support, motivation, metacognition, language learning, accessibility, and other educational functions. Responsible implementation requires attention to technical limitations, information quality, usability, privacy, fairness, academic integrity, human-AI relationships, and educational impact. The review particularly identifies the need for end-to-end frameworks connecting design, implementation, pedagogy, usability, ethics, and evaluation.

### Key Contributions

1. Provides an umbrella-level synthesis of CAI research in education.
2. Bridges traditional conversational-agent research and newer GenAI/LLM-based CAI.
3. Categorizes major educational applications of CAI.
4. Identifies technical, educational, usability, and ethical challenges.
5. Identifies gaps in current CAI design and implementation frameworks.
6. Provides directions for ethical and responsible CAI development.
7. Highlights human oversight, AI literacy, accessibility, and continuous evaluation.

### Limitations / Considerations

1. The review synthesizes existing review literature rather than directly evaluating a single CAI implementation.
2. The quality and scope of conclusions depend partly on the included reviews.
3. Educational CAI is highly context-dependent, making one universal framework difficult.
4. The rapid evolution of GenAI makes stable evaluation criteria difficult to establish.
5. The literature emphasizes higher education and some domains, leaving other contexts comparatively underrepresented.
6. More long-term research is needed on cognitive impact, knowledge transfer, and self-regulated learning.
7. More comparative research is needed across text, voice, multimodal, and embodied agents.
8. More culturally responsive and inclusive research is needed.

These are limitations and remaining research needs identified by the authors, not flaws that invalidate the study.

### Relevance to PRJ_316

R3 provides the educational and responsible-AI foundation for PRJ_316. R1 establishes the domain-specific AI-powered Ganga conservation mascot concept, R2 establishes the technical RAG foundation, and R3 establishes educational and conversational design requirements: the AI should be useful, understandable, accessible, reliable, responsible, and evaluated from a user and education perspective.

1. **Teaching and learning support:** The mascot can explain Ganga conservation concepts.
2. **Psychological and motivational support:** Interactive storytelling, conversational engagement, and motivational content can improve engagement.
3. **Inclusivity and accessibility:** Multilingual and voice interaction can support a wider audience.
4. **Information quality:** A controlled, authoritative knowledge base and RAG can reduce reliance on an LLM's internal knowledge.
5. **Human-AI relationship:** The mascot should augment educational awareness rather than replace teachers or experts.
6. **AI literacy:** The system should avoid presenting generated information as unquestionable fact.
7. **Ethical design:** Privacy, fairness, transparency, and responsible use should be considered during development.

### Connection Between R2 and R3

R2 asks, “How can a conversational generation system use external knowledge to improve knowledge-intensive responses?” R3 asks, “What should be considered when deploying conversational AI in an educational context?”

Together, R1, R2, and R3 provide three complementary foundations for PRJ_316:

- **R1:** Ganga conservation mascot/application baseline
- **R2:** Technical grounding / RAG
- **R3:** Educational, usability, and responsible-AI grounding

### Ideas for PRJ_316

1. Use understandable language appropriate for the intended audience.
2. Support multilingual interaction where feasible.
3. Consider voice interaction for accessibility and engagement.
4. Preserve source traceability for factual environmental information.
5. Evaluate answer quality rather than assuming the LLM is reliable.
6. Include safeguards against unsupported or misleading answers.
7. Consider privacy when collecting user conversations or voice input.
8. Avoid unnecessary collection of personal information.
9. Design the mascot as an educational assistant rather than a replacement for teachers or experts.
10. Evaluate usability, interaction quality, and accessibility.
11. Consider cultural and language differences.
12. Include quizzes, explanations, or storytelling where appropriate.
13. Plan evaluation criteria before final implementation.
14. Consider human oversight for important or uncertain information.

These are research-informed design considerations for PRJ_316, not mandatory features or implemented capabilities.

### Potential Research Gap for PRJ_316

Existing literature demonstrates the educational potential of conversational AI and identifies important challenges in usability, information quality, accessibility, ethics, and responsible deployment. However, there remains a need for domain-specific conversational AI systems that combine authoritative environmental knowledge, reliable retrieval, educational interaction, and accessible multimodal communication for river-conservation awareness.

PRJ_316 can investigate how a source-grounded conversational AI agent using a curated Ganga/environmental knowledge base can deliver reliable and engaging conservation education through an interactive digital mascot. This is a project-specific opportunity derived from the literature, not a claim that the area is completely unexplored.

### R3 Summary

R3 provides an umbrella-level synthesis of research on conversational AI agents in education by analyzing 34 review articles using PRISMA-guided screening and thematic analysis. The review identifies major CAI applications including teaching and learning support, psychological and motivational support, metacognitive development, language learning, assessment, and accessibility. It also highlights technical, usability, information-quality, privacy, ethical, and educational challenges, particularly growing concerns around hallucination, bias, data privacy, and over-reliance associated with generative AI. For PRJ_316, the study supports designing the conversational mascot not only as an AI question-answering system but as an accessible, educational, and responsible learning and awareness agent. Combined with R2's RAG foundation and R1's Ganga conservation mascot concept, R3 helps define the educational, usability, and responsible-AI requirements of the proposed system.

### R4 - Pedagogical AI Conversational Agents in Higher Education: A Conceptual Framework and Survey of the State of the Art

**Status:** Completed

**Paper ID:** R4

**Title:** Pedagogical AI Conversational Agents in Higher Education: A Conceptual Framework and Survey of the State of the Art

**Authors:** Habeeb Yusuf, Arthur Money, Damon Daylamani-Zad

**Year:** 2025

**Publication:** *Educational Technology Research and Development*, 73, 815–874

**DOI:** https://doi.org/10.1007/s11423-025-10447-4

**Research Category:** Pedagogical AI / Conversational Agents / Educational Technology / Human-AI Interaction / AI Agents

### Research Problem

Conversational agents are increasingly used in education, but the field includes varied agent types, technologies, pedagogical purposes, and educational contexts. This paper surveys the state of the art in pedagogical AI conversational agents in higher education and organizes the literature into a comprehensive conceptual framework. It investigates how these agents are used, their pedagogical and technological functions, how these functions can be organized conceptually, and which areas remain underexplored.

### Research Questions

- **RQ1:** How are pedagogical AI conversational agents being utilised in higher education?
- **RQ2:** What are the pedagogical and technological functions and features of AI conversational agents for higher education, and how are they organised conceptually?
- **RQ3:** What examples exist within the state-of-the-art higher education literature that provide evidence of the various pedagogical and technological functions and features identified in RQ2?
- **RQ4:** Which domains within higher education do the pedagogical and technological functions and features of AI conversational agents appear to remain underexplored and/or present opportunities for further future research?

### Research Method

This is a literature survey rather than a study that develops and tests a new conversational-agent system. The search began with 5,170 results and progressively filtered the literature to 1,448 studies after initial screening and duplicate removal, 484 after further abstract and publication-type screening, and 92 after full-text analysis and inclusion/exclusion criteria. The final sample therefore consisted of 92 studies, not 92 participants or users.

The authors used thematic/template analysis to identify recurring pedagogical and technological themes and construct the conceptual framework.

### Conceptual Framework

The central contribution is a framework organized around two complementary dimensions:

1. **Pedagogical Applications:** What the conversational agent is intended to do in an educational context.
2. **Technological Functions:** What the agent is technically capable of doing.

Technological capabilities can enable a wider range of pedagogical applications, while specialized pedagogical applications may require specialized technological capabilities.

### Pedagogical Purposes

The framework identifies three primary pedagogical purposes:

1. **Pastoral:** Supporting motivation, self-efficacy, educational administration, and related student-support activities.
2. **Instructional:** Supporting teaching and learning through instruction, explanations, or knowledge.
3. **Cognitive:** Supporting reflection, metacognition, assessment, and related higher-level learning activities.

### Pedagogical Agent Intent / Subtypes

The eight sub-types identified in the framework are:

1. Mentoring and coaching
2. Assessments
3. Simulate and experience
4. Reflective skills and metacognitive
5. Communication
6. Administration and management
7. Motivate and inspire
8. FAQs and knowledge base

These categories describe different educational purposes rather than separate technologies. The framework also considers face-to-face and distance education, demonstrating that conversational agents can operate across different educational delivery environments.

### Technological Functions

The framework first distinguishes:

1. **Embodied:** An agent with a visual or physical representation, such as an avatar, virtual human, or robot.
2. **Disembodied:** An agent without a physical or visual embodiment, such as a conventional chatbot.

It also identifies four functional types:

1. Virtual human
2. Avatar
3. Chatbot
4. Voice bot

These describe different forms through which conversational agents can interact with users.

### Technological Features

The five major technological functions/features are:

1. **Machine Learning:** Additional learning or sensing capabilities, potentially including emotion-related or behavioral signals.
2. **Natural Language Processing:** Processing and understanding natural human language.
3. **External Data Source:** Connection to an external source such as a database or online information repository.
4. **Social/Instant Messaging Link:** Use of social or messaging platforms as an interface.
5. **Custom/Unspecified Development:** Custom software development or technology that is not sufficiently specified by the study.

The paper further categorizes NLP-enabled systems as **Native/Natural NLP** or **Application Programming Interface (API)**, meaning that systems may use built-in/custom NLP capabilities or connect to external NLP services. These are categories in the reviewed literature, not the only NLP architectures available today.

### Major Findings

Many higher-education conversational agents in the surveyed literature focus on instructional and pastoral purposes. The paper reports 41 agents/studies associated with instructional purposes and 37 associated with pastoral purposes. Common functions include providing knowledge, answering student questions, supporting motivation and engagement, and teaching and learning. Cognitive applications, particularly assessment-oriented instructional agents, receive comparatively less emphasis. These counts are not percentages of educational institutions or students.

### Embodied vs Disembodied Agents

The literature includes chatbots, voice bots, avatars, and virtual humans. This shows that similar conversational intelligence can potentially be presented through different interfaces. For PRJ_316, this supports separating the AI Brain from the avatar or user interface: the Brain can provide reasoning and knowledge functionality while text, voice, avatar, or robot interfaces present it to users. The paper does not specifically propose the PRJ_316 architecture.

### Personalisation and Media Richness

The authors identify personalization and media richness as important future directions. Agents may become more effective by adapting interactions to individual users and supporting richer communication modalities rather than text alone. This is relevant to the possible PRJ_316 combination of text, voice, digital avatar, potential physical robot, and interactive educational content.

### Key Research Gaps Identified by the Paper

1. More research on assessment-related conversational agents.
2. More research on reflective practice.
3. More effective administrative and management support.
4. Greater personalization.
5. Greater media richness.
6. More research into cognitive conversational agents.
7. More research into emerging AI technologies for pedagogical agents.

These gaps are identified within higher education and should not automatically be treated as gaps specifically about environmental education.

### Results / Main Conclusions

As a literature survey, the results are conceptual and thematic rather than model-performance results. The paper concludes that pedagogical AI conversational agents can be understood through the combination of pedagogical applications and technological functions. The framework provides a structured way to understand their educational purposes, embodiment, interaction types, and technological capabilities. Conversational agents have significant potential to support teaching and learning, while further research is needed in pedagogical applications, personalization, and media richness.

### Key Contributions

1. Conducted a state-of-the-art survey of pedagogical AI conversational agents in higher education.
2. Analyzed a final sample of 92 studies.
3. Developed a conceptual framework for pedagogical conversational agents.
4. Organized the literature according to pedagogical applications and technological functions.
5. Identified pastoral, instructional, and cognitive pedagogical purposes.
6. Identified eight pedagogical sub-types.
7. Classified agents according to embodiment and functional type.
8. Identified technological functions including ML, NLP, and external data sources.
9. Identified underexplored areas and future research opportunities.
10. Highlighted personalization and media richness as future technological directions.

### Limitations / Considerations

1. The study is a literature survey rather than an experimental evaluation of one conversational agent.
2. The framework reflects patterns in the selected literature and is not a universal technical architecture.
3. Rapid development of AI and conversational technologies means the state of the art can change quickly.
4. The review focuses on higher education, so findings should not automatically generalize to all age groups or educational settings.
5. Some studies provide incomplete technological information, reflected in categories such as custom/unspecified development.
6. Further empirical research is needed, particularly for cognitive applications, assessment, personalization, and media richness.

### Relevance to PRJ_316

R4 provides a framework for deciding what kind of conversational agent PRJ_316 is building. Potential PRJ_316 pedagogical purposes include:

- **Instructional:** Explaining Ganga conservation, pollution, biodiversity, river health, and related concepts.
- **Motivate and inspire:** Encouraging environmentally responsible behavior.
- **Communication:** Enabling users to ask questions and interact conversationally.
- **FAQs and knowledge base:** Answering questions using a curated Ganga/environmental knowledge base.
- **Simulate and experience:** Supporting possible future interactive conservation scenarios.

These are proposed project directions, not features already implemented.

### Technological Mapping

Potential PRJ_316 classifications are:

- **Embodiment:** A digital avatar or physical robot would be an embodied conversational agent; a text-only Brain interface would be disembodied interaction.
- **Functional type:** Avatar, chatbot, voice bot, and potentially virtual-human or robot-style interaction.
- **Technological functions:** NLP, machine-learning/LLM-based generation, external data source, and custom software integration.

These are proposed/project architecture classifications, not claims about features already implemented.

### Connection to R1, R2, and R3

- **R1 = Domain/Application:** AI-powered Chacha Chaudhary mascot for Ganga conservation awareness.
- **R2 = RAG/Technical Foundation:** Retrieval-Augmented Generation and external knowledge retrieval.
- **R3 = Educational + Responsible AI:** Usability, information quality, accessibility, ethics, and human oversight.
- **R4 = Pedagogical Agent Architecture/Classification:** Pedagogical purpose, embodiment, interaction type, and technological functions.

Together, these papers provide a stronger theoretical foundation for PRJ_316.

### Ideas for PRJ_316

1. Clearly define the pedagogical purpose of the mascot.
2. Treat the Brain and presentation layer as modular components.
3. Support FAQ and knowledge-base interactions using the RAG Brain.
4. Consider instructional conversations rather than only generic question answering.
5. Consider motivational interactions to encourage conservation awareness.
6. Support voice interaction where feasible.
7. Use the avatar or robot as an embodied interface for the conversational Brain.
8. Consider personalization carefully while avoiding unnecessary personal-data collection.
9. Consider multiple media/modalities for richer interaction.
10. Include quizzes or assessment-style interaction if supported by project scope.
11. Evaluate interaction quality and educational usefulness.
12. Keep the Brain capable of operating independently of the avatar or robot interface.

### Important Architecture Insight

R4 supports the idea that conversational intelligence and its presentation/interface can be considered related but distinct dimensions. For PRJ_316, this suggests the following modular design inference:

**User Input (Text / Voice) → AI Brain (NLP + RAG + LLM) → Response / Actions → Text UI, Digital Avatar, or Robot Interface**

This exact architecture does not appear in R4; it is a PRJ_316 design inference based on the framework.

### Potential Research Gap for PRJ_316

R4 demonstrates that pedagogical conversational agents can be systematically categorized according to pedagogical purpose, embodiment, functional type, and technological capabilities. However, the framework is primarily oriented toward higher education and does not specifically address conversational agents for river or environmental conservation awareness using authoritative domain-specific knowledge.

PRJ_316 can explore the combination of a domain-specific RAG Brain, educational conversational interaction, and an embodied digital or physical mascot to deliver accessible Ganga conservation awareness. This is a project-specific research opportunity, not a claim that no previous work exists.

### R4 Summary

R4 presents a state-of-the-art literature survey of pedagogical AI conversational agents in higher education based on 92 studies and develops a conceptual framework organizing these agents according to pedagogical applications and technological functions. The framework identifies pastoral, instructional, and cognitive pedagogical purposes, together with multiple educational intents, and categorizes agents by embodiment, functional type, and technological capabilities such as NLP, machine learning, and external data sources. The study highlights opportunities for future research in assessment, reflective practice, personalization, and media-rich interaction. For PRJ_316, R4 provides a useful conceptual foundation for defining the mascot as an educational conversational agent and separating the AI Brain from its avatar or robot presentation layer. Combined with R1, R2, and R3, it connects the project's domain concept, technical RAG foundation, and educational design requirements.

### R5 - Designing a Flipped AI-Chatbot Learning Module to Support Students' Environmental Literacy Development

**Status:** Completed

**Paper ID:** R5

**Title:** Designing a flipped AI-chatbot learning module to support students’ environmental literacy development: A Fuzzy Delphi Method

**Authors:** Xiaoyu Wang, Xiang Li

**Year:** 2026

**Publication:** *PLOS ONE*, 21(3), e0345027

**DOI:** https://doi.org/10.1371/journal.pone.0345027

**Research Category:** Environmental Education / AI Chatbots / Environmental Literacy / Flipped Learning / Educational Technology

### Research Problem

Environmental degradation creates a need for effective environmental education that develops Environmental Literacy (EL). The paper identifies limitations in traditional higher-education environmental education, particularly teacher-centered approaches associated with low student motivation, limited interaction, inadequate pre-class preparation, insufficient personalized learning, and difficulty connecting environmental knowledge with real-world problems.

The study investigates how generative AI chatbots can be integrated with Flipped Learning to create a more student-centered environmental education model. Its goal is not simply to introduce a chatbot, but to design a structured instructional module in which AI-supported learning is integrated with learning objectives, activities, and evaluation.

### Research Questions

The paper examines:

1. What are the objectives of the FACL module to support students’ Environmental Literacy development based on experts’ opinions?
2. What content does the FACL module include to support students’ Environmental Literacy development based on experts’ opinions?
3. What instructional strategies are employed in the FACL module to support students’ Environmental Literacy development based on experts’ opinions?
4. What instructional resources and platforms are utilized in the FACL module to support students’ Environmental Literacy development based on experts’ opinions?
5. What evaluation strategies are implemented in the FACL module to support students’ Environmental Literacy development based on experts’ opinions?

### Core Concept — Flipped AI-Chatbot Learning (FACL)

FACL integrates Generative AI, an AI chatbot, Flipped Learning, and Environmental Literacy. Students interact with AI chatbots before class to prepare, explore concepts, and work through environmental problems. During class, learning shifts toward active learning, discussion, collaboration, teacher guidance, and real-world case analysis. After class, students can continue using chatbots for assignments, reflection, and evaluation.

**Before Class → AI-supported preparation and interaction → During Class → Case studies, discussion, collaboration, and teacher guidance → After Class → AI-supported assignments, reflection, and peer evaluation**

This is a design model from R5, not a mandatory classroom structure for PRJ_316.

### Theoretical Foundation

The module is grounded in Flipped Learning, Constructivist Learning, Social Constructivism, and Situated Cognition. These theories support active, contextualized, and collaborative learning rather than passive information transmission. The theoretical foundations inform the instructional structure and expert questionnaire.

### Research Method

The study uses the Fuzzy Delphi Method (FDM) in two phases:

1. Semi-structured interviews with five experts in Environmental Science, Educational Technology, and Artificial Intelligence identified important FACL module elements.
2. A Fuzzy Delphi questionnaire administered to 12 experts established consensus on the proposed elements.

The panel included relevant Environmental Science, Educational Technology, and AI expertise. Eligibility included at least a Master’s degree in a relevant field, at least five years of professional experience, and familiarity with the Chinese higher-education context and Environmental Literacy requirements. Snowball sampling was used to identify qualified experts.

### Ethics

The study received university Research Ethics Committee approval under protocol UM.TNC2/UMREC_3169. Experts participated voluntarily, provided written informed consent, and had their responses anonymized. This approval does not constitute ethical approval for PRJ_316.

### Fuzzy Delphi Method

FDM uses structured expert consensus to determine which proposed module elements have sufficient support for inclusion. The process converts linguistic judgments into triangular fuzzy numbers, calculates mean fuzzy opinions, determines a threshold, evaluates consensus, defuzzifies results, and applies consensus criteria. FDM is a methodology for expert consensus, not an AI algorithm used to generate chatbot responses.

### Initial Qualitative Findings

The five expert interviews produced seven themes used to construct the FDM questionnaire:

1. Module objectives
2. Content for module design
3. Instructional strategies before class
4. Instructional strategies during class
5. Instructional strategies after class
6. Resources and platforms for delivering the module
7. Evaluation strategies

### Environmental Literacy Objectives

The proposed FACL module aims beyond factual environmental knowledge. Its objectives include:

- Understanding fundamental environmental knowledge
- Using generative AI creatively
- Developing critical thinking and problem-solving skills
- Discovering and integrating extracurricular resources
- Improving data literacy
- Developing teamwork and communication
- Increasing awareness of environmental protection
- Developing environmental responsibility
- Encouraging participation in real-world environmental actions

This suggests a potential progression for PRJ_316 from **Knowledge → Understanding → Awareness → Action-oriented behavior**, without claiming that PRJ_316 has demonstrated behavioral change.

### Environmental Education Content

The FACL content includes soil ecology, introduction to ecosystems, aquatic ecology, and air ecology. For PRJ_316, the content domain could instead be adapted toward Ganga river ecology, water pollution, wastewater, biodiversity, river conservation, sustainable practices, Namami Gange-related awareness, and responsible human behavior. These Ganga topics are project design possibilities, not topics studied by R5.

### Instructional Strategy — Before Class

Students pre-learn using supporting materials, interact with an AI chatbot, complete individual and group tasks, ask questions, clarify concepts, explore possible solutions, and reflect on learning. For group activities, the chatbot can help synthesize ideas, compare perspectives, and develop a shared outline. AI is integrated into active learning rather than used only for question answering.

### Instructional Strategy — During Class

During-class activities include real-world environmental case scenarios, multimedia-supported lectures, group presentations, teacher guidance, group discussions, peer review, and assessment of mastery of pre-class content. The teacher remains an active facilitator; the paper does not propose replacing teachers with AI.

### Instructional Strategy — After Class

After-class activities include assignments using AI chatbots, self-reflection, peer evaluation, and applying concepts to real-world situations. This creates a continuous **Before → During → After** learning cycle.

### Role of the AI Chatbot

The chatbot provides personalized guidance, real-time assistance, concept clarification, exploration of solution pathways, support for individual and group tasks, and assistance with assignments and reflection. It operates within a broader instructional design. Teachers remain responsible for designing learning tasks, establishing AI-use expectations, guiding questions, facilitating discussions, correcting misconceptions, providing feedback, supporting collaboration, and evaluating learning.

### Resources and Platforms

The module includes text-based learning materials, lesson plans, individual and group pre-class task materials, instructional videos, AI chatbot platforms, and post-class tasks. The paper does not require a specific chatbot platform or LLM.

### Evaluation Strategies

The proposed strategies include team presentations, participation marks, peer evaluation, self-reflection, and quick question-and-answer sessions. Evaluation is distributed across the learning cycle rather than relying only on a final test. These are instructional evaluation strategies, not chatbot accuracy benchmark metrics.

### Main Results

The primary result is an expert-validated instructional framework rather than a chatbot performance benchmark. The Fuzzy Delphi process reached consensus on key FACL components, integrating instructional objectives, environmental content, before-class, during-class and after-class strategies, learning resources/platforms, and evaluation strategies.

The authors argue that the framework can support student-centered environmental education and potentially promote critical thinking, problem-solving, and pro-environmental behaviors. The study does not prove that the chatbot improved Environmental Literacy.

### Key Contributions

1. Introduces the Flipped AI-Chatbot Learning (FACL) module.
2. Connects generative AI with Flipped Learning and Environmental Literacy.
3. Uses expert consensus to structure the module.
4. Provides a complete before-during-after instructional framework.
5. Integrates AI chatbot interaction with active and collaborative learning.
6. Identifies environmental-learning objectives beyond factual knowledge.
7. Includes evaluation strategies within the instructional design.
8. Emphasizes critical thinking, problem solving, data literacy, teamwork, and environmental responsibility.
9. Demonstrates how AI can function as a learning-support tool rather than merely a conversational interface.

### Limitations / Considerations

1. The study develops and validates an instructional framework rather than conducting a large-scale experimental comparison of student learning outcomes.
2. The expert panel consists of 12 experts, so findings represent expert consensus rather than population-wide evidence.
3. The study is situated in higher education in China; direct generalization to Indian environmental education requires caution.
4. The module is designed around specific environmental-education content and a flipped-learning context.
5. The study focuses on module design rather than a domain-specific RAG architecture.
6. The paper does not establish that any particular LLM or chatbot technology is universally superior.
7. Long-term effects on environmental behavior and literacy require further empirical investigation.

### Relevance to PRJ_316

R5 is directly relevant because it combines AI, conversational interaction, and environmental education/awareness. The major difference is that R5 designs an educational module, whereas PRJ_316 proposes an interactive environmental-awareness mascot.

R5 supports treating the AI system as more than a question-answering tool. It could potentially explain concepts, provide personalized guidance, ask users questions, provide quizzes, encourage reflection, present environmental scenarios, connect knowledge with real-world problems, and encourage responsible environmental behavior. These are not claims that all such features are already implemented in PRJ_316.

### Relevance to the AI Brain

Instead of only **User → Question → Answer**, PRJ_316 could potentially use:

**User → Question/Interaction → Retrieve Relevant Environmental Knowledge → Generate Educational Explanation → Encourage Understanding/Reflection → Optional Quiz/Follow-up**

This is a design implication derived from R5, not an architecture directly proposed by the paper.

### Connection to R2 — RAG

R2 provides the technical foundation for retrieving external knowledge before generation, while R5 provides educational justification for using conversational AI to support environmental learning:

**Authoritative Environmental Documents → RAG Retrieval → AI Brain → Educational Conversation → Mascot Interaction**

This connects the technical and educational literature without claiming that R5 implements RAG.

### Connection to R1

R1 provides the specific Chacha Chaudhary/Ganga conservation mascot concept. R5 provides evidence and design principles for using AI chatbots in environmental education, strengthening the educational justification of the R1 concept.

### Connection to R3

R3 provides a broad educational and responsible-AI perspective, including information quality, usability, accessibility, privacy, ethics, and responsible AI. R5 provides a specific environmental-education instructional framework using an AI chatbot. Thus, R3 is the broad educational/responsible-AI perspective and R5 is the environmental-education-specific application/design perspective.

### Connection to R4

R4 provides a framework for pedagogical conversational agents, including instructional purposes and technological functions. R5 shows a concrete environmental-education instructional design in which an AI chatbot supports preparation, learning activities, and reflection. Together they help define the role of the PRJ_316 mascot as an educational conversational agent.

### Potential Research Gap for PRJ_316

R5 demonstrates how generative AI chatbots can be incorporated into a structured environmental-literacy learning framework, but the study focuses on higher-education environmental education and does not address domain-specific conversational agents for river-conservation awareness using authoritative, continuously maintainable knowledge sources.

PRJ_316 can explore integrating a domain-specific RAG Brain with environmental education and an interactive digital or physical mascot to provide source-grounded conversational awareness about Ganga conservation. This is not described as a completely unexplored research area.

### Ideas for PRJ_316

1. Design the Brain around environmental education rather than generic conversation.
2. Use real-world environmental scenarios.
3. Provide explanations rather than only short answers.
4. Include quizzes or knowledge checks.
5. Encourage reflection and follow-up questions.
6. Provide personalized educational guidance where appropriate.
7. Support individual and potentially group interactions.
8. Connect environmental facts to practical conservation actions.
9. Use authoritative environmental knowledge sources.
10. Evaluate educational usefulness separately from technical chatbot performance.
11. Consider user engagement and accessibility.
12. Maintain teacher or expert oversight for important environmental information.
13. Avoid presenting AI-generated content as unquestionably correct.
14. Consider multilingual interaction for broader accessibility.
15. Keep the AI Brain modular so it can later support avatar, voice, and robot interfaces.

These are potential design considerations, not mandatory requirements unless later approved in the PRJ_316 requirements.

### Important Research Insight

R5 suggests that the value of an environmental AI chatbot depends not only on chatbot technology but also on how AI is embedded within an educational design. PRJ_316 should therefore consider whether information is reliable, explanations are understandable, interactions support learning and awareness, access is inclusive, real-world action is encouraged appropriately, and human oversight is available—not only whether the AI answers Ganga-related questions.

### R5 Summary

R5 presents a Flipped AI-Chatbot Learning (FACL) module designed to support Environmental Literacy among higher-education students. Using the Fuzzy Delphi Method, the study gathered expert consensus to define instructional objectives, environmental content, before-class, during-class and after-class strategies, learning resources, and evaluation methods. The framework positions AI chatbots as learning-support tools that provide personalized guidance, concept clarification, and assistance across the learning cycle, while teachers remain responsible for instructional design, facilitation, and feedback. The study connects conversational AI directly with environmental education and emphasizes critical thinking, problem solving, environmental responsibility, and real-world application. Unlike R2, it does not investigate RAG, and unlike R1, it does not focus on Ganga or a digital mascot. Instead, it provides an educational-design foundation for using the PRJ_316 AI Brain as an environmental awareness and learning agent.

### R6 - Evaluating the Efficacy of ChatGPT in Environmental Education: Findings from Heuristic and Usability Assessments

**Status:** Completed

**Paper ID:** R6

**Title:** Evaluating the efficacy of ChatGPT in environmental education: findings from heuristic and usability assessments

**Authors:** Xiaoyu Wang, Zamzami Zainuddin, Chin Hai Leng, Wenting Dong, Xiang Li

**Year:** 2025

**Publication:** *On the Horizon: The International Journal of Learning Futures*, 33(2), 165–185

**DOI:** https://doi.org/10.1108/OTH-11-2024-0079

**Research Category:** Environmental Education / Generative AI / ChatGPT / Usability Evaluation / Human-AI Interaction

### Research Problem

Generative AI and ChatGPT have potential to provide interactive, personalized, and engaging educational experiences. However, the paper identifies a lack of rigorous usability research specifically examining ChatGPT in environmental education. The study investigates usability, user experience, information quality, interaction quality, accessibility, error handling, and environmental-education usefulness while identifying both strengths and limitations.

### Research Objective

The study investigates ChatGPT’s potential in environmental education in relation to sustainable development goals and identifies usability problems through heuristic evaluation, usability testing, structured questionnaires, and semi-structured interviews. It aims to provide practical guidance for integrating generative AI into environmental education.

### Research Context

The study evaluates ChatGPT in an environmental-education context at a Chinese higher-education institution. Its results should not be generalized automatically to all students, countries, or educational systems.

### Research Methodology

The study combines quantitative and qualitative usability evaluation:

1. **Heuristic evaluation:** Identifies interface and interaction problems through expert assessment.
2. **Chatbot Usability Questionnaire (CUQ):** Measures chatbot-specific usability and user perceptions.
3. **System Usability Scale (SUS):** Measures overall perceived system usability.
4. **User Experience Questionnaire (UEQ):** Measures broader user-experience dimensions.
5. **Semi-structured interviews:** Provide qualitative information that numerical scores may not reveal.

The study involved three expert evaluators with backgrounds in educational technology, artificial intelligence, and environmental science, together with seven undergraduate participants aged approximately 18–22 who had environmental-education backgrounds and experience using ChatGPT. The sample was small and purposively selected, so the findings are not statistically representative of all students.

### Heuristic Evaluation

Experts evaluated ChatGPT using Nielsen’s usability principles. Issues were identified at different severity levels. The most serious identified issue was error prevention (Nielsen heuristic P5), with an average severity of 2.6/4, classified as a major usability problem. Experts noted insufficient error notification and prevention mechanisms in the text-based interface. Other issues concerned flexibility, error recovery, help/documentation, matching the system with the real world, system-status visibility, user control, consistency, and recognition/ease of understanding. Not all heuristics were major problems.

### Environmental-Education Problems Identified

The study highlights:

1. Lack of dynamic fact-checking
2. Limited ability to provide up-to-date information
3. Contextual limitations
4. Limited resource variety
5. Reliance primarily on text
6. Lack of multimedia support
7. Language accessibility barriers
8. Inconsistent responses
9. Superficial information in some responses
10. Limited domain expertise

These issues matter because environmental education involves scientific information, current environmental conditions, and real-world contexts. Plausible but outdated, incomplete, or unsupported information can reduce educational reliability.

### Usability Questionnaire — CUQ

The mean CUQ score was **82.8 ± 7.1**, with a reported minimum of 75.0, maximum of 96.9, and median of 82.8. Compared with an acceptable benchmark of approximately 71.1, the paper interprets this as strong usability. Students generally viewed ChatGPT as adaptable and helpful, with positive responses concerning clear scope and purpose, navigation, ease of use, appropriateness of responses, and realistic or engaging interaction. Concerns included error handling, confusion, input recognition, response relevance, and complexity. CUQ is a usability measure, not an accuracy or environmental-learning measure.

### System Usability Scale — SUS

The mean SUS score was **87.50**, interpreted by the study as an “A” grade and excellent perceived usability. The lowest score was 70, the highest was 100, and the median was 85. Students generally considered ChatGPT easy to use and felt confident interacting with it. SUS measures perceived usability; it does not directly measure factual correctness, Environmental Literacy, or learning gain.

### User Experience Questionnaire — UEQ

The reported UEQ mean scores, on a scale from −3 to +3, were:

- Attractiveness: 2.690
- Perspicuity: 2.536
- Efficiency: 2.464
- Dependability: 2.250
- Stimulation: 2.179
- Novelty: 2.000

The positive scores indicate generally favorable user-experience perceptions. Attractiveness was highest and novelty was lowest among the reported dimensions. These scores describe user experience rather than factual accuracy.

### Student Interview Findings

The interviews identified eight themes:

1. Usability
2. Helpfulness
3. Intuitiveness
4. Attractiveness and engagement
5. Superficiality of information
6. Response-time problems
7. Limited resource variety
8. Language accessibility barriers

Students generally viewed ChatGPT as useful and easy to interact with. They appreciated recommendations, environmental-study assistance, idea generation, brainstorming, quick assistance, and support for self-directed learning. They also reported superficial answers, slow responses in some situations, limited resources, and language barriers.

### Positive Findings

The study identified perceived strengths including ease of use, intuitive interaction, helpfulness for environmental-learning tasks, brainstorming support, rapid feedback, self-directed learning, personalized interaction, engagement, and accessibility. These perceptions do not automatically establish improved learning outcomes.

### Negative Findings

The main weaknesses were unreliable fact-checking, limited up-to-date information, contextual limitations, text-heavy interaction, limited multimedia resources, language barriers, response inconsistencies, superficial information, limited domain expertise, and error-management weaknesses. These are particularly important for PRJ_316 because environmental information may involve scientific facts, current policies, conservation practices, and location-specific information.

### Hybrid Human-AI Model

The paper emphasizes a hybrid approach in which generative AI complements rather than completely replaces human educational interaction. Human involvement can support verification, contextual interpretation, educational guidance, correction of inaccurate information, and deeper learning. This is a responsible-AI principle relevant to PRJ_316.

### Results / Main Conclusions

The study concludes that ChatGPT has strong potential for interactive environmental education because students generally perceive it as usable, helpful, and engaging. However, usability alone does not guarantee educational reliability. The study documents limitations involving information quality, fact checking, current information, context, language, multimedia, error handling, and domain expertise. It therefore supports combining AI capabilities with human involvement. The evidence should be described as strong perceived usability and potential educational benefits, not proof that ChatGPT improves Environmental Literacy.

### Key Contributions

1. Provides empirical usability evidence for ChatGPT in environmental education.
2. Combines expert heuristic evaluation with student usability testing.
3. Uses multiple established usability instruments.
4. Identifies usability problems affecting environmental-learning use.
5. Quantifies perceived usability using CUQ and SUS.
6. Quantifies user experience using UEQ.
7. Identifies student perceptions through interviews.
8. Highlights information-quality and fact-checking limitations.
9. Proposes a hybrid human-AI approach.
10. Provides practical considerations for responsible GenAI integration into environmental education.

### Limitations / Considerations

1. The student sample consists of only seven undergraduate participants.
2. The expert evaluation involved only three experts.
3. Participants were purposively selected rather than randomly sampled.
4. The study focuses on usability and user experience rather than long-term learning gains.
5. It evaluates ChatGPT rather than a domain-specific environmental RAG system.
6. Results from a Chinese higher-education context should not automatically generalize to Indian users.
7. Generative AI changes rapidly, so usability and capabilities may change over time.
8. The study identifies a need for more comprehensive AI-supported environmental-education research.

These limitations constrain generalizability but do not invalidate the study.

### Relevance to PRJ_316

R6 provides direct empirical evidence about the strengths and weaknesses of generative AI in environmental education. R5 primarily provided an instructional-design perspective, while R6 adds empirical usability evidence. A system can be easy and enjoyable to use while still having serious information-quality problems.

PRJ_316 should therefore evaluate not only whether the Brain works, but whether information is accurate, current, relevant, understandable, usable, recoverable after errors, accessible in preferred languages, appropriately sourced, and free from unsupported claims.

### Relevance to the AI Brain

R6 supports investigating a controlled knowledge architecture:

**Authoritative Environmental Sources → Document Processing → Knowledge Base → Retrieval → LLM → Grounded Answer → Source Reference**

This is a proposed response to the information-quality and fact-checking problems identified in R6, not an architecture proposed or implemented by R6. R6 identifies limitations in generic ChatGPT such as limited fact-checking and delayed or incomplete information; these findings motivate investigating whether a domain-specific, source-grounded RAG architecture may improve reliability.

### Relevance to Multimodal and Multilingual Interaction

The study identifies limitations caused by text-only resources and limited multimedia support. This supports considering a digital avatar, voice interaction, text interaction, potential robot interaction, and educational visual/material support in PRJ_316. Adding an avatar does not automatically solve these limitations; multimodal interaction should be evaluated for actual usefulness.

Language accessibility findings support considering English, Indian regional languages, voice input/output, and clear, simple language without prescribing a final language list before project requirements are established.

### Connection to R2 — RAG

R2 demonstrates retrieval-augmented generation as a technical concept for combining external knowledge with generation and improving factuality and specificity. R6 identifies practical problems with generic ChatGPT, including limited dynamic fact-checking, delayed information, context limitations, and limited expertise.

- **R2:** Technical solution concept
- **R6:** Practical problem and evaluation evidence

Together they justify investigating a source-grounded RAG Brain without claiming that RAG will definitely solve the identified limitations.

### Connection to R3, R5, and R1

- **R3:** Broad educational and responsible-AI evidence concerning information quality, privacy, accessibility, usability, and ethics.
- **R6:** Empirical environmental-education usability evidence.
- **R5:** How AI can be integrated into environmental learning.
- **R6:** Usability and information problems to consider when doing so.
- **R1:** The AI-powered Chacha Chaudhary mascot for Ganga conservation awareness.
- **R6:** Evaluation considerations for the mascot, including usability, information quality, accessibility, interaction, and fact checking.

### Potential Research Gap for PRJ_316

R6 demonstrates strong perceived usability of ChatGPT in environmental education while identifying limitations in fact checking, current information, context, language accessibility, and resource variety. However, it evaluates a general-purpose generative AI system rather than a domain-specific, source-grounded environmental conversational agent.

PRJ_316 can investigate whether a domain-specific RAG Brain using authoritative Ganga and environmental sources may address some information-quality limitations while maintaining an accessible and engaging conversational interface.

### Ideas for PRJ_316

1. Include source-grounded answers and preserve document/source metadata.
2. Provide source references where practical.
3. Evaluate factual correctness, response relevance, and retrieval quality.
4. Test questions outside the knowledge base and implement an appropriate fallback when reliable information cannot be retrieved.
5. Avoid unsupported claims.
6. Consider multilingual, voice, and multimedia interaction.
7. Design explicit error-handling behavior and simple explanations for non-expert users.
8. Evaluate response latency and usability using established methods.
9. Consider human or expert review for important environmental information.
10. Evaluate the system periodically as the knowledge base changes.

These are potential design and evaluation considerations, not mandatory features.

### Evaluation Framework Suggested for PRJ_316

As a proposal inspired by R6, PRJ_316 could evaluate:

1. **Knowledge quality:** Factual accuracy, source correctness, and groundedness.
2. **Retrieval quality:** Relevance of retrieved chunks and retrieval recall/precision where feasible.
3. **User experience:** Usability, clarity, engagement, and response quality.
4. **System performance:** Response latency, error handling, and robustness.

This is not the evaluation methodology used by R6.

### R6 Summary

R6 evaluates ChatGPT’s use in environmental education through heuristic evaluation, student usability testing, structured questionnaires, and semi-structured interviews. The study involved three expert evaluators and seven undergraduate students and found strong perceived usability, with a mean CUQ score of 82.8 and a mean SUS score of 87.50. However, it also identified limitations involving error prevention, fact checking, current information, contextual understanding, multimedia support, language accessibility, and information depth. The findings demonstrate that a conversational AI system can be highly usable while still requiring safeguards for information quality and educational reliability. For PRJ_316, R6 provides empirical justification for evaluating both usability and factual reliability and for investigating a source-grounded, domain-specific architecture rather than relying solely on a general-purpose LLM.

### R7 - Virtual Characters Help K-12 Students Learn and Improve Motivation: A Meta-Analysis

**Status:** Completed

**Paper ID:** R7

**Title:** Virtual Characters Help K–12 Students Learn and Improve Motivation: A Meta-Analysis

**Authors:** Noah L. Schroeder, Shan Zhang, Chris Davis Jaldi, Jessica R. Gladstone, Alexis A. López, and Emmanuel Dorley

**Year:** 2025

**Publication:** *Review of Educational Research*

**DOI / Link:** https://doi.org/10.3102/00346543251389930

**Research Category:** Virtual Characters / Educational Technology / Pedagogical Agents / Learning Outcomes / Student Motivation / Meta-Analysis

### Research Problem

Virtual characters are increasingly incorporated into technology-supported learning environments. They may attract learner attention, increase engagement, provide social presence, communicate instructional information, motivate learners, and make digital learning more interactive. However, individual studies have produced varying findings about whether virtual characters improve learning and motivation. This paper therefore synthesizes aggregated evidence across studies and educational contexts rather than relying on a single experiment.

### Research Objective

The main objective is to quantitatively synthesize research on the effects of virtual characters on:

1. Learning
2. Motivation

The study examines whether educational interventions containing virtual characters produce different outcomes from appropriate control conditions.

### Research Method

The study uses a three-level meta-analysis. The researchers identified relevant empirical studies, applied inclusion criteria, extracted study characteristics and outcome data, calculated effect sizes, statistically combined the effects, examined variation between studies, and investigated moderators where supported by the available evidence. The analysis focuses on K–12 educational contexts and school-age learners. The paper's results should not automatically be generalized to college students, adults, or the general public.

### What Is a Virtual Character?

A virtual character is a computer-generated character presented within a digital learning environment. Depending on the included studies, characters may function as instructional agents, social agents, guides, tutors, presenters, or interactive educational characters. Not every virtual character necessarily had conversational AI capabilities.

**Virtual Character ≠ Conversational AI ≠ LLM ≠ RAG**

A virtual character may simply present instructional material without possessing a conversational AI Brain.

### Learning and Motivation Outcomes

The paper examines learning outcomes and learner motivation as separate outcomes. Learning measures depend on the included studies and may concern knowledge acquisition, retention, comprehension, or performance. Motivation can involve interest, engagement, willingness to participate, enjoyment, or willingness to continue learning. Motivation should not be equated with learning; engagement can increase without proportional learning gains.

### Main Meta-Analytic Findings

The paper reports five three-level meta-analyses comparing systems with virtual characters against systems without a virtual character:

- **Learning:** Hedges’ *g* = 0.42, *p* < .001, *k* = 70; a statistically significant positive effect.
- **Motivation:** Hedges’ *g* = 0.48, *p* = .001, *k* = 47; a statistically significant positive effect.
- **Emotions:** *g* = 0.60, *p* = .20, *k* = 15; not statistically significant.
- **Perceptions:** *g* = 0.05, *p* = .88, *k* = 34; not statistically significant.
- **Cognitive load:** *g* = −0.09, *p* = .84, *k* = 5; not statistically significant.

The reported abstract values do not include confidence intervals. The significant learning and motivation effects provide aggregated evidence of positive effects in the represented studies; they do not mean that every virtual-character implementation will be effective.

### Heterogeneity and Moderators

The three-level analysis accounts for the fact that multiple outcomes may be nested within studies. Effects may vary across educational studies because of learner characteristics, instructional design, character design, subject, interaction type, intervention duration, and learning environment. These factors should not be treated as significant moderators unless the paper reports statistical support for them. The available verified summary does not provide additional moderator effects or heterogeneity statistics, so none are asserted here.

### Character Design and Pedagogical Use

The educational value of a character depends on how it is integrated into the learning experience, not merely on whether it looks human-like. The important distinction is between **having an avatar** and **using an avatar pedagogically**. A character needs an appropriate instructional role; simply adding a decorative character does not guarantee improved learning or motivation.

For PRJ_316, possible roles for a Chacha-inspired mascot include explaining concepts, answering questions, telling educational stories, asking quiz questions, encouraging reflection, and motivating conservation behavior. These are PRJ_316 design implications, not features necessarily tested by R7.

### Results / Main Conclusions

The meta-analysis provides evidence that virtual characters can support learning and motivation under the conditions represented in the included K–12 studies. It does not show that virtual characters always improve learning, and the non-significant findings for emotions, perceptions, and cognitive load demonstrate that effects differ by outcome.

### Key Contributions

1. Quantitatively synthesizes empirical research on virtual characters in education.
2. Examines learning and motivation as separate outcomes.
3. Provides aggregate evidence rather than relying on a single experiment.
4. Uses three-level meta-analytic procedures to account for nested evidence.
5. Reports variability across outcome domains.
6. Clarifies the potential educational value of virtual-character learning environments.
7. Provides implications for designing and using virtual characters in educational technology.

### Limitations / Considerations

1. The evidence is restricted to studies meeting the meta-analysis inclusion criteria.
2. The population focuses on K–12 learners.
3. Included studies may differ substantially in educational context and character design.
4. Studies may measure learning and motivation differently.
5. A positive aggregate effect does not mean every implementation will be effective.
6. Findings should not automatically generalize to adult education, higher education, or environmental awareness.

These considerations describe the scope of the evidence and do not invalidate the meta-analysis.

### Relevance to PRJ_316

R7 is primarily relevant to the avatar or mascot component of PRJ_316. R1 established the Chacha Chaudhary mascot concept, R4 established a framework for pedagogical agents and embodiment, and R7 provides quantitative evidence concerning the potential educational value of virtual characters. This supports investigating whether mascot presentation contributes to engagement, motivation, learning, social presence, or attention. R7 does not establish that a Ganga conservation mascot will produce these effects, so PRJ_316 should evaluate the mascot rather than assume its effectiveness.

### Connection to the AI Brain

R7 primarily concerns the presentation and character component, while R2 concerns knowledge and retrieval:

- **R2:** How the Brain accesses external knowledge.
- **R7:** Why an appropriately designed virtual character may improve the learning experience.

This supports studying the presentation layer separately from the knowledge and reasoning architecture. A possible PRJ_316 design inference is:

**User Input (Text / Voice) → AI Brain (RAG + LLM) → Response / Action → Digital Mascot UI**

This exact architecture does not appear in R7.

### Connection to R1, R4, R5, and R6

- **R1:** Provides the specific Chacha Chaudhary/Ganga conservation mascot concept; R7 provides broader educational evidence for investigating character-mediated engagement and motivation.
- **R4:** Classifies pedagogical purposes and embodiment; R7 provides quantitative evidence about virtual characters and learning or motivation. Together they support giving the avatar a meaningful pedagogical function rather than making it purely decorative.
- **R5:** Provides environmental-learning interaction principles; R7 provides evidence about character-mediated engagement and motivation.
- **R6:** Shows that ChatGPT can be usable while having information-quality and accessibility problems; R7 suggests that the character/interface can influence learner experience. PRJ_316 should therefore evaluate Brain quality separately from interface/character quality.

### Potential Research Gap for PRJ_316

R7 provides evidence concerning the educational effects of virtual characters in K–12 learning environments, but the meta-analysis does not specifically examine virtual characters integrated with domain-specific retrieval-augmented conversational AI for environmental or river-conservation awareness.

PRJ_316 can investigate the combination of a source-grounded AI Brain with an interactive environmental mascot, examining both information reliability and user engagement. This is a project-specific research opportunity, not a claim that no previous system has combined these technologies.

### Ideas for PRJ_316

1. Give the mascot a meaningful educational role.
2. Use the character to explain rather than merely display information.
3. Consider appropriate expressions or animations where feasible.
4. Consider voice and conversational interaction.
5. Evaluate engagement, motivation, and interaction quality.
6. Compare character-based and non-character interfaces if project scope allows.
7. Separate evaluation of the AI Brain from evaluation of the avatar/interface.
8. Avoid excessive animation or decoration that distracts from learning.
9. Keep character behavior consistent with the educational purpose.
10. Test whether the character improves user experience rather than assuming it does.
11. Consider accessibility when designing the avatar and interaction.

These are potential design and evaluation considerations, not mandatory project requirements.

### Important Research Insight

The literature should not be interpreted as saying that an avatar itself is the source of intelligence.

- **Avatar/Mascot:** Presentation and social/educational interaction layer
- **AI Brain:** Knowledge retrieval, reasoning, and response generation

This separation allows the project to improve or replace the avatar without redesigning the underlying knowledge system.

### Evaluation Proposal for PRJ_316

The avatar component could eventually be evaluated separately from the Brain.

- **Avatar evaluation:** Engagement, motivation, perceived attractiveness, interaction quality, ease of understanding, and educational usefulness.
- **Brain evaluation:** Factual accuracy, retrieval relevance, groundedness, source correctness, and response quality.

This is a PRJ_316 evaluation proposal inspired by the literature, not a claim that these exact metrics were used in R7.

### R7 Summary

R7 is a three-level meta-analysis investigating the effects of virtual characters in educational settings, with a particular focus on learning and motivation among K–12 learners. By quantitatively synthesizing multiple empirical studies, it reports positive effects on learning (*g* = 0.42, *p* < .001, *k* = 70) and motivation (*g* = 0.48, *p* = .001, *k* = 47), while finding no statistically significant effects on emotions, perceptions, or cognitive load in the reported analyses. The study is relevant to PRJ_316 because the project includes an interactive digital mascot as a presentation and engagement layer. However, the findings do not show that simply adding an avatar guarantees improved learning or motivation. R7 instead supports evaluating whether the mascot contributes meaningful educational and engagement benefits when integrated with the AI Brain, complementing R1, R4, R5, and R6.

### R8 - A Systematic Review of Pedagogical Agent Research: Similarities, Differences and Unexplored Aspects

**Status:** Completed

**Paper ID:** R8

**Title:** A systematic review of pedagogical agent research: Similarities, differences and unexplored aspects

**Authors:** Laduona Dai, Merel M. Jung, Marie Postma, Max M. Louwerse

**Year:** 2022

**Publication:** *Computers & Education*, Volume 190, Article 104607, pages 1–28

**DOI:** https://doi.org/10.1016/j.compedu.2022.104607

**Research Category:** Pedagogical Agents / Virtual Characters / Educational Technology / Human-Computer Interaction / Learning Outcomes / Agent Design

### Research Problem

Technological advances have enabled increasingly human-like pedagogical agents in educational environments. Although previous research has reported benefits, findings remain inconsistent regarding which agent design characteristics contribute to effective learning. Potential characteristics include appearance, embodiment, identity, role, function, voice, animation, and interaction modality. Differences in research designs, experimental conditions, learner populations, evaluation methods, measurement instruments, and agent implementations may partly explain these inconsistencies. The paper therefore systematically reviews recent pedagogical-agent research to identify common patterns, limitations, and unexplored directions.

### Research Objectives / Questions

- **RQ1:** To what extent does pedagogical agent design help learning? This includes appearance, embodiment, identity, role, function, voice, and technical implementation.
- **RQ2:** What are the contextual features and experimental designs in pedagogical agent research? This includes educational level, sample size, sample-size calculation, learning environment, experimental design, and study setting.
- **RQ3:** How are the effects of learning outcomes, learners’ motivation, and agent perception evaluated? This includes learning-outcome measures, motivation measures, agent-perception measures, and knowledge levels assessed.

### Review Scope

The review covers pedagogical-agent research published from 2010 to 2021. It systematically searched ProQuest, Web of Science, EBSCOhost, Scopus, and Wiley. The final review included 75 studies from 67 articles. These are research studies, not participants.

### Eligibility Criteria

The review focused on empirical research involving peer-reviewed English-language journal articles published between January 2010 and April 2021, quantitative evaluation of learning outcomes, experimental designs with control groups, embodied pedagogical agents, and participants below 30 years of age. An agent had to be embodied, meaning at least its head, part of its body, or full body was visible. Conventional text-only chatbots were therefore outside the review’s scope. R8 primarily studies embodied pedagogical agents and does not represent the entire conversational-AI literature.

### Three Main Analysis Directions

The review investigates:

1. Agent design features and implementations.
2. Moderating and contextual variables.
3. Instruments used to evaluate agent effectiveness.

These dimensions help distinguish what the mascot looks like and does, where and how it is used, and how its outcomes are measured.

### Agent Design Features

The review examines appearance, embodiment, identity, role, function, voice, animation, and other technical implementation details. Most studies used 3D humanoid agents. Smaller numbers used 2D humanoid agents, 2D non-humanoid agents, 3D non-humanoid agents, and recordings of real humans. Embodiment was also categorized by visible body parts:

1. Head
2. Head and shoulders
3. Upper body
4. Full body

### Agent Role and Function

The literature considers roles such as expert, motivator, mentor, and learner, together with functions such as demonstrating, coaching, providing information, testing, and eliciting information. An avatar’s presence does not determine its pedagogical role. A Chacha-inspired mascot could potentially function as an information provider, motivator, educational guide, or quiz facilitator, but these are PRJ_316 design possibilities rather than functions demonstrated by R8.

### Voice and Animation

The review examines voice and appearance implementation. Prior literature reports mixed findings concerning human versus synthesized voice, static versus animated agents, and different agent formats. R8 does not support simplistic conclusions that human voice is always better or animation always improves learning; effects can depend on context and experimental conditions.

### Human-Likeness

Human-likeness remains an unresolved issue. Although most studies used 3D humanoid agents, many were not highly human-like or did not use a strong fictional identity. Future research opportunities include human-like characters, fictional identities, non-human characters, and different levels of anthropomorphism. This is relevant to PRJ_316 because Chacha Chaudhary is a recognizable fictional and cultural identity, but R8 does not specifically study Chacha Chaudhary.

### Contextual Variables

The review examines learner educational level, learning environment, sample size, experimental design, and study setting. Reviewed learning environments were mainly classrooms and research laboratories, with limited exploration of newer environments such as virtual reality. R8 notes underrepresentation of K–12 populations in the pedagogical-agent literature included in its analysis, so PRJ_316 should define its target audience rather than assume that findings from one learner group generalize to everyone.

### Virtual Reality

Pedagogical agents have rarely been studied in immersive virtual-reality environments despite the established use of VR in education. VR is an underexplored direction, not a required feature for PRJ_316, and should only be considered as a future extension if project scope permits.

### Learning Outcome Evaluation

Multiple-choice questions are commonly used to evaluate learning. The paper notes that MCQs may suit lower levels of knowledge in Bloom’s taxonomy but are less suitable for higher levels. A simple PRJ_316 quiz may measure recall but may not adequately measure understanding, application, analysis, evaluation, or deeper reasoning. Learning outcomes, motivation, and agent perception should be evaluated separately.

### Motivation and Agent Perception

The review examines instruments for learner motivation and perception of the agent. Relevant perception dimensions can include perceived characteristics, persona, social presence, appearance, and interaction. These measures help assess acceptance and engagement with the agent, but:

**Learning ≠ Motivation ≠ Agent perception**

A mascot may be enjoyable without necessarily producing greater learning. PRJ_316 could evaluate agent perception separately from the factual accuracy of the Brain.

### Main Findings

The review finds that pedagogical-agent effectiveness varies with agent design and contextual factors. The overall trend reported by the authors is that agents with higher levels of embodiment tended to facilitate learning more than agents with lower or no embodiment; this is not evidence that every embodied agent is more effective. The review also finds that most studies use 3D humanoid agents, human-likeness is insufficiently explored, VR-based agents are relatively uncommon, K–12 research is underrepresented, sample-size calculations are often absent, many studies use relatively small samples, learning environments are often classrooms or laboratories, long-term effects are understudied, MCQs dominate learning-outcome evaluation, and motivation and agent perception require appropriate measurement.

### Long-Term Learning Effects

Many studies focus on immediate learning outcomes rather than whether benefits remain over time. Short-term evaluation may be realistic for a limited-scope project, but short-term engagement does not establish long-term educational impact.

### Methodological Issues

The field includes small samples, missing sample-size calculations, differing experimental designs, evaluation instruments, learning measures, and agent implementations. These differences make direct comparison difficult and help explain conflicting conclusions in prior research.

### Results / Main Conclusions

Pedagogical agents can support learning, but effectiveness depends on agent design and contextual variables. The evidence does not establish one universally optimal design. The potential of pedagogical agents remains incompletely explored, particularly regarding human-likeness, fictional identity, VR, underrepresented learner populations, long-term learning effects, and improved experimental methodology.

### Key Contributions

1. Provides a systematic review of pedagogical-agent research from 2010–2021.
2. Reviews 75 studies from 67 articles.
3. Examines agent design characteristics.
4. Examines contextual and experimental factors.
5. Reviews learning-outcome evaluation methods.
6. Reviews motivation and agent-perception measures.
7. Identifies inconsistencies in previous findings.
8. Identifies methodological weaknesses in the field.
9. Identifies underexplored areas including human-likeness and VR.
10. Provides directions for future pedagogical-agent research.

### Limitations / Considerations

1. The review includes only studies meeting its eligibility criteria.
2. It focuses on embodied pedagogical agents, so text-only conversational agents are outside its scope.
3. Its publication period is 2010–2021, so newer developments are not represented.
4. The participant criterion limits the review to populations below 30 years of age.
5. The reviewed studies vary substantially in experimental design, measures, and agent implementation.
6. Many studies have relatively small samples.
7. Long-term learning effects are not well studied.
8. Most research occurs in classrooms or laboratory environments.
9. The evidence is insufficient to establish a single universally optimal agent design.

These limitations describe the review’s scope and remaining research needs; they do not invalidate the review.

### Relevance to PRJ_316

R8 is highly relevant to the avatar and interaction component of PRJ_316. R1 provides the Ganga/Chacha mascot concept, R4 provides a conceptual framework for pedagogical conversational agents, R7 provides meta-analytic evidence concerning virtual characters and learning or motivation, and R8 systematically examines agent design features, contextual variables, and evaluation methods. R8 therefore helps answer what design and evaluation factors should be considered when building the PRJ_316 mascot.

### Relevance to the Avatar

Based on R8, the mascot should be treated as an educational agent rather than simply an animated image. Potential design dimensions include:

- **Identity:** Chacha-inspired educational mascot
- **Role:** Environmental educator or guide
- **Function:** Explain, answer, motivate, quiz, and guide users
- **Voice:** Potential voice interaction
- **Animation:** Expressions and gestures where appropriate

These are proposed PRJ_316 choices, not findings of R8.

### Relevance to the AI Brain

R8 concerns pedagogical-agent design rather than knowledge retrieval:

- **R2:** RAG and external knowledge
- **R8:** Agent design, interaction, and evaluation

A modular PRJ_316 inference could be:

**User → Text / Voice → AI Brain (RAG + LLM) → Response → Avatar / Voice / Robot → User**

The Brain handles knowledge and response generation, while the avatar handles presentation, embodiment, and social or educational interaction. This exact architecture does not come from R8.

### Evaluation Implications for PRJ_316

As a project proposal inspired by the review, PRJ_316 could separate:

- **Brain / Knowledge Evaluation:** Factual accuracy, retrieval relevance, groundedness, and source correctness.
- **Educational Evaluation:** Knowledge gain, understanding, ability to apply concepts, and environmental awareness.
- **User / Avatar Evaluation:** Motivation, engagement, agent perception, usability, and social presence where relevant.
- **System Evaluation:** Response time, error handling, and robustness.

R8 does not require this exact evaluation framework.

### Connection to R7

R7 is a meta-analysis of virtual characters and learning or motivation, while R8 is a systematic review of agent design, context, and evaluation. R7 provides aggregate evidence that virtual characters can potentially support learning and motivation; R8 explains why effects can vary by design and context. PRJ_316 should therefore evaluate its specific mascot rather than assume “avatar = better learning.”

### Connection to R4, R5, and R6

- **R4:** Provides the broader conceptual framework for pedagogical purposes and technological or embodiment characteristics.
- **R8:** Provides deeper examination of design features and experimental evaluation.
- **R5:** Connects AI chatbots with environmental-literacy instructional design.
- **R8:** Connects pedagogical-agent design with learning evaluation.
- **R6:** Identifies usability and information-quality problems in environmental ChatGPT use.
- **R8:** Supports evaluating AI quality separately from agent/interface quality.

Together, these papers connect educational purpose, conversational interaction, appropriate agent presentation, and meaningful evaluation.

### Potential Research Gap for PRJ_316

R8 demonstrates that pedagogical-agent effectiveness varies with agent design, contextual factors, and evaluation methods, while identifying underexplored areas such as human-like identity, immersive environments, and long-term learning effects. However, the review focuses on embodied pedagogical agents and does not specifically address domain-specific environmental conversational agents that combine an embodied mascot with retrieval-augmented generation.

PRJ_316 can investigate integrating a source-grounded environmental AI Brain with an embodied digital mascot, evaluating both knowledge reliability and user or educational outcomes. This is a project-specific research opportunity, not a claim that no previous work combines these technologies.

### Ideas for PRJ_316

1. Define the mascot’s educational role explicitly.
2. Define its identity and persona consistently.
3. Decide the appropriate embodiment level.
4. Use animation only when it supports communication.
5. Consider voice as part of the agent design.
6. Design responses around educational functions.
7. Separate Brain evaluation from avatar evaluation.
8. Evaluate motivation separately from learning.
9. Evaluate agent perception separately from factual accuracy.
10. Avoid relying only on MCQs if educational impact is evaluated.
11. Consider higher-level learning measures where feasible.
12. Record sample size and evaluation methodology carefully.
13. Consider short-term and, if possible, longer-term outcomes.
14. Test the mascot with representative users.
15. Avoid assuming that greater human-likeness automatically produces better learning.

These are potential design considerations, not mandatory requirements.

### Important Research Insight

The literature indicates that the effectiveness of a pedagogical agent is not determined by appearance alone. Agent design, pedagogical function, learner context, and evaluation methodology all influence the observed outcome.

For PRJ_316, mascot design, pedagogical role, AI Brain, user context, and evaluation must be considered together.

### R8 Summary

R8 systematically reviews pedagogical-agent research published between 2010 and 2021, analyzing 75 studies from 67 articles. The review examines agent design features, contextual and experimental variables, and methods used to evaluate learning, motivation, and agent perception. The findings indicate that pedagogical-agent effectiveness varies according to design and context, with a general trend toward greater learning support from more embodied agents, while also highlighting that no single agent design is universally optimal. The review identifies gaps including limited research on human-likeness, fictional identities, virtual-reality agents, long-term learning effects, and methodological consistency. For PRJ_316, R8 provides an evidence-based foundation for treating the digital mascot as an educational agent with a defined identity, role, and interaction design, while emphasizing the need to evaluate the mascot separately from the AI Brain. Combined with R1, R2, R4, R5, R6, and R7, it strengthens the project’s foundation for integrating reliable conversational AI with an educational embodied interface.

### R9 - Exploring Persona Characteristics in Learning: A Review Study of Pedagogical Agents

**Status:** Completed

**Paper ID:** R9

**Title:** Exploring Persona Characteristics in Learning: A Review Study of Pedagogical Agents

**Authors:** Yayi Tao, Guangli Zhang, Di Zhang, Fang Wang, Yun Zhou, Tao Xu

**Year:** 2022

**Publication:** *Procedia Computer Science*, Volume 201, pages 87–94

**Conference:** The 13th International Conference on Ambient Systems, Networks and Technologies (ANT 2022)

**DOI:** https://doi.org/10.1016/j.procs.2022.03.014

**Publication / Article Link:** https://www.sciencedirect.com/science/article/pii/S1877050922004264

**Research Type:** Literature review / review study

**Research Category:** Pedagogical Agents / Avatar Design / Educational Technology

### Research Problem

The paper investigates how persona characteristics of pedagogical agents influence learners’ learning performance and learning experience. Such agents can provide instruction, coaching, feedback, emotional support, and social support in interactive learning environments. Although agents may support learning, poorly designed agents may distract learners or increase external cognitive load. The review therefore examines which persona characteristics may contribute to effective learning and how they should inform agent design.

### Research Objective

The review examines existing research on pedagogical-agent personas, how characteristics affect learning outcomes and learning experience, and implications for designing effective agents. It focuses on five characteristics: appearance, gender, facial expression, voice/sound, and movement.

### Methodology and Evidence

The authors reviewed literature using ScienceDirect, Google Scholar, and Web of Science. Search descriptors included combinations such as “agent persona AND pedagogical agent” and “agent persona AND virtual human.” Findings were organized around appearance, gender, facial expression, voice, and motion.

This is a literature review rather than a new user experiment. No new participant dataset was collected; the evidence comes from previously published studies involving different learners, settings, agent designs, voices, expressions, and movements. No participant count is asserted for the review itself.

### Persona Characteristics

#### 1. Appearance

The review considers human versus non-human, human-like versus cartoon-like, 2D versus 3D, realistic versus stylized, and humanoid versus non-humanoid agents. Appearance can influence learning, attention, emotion, and perception, but greater realism is not automatically better. Overly realistic agents may create discomfort or distraction, including effects associated with the uncanny valley, while non-humanoid or cartoon-like agents can perform well in some educational contexts.

#### 2. Gender

Some reviewed studies reported effects on perceived credibility or preferences, while others found no significant effect on learning. The paper reaches no unified conclusion that agent gender improves learning outcomes.

#### 3. Facial Expression

Reviewed expressions include happy, sad, surprised, neutral, bored, content, and frustrated. Dynamic expressions may improve learning or emotional engagement, but mismatched expressions can have negative effects. For example, a smiling agent could produce lower positive emotion when its facial expression did not match the generated voice emotion. Expressions should therefore be natural and contextually consistent.

#### 4. Voice / Sound

The review compares human-recorded and synthesized voices, voice quality, tone, intonation, and enthusiastic versus neutral speech. Human voices may provide stronger emotional expression in some contexts, but synthesized speech can also serve educational purposes. No universally superior voice design is established; audience, emotional tone, and cognitive load should be considered.

#### 5. Movement

Agent movement includes head and eye movement, facial movement, hand and body movement, pointing/deictic gestures, metaphorical gestures, and beat gestures. Appropriate gestures can support attention, understanding, knowledge transfer, and social presence. Motion should have a clear instructional purpose rather than become visual distraction.

### Technologies / Models Used

This review study does not propose or implement a specific AI/ML model or software architecture. It does not use RAG, ChromaDB, vector databases, LLMs, GPT, or embedding models. It discusses implementations found in prior studies, including animated agents, virtual agents, 2D/3D agents, synthesized and human voices, gestures, facial expressions, and virtual-reality environments.

### Main Findings

1. Persona characteristics can influence learning experiences and outcomes.
2. Appearance matters, but greater realism does not necessarily produce better learning.
3. Human-like or highly realistic agents may increase cognitive load or distraction.
4. 2D, cartoon-like, non-humanoid, and stylized agents can be effective depending on context.
5. Gender can affect credibility or preference in some studies, but has no consistent learning effect.
6. Facial expressions can affect emotion and engagement when natural and appropriate.
7. Voice quality, speech type, tone, and intonation can influence perception and emotional experience without establishing one best voice.
8. Appropriate gestures, eye gaze, and body movements can support attention and knowledge transfer.
9. Poorly designed agents can increase external cognitive load and distract learners.
10. Effective persona design depends on target learners, objectives, content, interaction context, development cost, and complexity.

### Key Contributions

The paper organizes pedagogical-agent persona research around appearance, gender, facial expression, voice, and motion. It synthesizes previous findings and provides design implications for supporting learning without unnecessarily increasing cognitive load. It emphasizes alignment with target users, learning objectives, communicated information, interaction requirements, and development cost.

### Limitations / Research Considerations

1. The paper is a literature review rather than a new experimental evaluation.
2. Reviewed studies differ in experimental conditions, learners, agent designs, and educational contexts.
3. Findings do not define one universally optimal avatar or persona design.
4. The paper reports no definite consensus about the overall impact of pedagogical agents.
5. Some persona characteristics have conflicting findings.
6. Highly realistic or complex agents can increase development cost and potentially cognitive load.
7. The review focuses on persona characteristics rather than an underlying AI knowledge architecture.

These are considerations for applying the findings and do not invalidate the review.

### Relevance to PRJ_316

R9 is highly relevant to the digital-avatar portion of PRJ_316. The project should not design the mascot purely for visual attractiveness; appearance, voice, expressions, and movements should support educational purpose.

- **Appearance:** A recognizable stylized or cartoon-like avatar may be preferable to unnecessary realism.
- **Facial expressions:** Limited meaningful expressions could correspond to conversational context, such as positive feedback for quiz answers, concern when discussing pollution, or encouragement for conservation actions.
- **Voice:** Selection should consider audience, language, clarity, emotional appropriateness, and synchronization.
- **Movement and gestures:** Simple gestures could reinforce visuals, quiz options, conservation instructions, or relevant statistics.
- **Cost and complexity:** A college mini-project should prioritize educational interaction over excessive visual realism.

These are PRJ_316 design possibilities, not findings that validate a Chacha Chaudhary choice specifically.

### Connection to Previous Papers

- **R1:** Establishes the Ganga/Chacha conservation mascot application; R9 provides persona and avatar design considerations without specifically validating Chacha Chaudhary.
- **R3:** Provides broad conversational-AI and responsible-education context; R9 focuses on embodied persona and interface design.
- **R4:** Provides the broader pedagogical-agent framework; R9 gives more detailed persona considerations.
- **R8:** Provides broader agent-design context; R9 examines appearance, gender, facial expression, voice, and motion in greater detail.
- **R6:** Highlights usability, engagement, response quality, language accessibility, and human-AI issues; R9 adds that avatar presentation can affect learning experience even when the Brain provides good answers.

Together these distinctions help separate the AI/conversational Brain, pedagogical role, and avatar/persona/interface.

### Research Gap for PRJ_316

A potential project-specific opportunity is integrating:

1. A source-grounded environmental AI Brain
2. A pedagogically designed digital avatar
3. Voice interaction
4. Contextually appropriate facial expressions and gestures
5. Separate evaluation of AI response quality and avatar usability

R9 does not provide solutions for Ganga-specific knowledge grounding, government-source retrieval, RAG, environmental fact verification, knowledge-base maintenance, source citation, or current environmental information. PRJ_316 can combine R9’s avatar/persona findings with R2’s RAG foundation and R3–R6’s educational and environmental findings.

### Ideas for PRJ_316

1. Keep the avatar recognizable and approachable.
2. Avoid unnecessary photorealism.
3. Match expressions to response meaning and emotional tone.
4. Synchronize facial expressions with voice.
5. Use simple, meaningful gestures.
6. Avoid animation that distracts from educational content.
7. Choose voice characteristics appropriate for the target audience.
8. Consider multilingual voice interaction.
9. Keep the avatar lightweight enough for a college mini-project.
10. Evaluate the avatar separately from the Brain.

**Brain evaluation** may include factual correctness, groundedness, retrieval quality, and relevance. **Avatar evaluation** may include usability, engagement, clarity, perceived helpfulness, and distraction. AI Brain quality and avatar quality should not be treated as the same thing.

### Concise Summary

R9 reviews how pedagogical-agent persona characteristics affect learning and learning experience. It identifies appearance, gender, facial expression, voice, and movement as important characteristics that can influence attention, emotion, perception, and learning, while finding no universally optimal persona design. Poorly designed or overly realistic agents may increase cognitive load or distract learners. For PRJ_316, the paper is mainly relevant to the digital-avatar component and supports designing the avatar around educational goals, target users, appropriate voice and expressions, meaningful gestures, and manageable implementation complexity. It does not provide a RAG or AI-Brain architecture.

### R10 - How Effective are Pedagogical Agents for Learning? A Meta-Analytic Review

**Status:** Completed

**Paper ID:** R10

**Title:** How Effective are Pedagogical Agents for Learning? A Meta-Analytic Review

**Authors:** Noah L. Schroeder, Olusola O. Adesope, Rachel Barouch Gilbert

**Year:** 2013

**Publication:** *Journal of Educational Computing Research*, Volume 49, Issue 1, pages 1–39

**DOI:** https://doi.org/10.2190/EC.49.1.a

**Official Article:** https://journals.sagepub.com/doi/10.2190/EC.49.1.a

**Research Type:** Meta-analysis

**Research Category:** Pedagogical Agents / Educational Technology / Learning Effectiveness

### Research Problem

The paper investigates whether pedagogical agents improve learning outcomes. Pedagogical agents are on-screen characters incorporated into educational software or learning environments to facilitate instruction. Because individual studies reported inconsistent results, the authors conducted a meta-analysis to estimate the overall effect and determine whether contextual and methodological factors moderate that effect.

### Research Objective

The objectives were to:

1. Determine the overall effectiveness of pedagogical agents for learning.
2. Examine whether contextual characteristics influence effectiveness.
3. Examine whether methodological characteristics influence measured effectiveness.
4. Identify conditions under which pedagogical agents may be more or less beneficial.

### Methodology

The authors conducted a quantitative meta-analysis of previous empirical studies, aggregating 43 studies involving 3,088 participants. The analysis synthesized learning outcomes and examined moderators, including educational level, communication modality, and contextual and methodological characteristics.

### Dataset / Sample

The meta-analysis included 43 studies and 3,088 total participants. The underlying studies involved both K–12 and post-secondary learners in educational settings. These figures describe the reviewed evidence, not a new experiment conducted by the authors.

### Proposed Approach / Framework

This paper does not propose a new AI architecture. Its analytical framework is:

**Existing pedagogical-agent studies → Comparable learning outcomes → Effect-size calculation and synthesis → Overall effect estimate → Contextual and methodological moderator analysis**

The central point is that effectiveness depends not only on whether an agent is present, but also on context and implementation.

### Technologies / Models Used

The paper does not introduce a modern AI/ML model or conversational-AI architecture. It does not use RAG, ChromaDB, vector databases, LLMs, GPT, or embedding models. It concerns pedagogical agents implemented in educational software and learning environments, with technologies varying across the underlying studies.

### Main Results

#### Overall Effect

Pedagogical agents produced a small, statistically significant positive effect on learning. This supports measurable learning benefits in the aggregated evidence but does not establish that an agent automatically produces major improvements.

#### Educational Level

The effect was stronger for K–12 students than for post-secondary students. This is relevant if PRJ_316 ultimately targets school students or younger audiences, but the finding should not be assumed to apply automatically to the project’s target population.

#### Communication Modality

Within the analyzed studies, agents communicating through on-screen text were more effective for learning than agents communicating through narration. This comparison does not mean narration is inherently ineffective or that text is universally better than voice.

#### Moderating Factors

The overall effect was moderated by contextual and methodological characteristics. Thus, effectiveness depends on factors surrounding the learning environment and study design rather than on simply having an avatar.

### Key Contributions

1. Provides quantitative evidence across multiple pedagogical-agent studies.
2. Demonstrates a small but statistically significant positive overall learning effect.
3. Shows that effectiveness varies according to contextual and methodological factors.
4. Finds stronger benefits for K–12 learners than post-secondary learners.
5. Finds on-screen text more effective than narration in the analyzed studies.
6. Provides a foundation for research into pedagogical-agent design and implementation.

### Limitations / Research Considerations

1. Although statistically significant, the overall effect was small.
2. Effectiveness varied according to context and methodology, so results cannot automatically generalize to Ganga or environmental awareness.
3. Published in 2013, the evidence predates modern large language models, generative AI, RAG, and current multimodal AI systems.
4. The paper primarily investigates educational interfaces and characters, not whether a more intelligent underlying AI Brain produces better outcomes.

These considerations support careful application of the findings and do not invalidate the meta-analysis.

### Relevance to PRJ_316

R10 supports the general rationale for an interactive digital mascot intended to educate and engage users about Ganga and river conservation, while emphasizing that the avatar itself is not enough. PRJ_316 must also consider educational content quality, interaction design, target audience, communication modality, learning objectives, and evaluation methodology.

### Implications for the PRJ_316 Brain

If an attractive avatar produces incorrect information, irrelevant answers, unsupported claims, or poor explanations, its presence does not guarantee learning effectiveness. The Brain and avatar should therefore remain separate but complementary:

- **Brain:** Knowledge retrieval, answer generation, factual grounding, educational explanation, question answering, and possible quiz generation.
- **Avatar:** Visual presentation, voice, facial expressions, gestures, and engagement.

This supports the modular architecture direction identified across R1–R9.

### Connection to Previous Papers

- **R1:** Provides domain/application motivation; R10 provides broader evidence concerning pedagogical-agent effectiveness without validating the Chacha Chaudhary or Ganga-conservation application.
- **R2:** Addresses how the Brain can use external knowledge; R10 addresses whether the pedagogical-agent interface can support learning.
- **R3:** Provides the educational conversational-AI and responsible-use landscape; R10 provides older quantitative evidence of learning effects.
- **R4:** Provides a conceptual framework for pedagogical-agent functions; R10 provides evidence of measurable learning benefits.
- **R5:** Connects AI chatbots with environmental-literacy design; R10 provides broader evidence supporting educational agents.
- **R6:** Emphasizes usability and environmental-AI evaluation; R10 emphasizes learning outcomes. PRJ_316 should distinguish usability, engagement, response quality, and learning or awareness outcomes.
- **R7:** Focuses on virtual characters, learning, and motivation; R10 provides broader meta-analytic evidence about pedagogical agents and learning.
- **R8/R9:** Examine agent design and persona characteristics; R10 asks whether pedagogical agents have a positive learning effect.

### Research Gap for PRJ_316

#### Gap 1 — Modern AI Brain and Pedagogical Agent

R10 predates modern generative AI. A contemporary implementation could combine source-grounded retrieval, generative AI, conversational interaction, and pedagogical-agent presentation while evaluating environmental learning or awareness.

#### Gap 2 — Domain-Specific Environmental Education

The meta-analysis covers pedagogical-agent research broadly and does not specifically establish effectiveness for Ganga conservation, Indian river systems, Namami Gange, or Indian environmental awareness. PRJ_316 can evaluate its system in this specific context.

#### Gap 3 — Separate Component Evaluation

PRJ_316 should not evaluate only whether users like the avatar. It can separately measure:

- **Brain:** Factual correctness, groundedness, retrieval relevance, and answer relevance.
- **Interaction:** Usability, engagement, response time, and voice interaction.
- **Educational outcome:** Knowledge gain, awareness, quiz performance, and intended conservation actions.

#### Gap 4 — Target Audience

R10 found stronger effects for K–12 learners than post-secondary learners. If PRJ_316 targets school students or younger audiences, this finding can inform evaluation design, but the project must test its own target population rather than assume automatic transfer.

### Ideas for PRJ_316

1. Define a clear educational objective for every major interaction.
2. Avoid treating the avatar as merely decorative.
3. Use the Brain to provide meaningful educational explanations.
4. Support text interaction even if voice interaction is also available.
5. Evaluate the system with actual users.
6. Measure learning or awareness separately from user satisfaction.
7. Compare pre- and post-interaction knowledge where feasible.
8. Use quizzes to measure knowledge retention or immediate learning.
9. Evaluate whether the avatar improves engagement without distracting from information.
10. Report limitations honestly because pedagogical-agent effects are context-dependent.

### Overall Research Gap Across R1–R10

The ten papers provide strong foundations in separate areas:

- **R1:** Ganga conservation mascot/application concept
- **R2:** RAG and knowledge-grounded generation
- **R3:** Conversational AI in education and responsible AI
- **R4:** Pedagogical conversational-agent framework
- **R5:** AI chatbot and environmental literacy
- **R6:** Environmental AI usability and evaluation
- **R7:** Virtual characters and learning/motivation
- **R8:** Pedagogical-agent design and evaluation
- **R9:** Avatar persona characteristics
- **R10:** Meta-analytic evidence of pedagogical-agent learning effects

These areas are not fully integrated into one clearly defined system. A project-level opportunity identified from the reviewed literature is:

**Developing and evaluating a domain-specific environmental conversational agent that combines a source-grounded AI knowledge Brain with a pedagogically designed digital avatar, while separately evaluating knowledge quality, interaction quality, engagement, and educational outcomes.**

This is not claimed as a proven novel gap across the entire academic literature.

### R10 Summary

R10 is a 2013 meta-analysis of 43 studies involving 3,088 participants that investigates the learning effectiveness of pedagogical agents. It finds a small, statistically significant positive overall effect, stronger effects for K–12 than post-secondary learners, and greater effectiveness for on-screen text than narration in the analyzed studies. The study also shows that effects depend on contextual and methodological factors. Because it predates modern generative AI and RAG, it should be used as evidence about pedagogical-agent effectiveness rather than modern AI architectures. For PRJ_316, R10 supports evaluating the avatar and AI Brain as complementary but separate components and measuring factual quality, usability, engagement, and educational outcomes.

## Potential Research Gap

This section synthesizes the reviewed literature across Ganga conservation, knowledge-grounded AI, educational conversational AI, environmental education, digital avatars, pedagogical agents, and evaluation methods.

R9 strengthens the avatar/interface side of PRJ_316, while R2 provides the foundation for the AI Brain. Across R1–R10, a project-level opportunity is to combine a source-grounded environmental conversational system with a pedagogically designed avatar and evaluate knowledge quality, interaction quality, engagement, and educational outcomes separately.

## Literature Review Conclusion

The reviewed literature establishes the major foundations required for PRJ_316. R1 provides the closest application-level precedent for an AI-powered mascot for Ganga conservation. R2 provides the technical foundation for Retrieval-Augmented Generation and combining a generative model with external non-parametric knowledge. R3–R6 establish educational, environmental, usability, and responsible-AI considerations for conversational systems. R7–R10 establish the role and limitations of virtual and pedagogical agents in learning, including persona design, engagement, and learning effectiveness.

PRJ_316 should not be treated as simply an avatar project or simply a chatbot project. Its potential contribution is an integrated educational system consisting of:

1. A domain-specific knowledge/AI Brain
2. A conversational interaction layer
3. A pedagogically designed digital avatar
4. Educational interaction features such as quizzes and explanations
5. Evaluation of factual quality, usability, engagement, and educational outcomes

The strongest technical opportunity identified for the Brain is source-grounded knowledge retrieval using RAG, while the strongest design opportunity for the avatar is contextually appropriate persona and pedagogical-agent design.

## Research Status

| ID | Paper | Status | Primary Relevance |
|---|---|---|---|
| R1 | AI-Powered Chacha Chaudhary Mascot for Ganga Conservation Awareness | COMPLETED | Domain/application baseline |
| R2 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | COMPLETED | RAG foundation |
| R3 | Conversational AI Agents in Education | COMPLETED | Educational conversational AI / responsible AI |
| R4 | Pedagogical AI Conversational Agents in Higher Education | COMPLETED | Pedagogical-agent framework |
| R5 | Designing a Flipped AI-Chatbot Learning Module for Environmental Literacy | COMPLETED | Environmental education |
| R6 | Evaluating the Efficacy of ChatGPT in Environmental Education | COMPLETED | Evaluation / usability |
| R7 | Virtual Characters Help K–12 Students Learn and Improve Motivation | COMPLETED | Virtual characters / learning / motivation |
| R8 | A Systematic Review of Pedagogical Agent Research | COMPLETED | Agent design / evaluation |
| R9 | Exploring Persona Characteristics in Learning | COMPLETED | Avatar / persona design |
| R10 | How Effective are Pedagogical Agents for Learning? | COMPLETED | Evidence of learning effectiveness |

**Overall Literature-Review Status:** COMPLETED

R1–R10 literature review completed. The reviewed literature covers the application domain, RAG/knowledge grounding, educational conversational AI, environmental education, AI evaluation, virtual characters, pedagogical-agent design, persona characteristics, and learning effectiveness.
