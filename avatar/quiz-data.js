(function (root, factory) {
  const questions = factory();
  if (typeof module === 'object' && module.exports) module.exports = questions;
  if (root) root.GangaQuizQuestions = questions;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  return [
    {
      id: 'ganga-headstreams',
      category: 'Ganga Knowledge',
      question: 'How many main Himalayan headstreams are included in the GRBMP definition of the River Ganga?',
      options: [
        { id: 'a', text: 'Four' },
        { id: 'b', text: 'Five' },
        { id: 'c', text: 'Six' },
        { id: 'd', text: 'Eight' }
      ],
      correctOptionId: 'c',
      explanation: 'The GRBMP Extended Summary names six main headstreams, from Alaknanda to Bhagirathi.',
      source: {
        title: 'GRBMP — January 2015: Extended Summary',
        reference: 'Section 2.3, “Defining River Ganga”'
      }
    },
    {
      id: 'ganga-middle-segment',
      category: 'Ganga Knowledge',
      question: 'Which stretch is identified as the Middle Ganga segment in the GRBMP definition?',
      options: [
        { id: 'a', text: 'Gaumukh to Rishikesh' },
        { id: 'b', text: 'Rishikesh to Varanasi' },
        { id: 'c', text: 'Varanasi to Ganga Sagar' },
        { id: 'd', text: 'Alaknanda to Bhagirathi confluence' }
      ],
      correctOptionId: 'b',
      explanation: 'The definition places the main stem downstream from Rishikesh to Varanasi in the Middle Ganga segment.',
      source: {
        title: 'GRBMP — January 2015: Extended Summary',
        reference: 'Section 2.3, “Defining River Ganga”'
      }
    },
    {
      id: 'ganga-lower-segment',
      category: 'Ganga Knowledge',
      question: 'In the GRBMP definition, where does the Lower Ganga segment extend?',
      options: [
        { id: 'a', text: 'Rishikesh to Prayagraj' },
        { id: 'b', text: 'Haridwar to Varanasi' },
        { id: 'c', text: 'Varanasi to Ganga Sagar' },
        { id: 'd', text: 'Gaumukh to Rishikesh' }
      ],
      correctOptionId: 'c',
      explanation: 'The GRBMP defines the final stretch from Varanasi to Ganga Sagar as the Lower Ganga segment.',
      source: {
        title: 'GRBMP — January 2015: Extended Summary',
        reference: 'Section 2.3, “Defining River Ganga”'
      }
    },
    {
      id: 'nmcg-expansion',
      category: 'Namami Gange',
      question: 'In the Vision Ganga document, what does the abbreviation NMCG stand for?',
      options: [
        { id: 'a', text: 'National Mission for Clean Ganga' },
        { id: 'b', text: 'National Monitoring Council for Groundwater' },
        { id: 'c', text: 'National Management Centre for Glaciers' },
        { id: 'd', text: 'National Ministry for Conservation and Governance' }
      ],
      correctOptionId: 'a',
      explanation: 'The document’s heading spells out NMCG as National Mission for Clean Ganga.',
      source: {
        title: 'Vision Ganga by cGanga and NMCG (2018)',
        reference: 'Page 2, “National Mission for Clean Ganga (NMCG)”'
      }
    },
    {
      id: 'nmcg-role-2018',
      category: 'Namami Gange',
      question: 'What role does the 2018 Vision Ganga document describe for NMCG?',
      options: [
        { id: 'a', text: 'The implementation wing of the National Ganga Council' },
        { id: 'b', text: 'The scientific laboratory for every Ganga water sample' },
        { id: 'c', text: 'The authority that operates all municipal treatment plants' },
        { id: 'd', text: 'The organization that manages Himalayan glaciers' }
      ],
      correctOptionId: 'a',
      explanation: 'This is the role stated in that 2018 document; it is a historical source description, not a claim about current organizational arrangements.',
      source: {
        title: 'Vision Ganga by cGanga and NMCG (2018)',
        reference: 'Page 2, “National Mission for Clean Ganga (NMCG)”'
      }
    },
    {
      id: 'pollution-town-waste',
      category: 'River Pollution',
      question: 'Which group does the GRBMP Mission 2 summary identify as point sources of pollution?',
      options: [
        { id: 'a', text: 'Liquid and solid waste from towns, villages, and industries' },
        { id: 'b', text: 'Only naturally occurring sediment from mountain streams' },
        { id: 'c', text: 'Only rainfall over forested areas' },
        { id: 'd', text: 'Only seasonal changes in river temperature' }
      ],
      correctOptionId: 'a',
      explanation: 'Mission 2 identifies waste from towns, villages, and industries as point sources in the basin.',
      source: {
        title: 'GRBMP — January 2015: Mission 2 — Nirmal Dhara',
        reference: 'Summary, pollution sources'
      }
    },
    {
      id: 'pollution-agricultural-runoff',
      category: 'River Pollution',
      question: 'According to GRBMP Mission 2, how can agricultural fertilizers and pesticides reach the river system?',
      options: [
        { id: 'a', text: 'Through irrigation return flows or storm runoff' },
        { id: 'b', text: 'Only through glacier melt' },
        { id: 'c', text: 'Only through municipal drinking-water pipes' },
        { id: 'd', text: 'By becoming part of natural river sediments without runoff' }
      ],
      correctOptionId: 'a',
      explanation: 'The report describes fertilizers and pesticides leaching into irrigation return flows or storm runoff.',
      source: {
        title: 'GRBMP — January 2015: Mission 2 — Nirmal Dhara',
        reference: 'Summary, non-point pollution sources'
      }
    },
    {
      id: 'water-quality-nirmal-dhara',
      category: 'Water Quality',
      question: 'What is the stated objective of Mission Nirmal Dhara?',
      options: [
        { id: 'a', text: 'To ensure the Ganga River System is free from human-caused pollution' },
        { id: 'b', text: 'To increase the number of riverbank roads' },
        { id: 'c', text: 'To divert all tributaries into one channel' },
        { id: 'd', text: 'To measure only the depth of the river' }
      ],
      correctOptionId: 'a',
      explanation: 'Mission 2 states that Nirmal Dhara aims for flow in the Ganga River System to be bereft of manmade pollution.',
      source: {
        title: 'GRBMP — January 2015: Mission 2 — Nirmal Dhara',
        reference: 'Summary, Mission Nirmal Dhara objective'
      }
    },
    {
      id: 'water-quality-waste-types',
      category: 'Water Quality',
      question: 'Which kinds of waste does the GRBMP Mission 2 summary say affect Ganga River System water quality?',
      options: [
        { id: 'a', text: 'Domestic, industrial, and agricultural wastes' },
        { id: 'b', text: 'Only household drinking water' },
        { id: 'c', text: 'Only natural spring water' },
        { id: 'd', text: 'Only waste from recreational boats' }
      ],
      correctOptionId: 'a',
      explanation: 'The summary names wastes from domestic, industrial, and agricultural sources as affecting water quality.',
      source: {
        title: 'GRBMP — January 2015: Mission 2 — Nirmal Dhara',
        reference: 'Summary, pollution and water quality'
      }
    },
    {
      id: 'ganga-aviral-dhara',
      category: 'Ganga Knowledge',
      question: 'What does the GRBMP Mission 1 objective say should flow continuously and adequately through the Ganga river network?',
      options: [
        { id: 'a', text: 'Water along with sediments, nutrients, and other natural constituents' },
        { id: 'b', text: 'Treated sewage from every town' },
        { id: 'c', text: 'Only water released during monsoon' },
        { id: 'd', text: 'Industrial effluent after dilution' }
      ],
      correctOptionId: 'a',
      explanation: 'Mission 1, Aviral Dhara, describes continuous and adequate flow of water together with sediments, nutrients, and other natural constituents.',
      source: {
        title: 'GRBMP — January 2015: Mission 1 — Aviral Dhara',
        reference: 'Section 2, “Objective”'
      }
    }
  ];
});
