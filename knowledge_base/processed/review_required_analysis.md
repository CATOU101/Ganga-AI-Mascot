# REVIEW_REQUIRED Section Analysis

Generated: 2026-09-12

All sections with review_status HUMAN_REVIEW_REQUIRED: 542 section_classification REVIEW_REQUIRED records plus 12 OCR_REQUIRED records. Existing classifications were not changed.

Categories are evidence-grounded flags, not reclassifications. The source artifact records one dominant non-OCR rationale for 542 records: the extracted heading is not sufficiently interpretable. Suggested categories with no supporting evidence are reported with zero counts rather than inferred.

## Summary

- review required sections analyzed: **554**
- classification REVIEW REQUIRED: **542**
- classification OCR REQUIRED: **12**
- primarily extraction noise: **109**
- extraction noise flagged: **219**
- require actual human content judgement: **433**
- require OCR: **12**
- probably safely reclassifiable using deterministic rules: **109**
- genuinely require manual review: **433**
- category counts are overlapping: **True**

## Reason categories

Counts overlap where one section has multiple evidence-supported reasons.

### NOISY_EXTRACTION
- Count: **219** (39.53% of 554)
- Typical reason: The recorded rationale says the extracted heading is not sufficiently interpretable; the label is missing, malformed, fragmented, abbreviated, or looks like an extraction artifact.
- Recommended next action: Repair or validate the heading against adjacent extracted pages and the PDF structure. Re-run only deterministic heading normalization; do not reclassify content until the repaired context is readable.
- Representative examples:
  - `10_019SEC.pdf`, pages 46-46, section `N P K`: 46 | P a g e Table A.16: Consumption of Fertilizers and Pesticides in West Bengal Year Total Fertilizer Consumption in tones Fertilizer Pesticide Consumption Ingredient Active N P 
  - `10_037_ Implementation Mechanism.pdf`, pages 27-27, section `i. a co-operative society registered under any law relating to cooperative`: Report Code: 037_GBP_IIT_PLG_S&R_01_Ver 1_Dec 2013 27 | P a g e g. any corporation established by or under any Central, State or Provincial Act or a Government company as defined i
  - `10_037_ Implementation Mechanism.pdf`, pages 50-50, section `i. any other matter which may be prescribed.`: Report Code: 037_GBP_IIT_PLG_S&R_01_Ver 1_Dec 2013 50 | P a g e h. setting aside any order of dismissal of any representation for default or any order passed by it ex parte; i. any
  - `11_Mission 8 - Environmental Knowledge (1).pdf`, pages 18-18, section `1997–2000 [ICPDR`: Table 4.3: Pesticide Consumption in Some 2005] Figure 4.4: Chlorophyll Concentrations in Locations during 1998 Table 4.4: Annual Mean 1997–2000 [ICPDR 10 Consumption in Some Danube
  - `11_Mission 8 - Environmental Knowledge (1).pdf`, pages 19-21, section `[ICPDR, 2005]`: 11 Figure 4.5: Number of Macro-Benthic Species In Front of the Danube Delta [ICPDR, 2005] For river basin management it should be clearly noted that the data types listed above are

### OCR_REQUIRED
- Count: **12** (2.17% of 554)
- Typical reason: The page has no usable extracted text, so the section cannot be evaluated from the current evidence.
- Recommended next action: Prioritize targeted OCR of the flagged pages after confirming that the page contains substantive content. Preserve the OCR result as a separate derived artifact.
- Representative examples:
  - `11_Mission 8 - Environmental Knowledge (1).pdf`, pages 2-6, section `Unidentified extracted structure`: i Preface In exercise of the powers conferred by sub-sections (1) and (3) of Section 3 of the Environment (Protection) Act, 1986 (29 of 1986), the Central Government constituted th
  - `11_Mission 8 - Environmental Knowledge.pdf`, pages 2-6, section `Unidentified extracted structure`: i Preface In exercise of the powers conferred by sub-sections (1) and (3) of Section 3 of the Environment (Protection) Act, 1986 (29 of 1986), the Central Government constituted th
  - `15_37_Stream Power Distribution Pattern for the Ganga River to Determine the Effects of River Energy and.pdf`, pages 1-3, section `Unidentified extracted structure`: Stream Power Distribution Pattern of the Ganga River and its GRBMP : Ganga River Basin Management Plan IIT Bombay IIT Delhi IIT Guwahati Indian Institutes of Technology Stream Powe
  - `15_66_Assessment of Domestic Pollution Load from Urban Agglomeration in Ganga Basin Ramganga Kali and Gomati Sub-Basin.pdf`, pages 1-3, section `Unidentified extracted structure`: Assessment of Domestic Pollution Load from Urban Agglomeration in Ganga Basin: Ramganga, Kali and Gomati Sub-Basin GRBMP: Ganga River Basin Management Plan by IIT Bombay IIT Delhi 
  - `35_70_Assessment of Potential Institutional Models for Sewage Treatment in Ganga Basin and the Way.pdf`, pages 20-23, section `LEGAL ARBITRATION CELL`: Report Code: 070_GBP_IIT_PLG_ANL_06_Ver 1_Dec 2014 20 | P a g e LEGAL ARBITRATION CELL ADMINISTRATION CELL RESEARCH AND TECHNICAL CELL Chairman – Expert in river basin Members- Sci

### AMBIGUOUS_RELEVANCE
- Count: **11** (1.99% of 554)
- Typical reason: After accounting for extraction quality, the available label and excerpt do not establish whether the content answers a likely Brain question.
- Recommended next action: Have a domain reviewer assess the section in document context and record a user-question or topic justification before approving or filtering it.
- Representative examples:
  - `15_012EQP.pdf`, pages 41-45, section `4. Environmental Impacts of Wastewater Reuse`: 41 | P a g e 4. Environmental Impacts of Wastewater Reuse The wastewater reuse is the most promising alternative to augment water supply and means of alleviating the anthropogenic 
  - `22_016SEC.pdf`, pages 29-30, section `7.1. Consumption of Fertilizers across Districts`: 29 | P a g e 7.1. Consumption of Fertilizers across Districts Figures 26a and 26b show the proportion of three main chemical fertilizers i.e. nitrogenous, phosphorous, and potasic 
  - `2_Mission 7_River Hazards Mgmt.pdf`, pages 8-8, section `5. Socio Economic and Cultural (SEC)`: vi 5. Socio Economic and Cultural (SEC) Lead: S P Singh, IIT Roorkee Members:Pushpa L Trivedi (IIT Bombay); Seema Sharma, V B Upadhyay (IIT Delhi); P M Prasad , Vinod Tare (IIT Kan
  - `32_035ENB.pdf`, pages 12-12, section `2.2. Periphyton`: 12 | P a g e 2.2. Periphyton Periphytons are the complex mixture of algae, detritus that are attached to ecosystems . In terms of group composition Chlorophyceae and Bac illariophy
  - `32_035ENB.pdf`, pages 14-14, section `2.5. Fish`: 14 | P a g e 2.5. Fish The river Ramganga is one of the prin the fish diversity. Mainly Corbett National Park is the home to many species of fresh water fish. The most celebrated o

### CONTEXT_DEPENDENT
- Count: **219** (39.53% of 554)
- Typical reason: The label or excerpt is too fragmentary to establish the section's meaning without surrounding pages.
- Recommended next action: Review the preceding and following sections together, preserving section boundaries and enough context for any eventual ingestion unit.
- Representative examples:
  - `10_019SEC.pdf`, pages 46-46, section `N P K`: 46 | P a g e Table A.16: Consumption of Fertilizers and Pesticides in West Bengal Year Total Fertilizer Consumption in tones Fertilizer Pesticide Consumption Ingredient Active N P 
  - `10_037_ Implementation Mechanism.pdf`, pages 27-27, section `i. a co-operative society registered under any law relating to cooperative`: Report Code: 037_GBP_IIT_PLG_S&R_01_Ver 1_Dec 2013 27 | P a g e g. any corporation established by or under any Central, State or Provincial Act or a Government company as defined i
  - `10_037_ Implementation Mechanism.pdf`, pages 50-50, section `i. any other matter which may be prescribed.`: Report Code: 037_GBP_IIT_PLG_S&R_01_Ver 1_Dec 2013 50 | P a g e h. setting aside any order of dismissal of any representation for default or any order passed by it ex parte; i. any
  - `11_Mission 8 - Environmental Knowledge (1).pdf`, pages 18-18, section `1997–2000 [ICPDR`: Table 4.3: Pesticide Consumption in Some 2005] Figure 4.4: Chlorophyll Concentrations in Locations during 1998 Table 4.4: Annual Mean 1997–2000 [ICPDR 10 Consumption in Some Danube
  - `11_Mission 8 - Environmental Knowledge (1).pdf`, pages 19-21, section `[ICPDR, 2005]`: 11 Figure 4.5: Number of Macro-Benthic Species In Front of the Danube Delta [ICPDR, 2005] For river basin management it should be clearly noted that the data types listed above are

### TECHNICAL_SCOPE_UNCLEAR
- Count: **165** (29.78% of 554)
- Typical reason: The source is technical or data-heavy, but the available evidence does not show whether it provides useful explanation or only specialist detail.
- Recommended next action: Ask a subject-matter reviewer to separate conceptual explanation from specialized calculations, raw inputs, and implementation detail.
- Representative examples:
  - `10_009PLG.pdf`, pages 15-15, section `4. Governance Grid`: Report Code: 009_GBP_IIT_PLG_ANL_03_Ver 1_Dec 2011 15 | P a g e economic and political benefits) which would accrue to the stakeholders or are expected by the stakeholder. Thus, in
  - `13_GRBMP - MPD.pdf`, pages 7-7, section `1. Environmental Quality and Pollution (EQP)`: GRBMP – January 2015: Main Plan Document v Composition of Thematic Groups 1. Environmental Quality and Pollution (EQP) Lead: Purnendu Bose, IIT Kanpur Members: Shyam R Asolekar, Su
  - `13_GRBMP - MPD.pdf`, pages 87-87, section `2. Disposal of industrial/ municipal solid wastes and sludge (from treatment`: GRBMP – January 2015: Main Plan Document 55 2. Disposal of industrial/ municipal solid wastes and sludge (from treatment of sewage or effluents)to be restricted every where except 
  - `14_61_Assessment of Domestic Pollution Load from Urban Agglomeration in Ganga Basin Rajasthan.pdf`, pages 10-14, section `2. Major Obstructi on and Abstractio n Projects on the`: 10 | P a g e 2. Major Obstructi on and Abstractio n Projects on the Tributaries of the River Ganga Executed in the State The natural flow regime in the river s and their tributarie
  - `15_Hydrological Flow Health Assessment of the River Ganga.pdf`, pages 20-21, section `25% - 75%, FHS =1`: 20 | P age ii) occasional increased flows in the high flow sea son were not detrimental to river health. Flow health adopts the inter-quartile range (25 th to 75 th percentile) for

### HISTORICAL_CONTEXT_UNCLEAR
- Count: **441** (79.6% of 554)
- Typical reason: The excerpt contains dated-looking findings, measurements, status, or trends without enough section-level evidence to establish the study/data period.
- Recommended next action: Confirm publication, study, and data periods from nearby pages and label retained content explicitly as historical.
- Representative examples:
  - `10_009PLG.pdf`, pages 15-15, section `4. Governance Grid`: Report Code: 009_GBP_IIT_PLG_ANL_03_Ver 1_Dec 2011 15 | P a g e economic and political benefits) which would accrue to the stakeholders or are expected by the stakeholder. Thus, in
  - `10_019SEC.pdf`, pages 17-18, section `4.1. Growth of Agriculture across Districts of West Bengal`: Report Code: 019_GBP_IIT_SEC_ANL_05_Ver 1_Dec 2011 17 | P a g e under consideration. However, production of all the crops, except jute and wheat continued accelerating in the post-
  - `10_019SEC.pdf`, pages 19-22, section `4.2. Crop Diversification in West Bengal`: Report Code: 019_GBP_IIT_SEC_ANL_05_Ver 1_Dec 2011 19 | P a g e It is important to note that despite marginal increase or decline in area under many of the crops in majority of the
  - `10_019SEC.pdf`, pages 23-28, section `5. Agricultural Inputs`: Report Code: 019_GBP_IIT_SEC_ANL_05_Ver 1_Dec 2011 23 | P a g e intensity in recent years may have been attributed to the paucity of water and other complementary inputs. Table 16:
  - `10_019SEC.pdf`, pages 47-47, section `I. Cultivators 19.53 17.95 1.58 0.25 0.21 0.09 19.79 18.17 1.62`: Report Code: 019_GBP_IIT_SEC_ANL_05_Ver 1_Dec 2011 47 | P a g e Table A.18: Total Main Workers and Its Percentage Distribution in West Bengal and India Category Rural Urban Total P

### GEOGRAPHIC_SCOPE_UNCLEAR
- Count: **0** (0.0% of 554)
- Typical reason: The available section evidence does not establish whether a claim is basin-wide, regional, city-level, or tied to a river stretch.
- Recommended next action: Confirm the study boundary from the title, methods, maps, and nearby text before allowing any basin-level interpretation.
- Representative examples:

### DUPLICATION_UNCLEAR
- Count: **0** (0.0% of 554)
- Typical reason: The available section evidence does not establish whether the content materially duplicates another source.
- Recommended next action: Compare the section with overlapping reports after its structure and scope are repaired; retain the stronger source while preserving provenance.
- Representative examples:

### TABLE_FIGURE_CONTEXT
- Count: **268** (48.38% of 554)
- Typical reason: The label or excerpt resembles a table, matrix, figure, formula, or value sequence whose meaning depends on missing captions, units, or surrounding explanation.
- Recommended next action: Review the original page with its caption, units, legend, and interpretation; do not ingest the isolated values.
- Representative examples:
  - `10_019SEC.pdf`, pages 23-28, section `5. Agricultural Inputs`: Report Code: 019_GBP_IIT_SEC_ANL_05_Ver 1_Dec 2011 23 | P a g e intensity in recent years may have been attributed to the paucity of water and other complementary inputs. Table 16:
  - `10_019SEC.pdf`, pages 47-47, section `I. Cultivators 19.53 17.95 1.58 0.25 0.21 0.09 19.79 18.17 1.62`: Report Code: 019_GBP_IIT_SEC_ANL_05_Ver 1_Dec 2011 47 | P a g e Table A.18: Total Main Workers and Its Percentage Distribution in West Bengal and India Category Rural Urban Total P
  - `10_019SEC.pdf`, pages 48-54, section `1. Rice 5176.2 5812.9 5435.3 5783.6 5782.9 5687.0 5719.8`: Report Code: 019_GBP_IIT_SEC_ANL_05_Ver 1_Dec 2011 48 | P a g e Table A. 20: Area under Principal Crops (Food Grains) in West Bengal (Area in '000 ha; Production in 000 tones) Sl. 
  - `10_037_ Implementation Mechanism.pdf`, pages 26-26, section `24) ͞Flood PlaiŶ͟ is the laŶd aƌea susĐeptiďle to iŶuŶdatioŶ ďǇ flood ǁateƌs;`: Report Code: 037_GBP_IIT_PLG_S&R_01_Ver 1_Dec 2013 26 | P a g e 24) ͞Flood PlaiŶ͟ is the laŶd aƌea susĐeptiďle to iŶuŶdatioŶ ďǇ flood ǁateƌs; 25) ͞Flood ‘outiŶg ChaŶŶel͟ is a ĐhaŶŶ
  - `10_037_ Implementation Mechanism.pdf`, pages 27-27, section `i. a co-operative society registered under any law relating to cooperative`: Report Code: 037_GBP_IIT_PLG_S&R_01_Ver 1_Dec 2013 27 | P a g e g. any corporation established by or under any Central, State or Provincial Act or a Government company as defined i

### OTHER
- Count: **0** (0.0% of 554)
- Typical reason: The evidence does not support a more specific reason category.
- Recommended next action: Perform targeted human review and record the missing evidence before deciding on a classification.
- Representative examples:

## Primary reasons

- TABLE_FIGURE_CONTEXT: **268** (48.38%)
- NOISY_EXTRACTION: **109** (19.68%)
- HISTORICAL_CONTEXT_UNCLEAR: **103** (18.59%)
- TECHNICAL_SCOPE_UNCLEAR: **51** (9.21%)
- OCR_REQUIRED: **12** (2.17%)
- AMBIGUOUS_RELEVANCE: **11** (1.99%)

## Prioritized review plan

### Priority 1: Prevent incorrect knowledge from entering the Brain
- Focus: OCR_REQUIRED, HISTORICAL_CONTEXT_UNCLEAR, GEOGRAPHIC_SCOPE_UNCLEAR, TABLE_FIGURE_CONTEXT
- Action: Resolve missing text, dates, study periods, geographic boundaries, units, captions, and interpretation before approving any section with factual claims or measurements.

### Priority 2: Prevent useful knowledge from being excluded
- Focus: AMBIGUOUS_RELEVANCE, TECHNICAL_SCOPE_UNCLEAR, CONTEXT_DEPENDENT
- Action: Repair headings and review adjacent pages with a domain reviewer; distinguish useful explanations from specialist detail before filtering.

### Priority 3: Repair structural and formatting issues
- Focus: NOISY_EXTRACTION
- Action: Apply deterministic heading cleanup and page-boundary validation, then return unresolved content to the priority 1 or 2 queues.

## Unsupported categories

These categories were not assigned because the current rationale/evidence does not support them:

- **GEOGRAPHIC_SCOPE_UNCLEAR**: No explicit supporting evidence in the recorded rationale or excerpt; do not infer at this stage.
- **DUPLICATION_UNCLEAR**: No explicit supporting evidence in the recorded rationale or excerpt; do not infer at this stage.
- **OTHER**: No explicit supporting evidence in the recorded rationale or excerpt; do not infer at this stage.

## Recommendation

Repair extraction structure first, then perform targeted OCR for the 11 OCR-affected documents. After those repairs, route factual/date/geography/table uncertainties through human review before resolving relevance or technical-scope questions. Do not begin chunking until the repaired records have complete section context and explicit temporal/geographic decisions.
