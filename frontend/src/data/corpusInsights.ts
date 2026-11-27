// Verified precomputed insights from the DA team's evaluation artifacts
// (data/eval/review_nlp_metrics.json, review_summaries.json, demand_analysis.json, email_metrics.json).
// These are descriptive corpus artifacts — never live DB queries or causal claims.

export interface TopicPattern {
  topic: string;
  labelIt: string;
  prevalencePooled: number;
  prevalenceLago: number;
  prevalenceMontagna: number;
  mappedDimension: string | null;
  deltaPooled: number | null;
  note: string;
}

export const NLP_CORPUS_INSIGHTS = {
  totalReviews: 1638,
  lagoCount: 762,
  montagnaCount: 876,
  models: {
    sentiment: "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual",
    topics: "facebook/bart-large-mnli (zero-shot NLI)",
  },
  sentimentCounts: {
    pooled: { positive: 809, neutral: 477, negative: 352 },
    lago: { positive: 289, neutral: 277, negative: 196 },
    montagna: { positive: 520, neutral: 200, negative: 156 },
  },
  overallSpearman: {
    pooled: 0.5517,
    lago: 0.6266,
    montagna: 0.437,
  },
  topics: [
    {
      topic: "noise",
      labelIt: "Rumore / Insonorizzazione",
      prevalencePooled: 0.1783,
      prevalenceLago: 0.1654,
      prevalenceMontagna: 0.1895,
      mappedDimension: "Qualità del sonno",
      deltaPooled: -0.696,
      note: "Segnale negativo più netto: chi cita il rumore ha un voto sonno di -0,70 punti (3,60 vs 4,29).",
    },
    {
      topic: "value",
      labelIt: "Rapporto qualità-prezzo",
      prevalencePooled: 0.7912,
      prevalenceLago: 0.7231,
      prevalenceMontagna: 0.8505,
      mappedDimension: "Valore",
      deltaPooled: 0.805,
      note: "Prevalenza alta ma calibrazione più debole (F1 probe 0,857); menzioni spesso positive.",
    },
    {
      topic: "staff",
      labelIt: "Staff e accoglienza",
      prevalencePooled: 0.6862,
      prevalenceLago: 0.7283,
      prevalenceMontagna: 0.6495,
      mappedDimension: null,
      deltaPooled: null,
      note: "Molto citato al Lago (72,8%); nessuna dimensione dedicata nei voti TripAdvisor.",
    },
    {
      topic: "location",
      labelIt: "Posizione",
      prevalencePooled: 0.6813,
      prevalenceLago: 0.6273,
      prevalenceMontagna: 0.7283,
      mappedDimension: "Posizione",
      deltaPooled: 0.07,
      note: "Correlazione debole con il sentiment complessivo (ρ 0,2126): citata sia in voti alti che bassi.",
    },
    {
      topic: "cleanliness",
      labelIt: "Pulizia",
      prevalencePooled: 0.4664,
      prevalenceLago: 0.3714,
      prevalenceMontagna: 0.5491,
      mappedDimension: "Pulizia",
      deltaPooled: 0.172,
      note: "Più presente in Montagna (54,9%) rispetto al Lago (37,1%).",
    },
    {
      topic: "breakfast",
      labelIt: "Colazione",
      prevalencePooled: 0.2265,
      prevalenceLago: 0.1549,
      prevalenceMontagna: 0.2888,
      mappedDimension: null,
      deltaPooled: null,
      note: "Menzionata quasi il doppio in Montagna (28,9%) rispetto al Lago (15,5%).",
    },
  ] satisfies TopicPattern[],
};

export interface ExtractiveSummary {
  property_id: 1 | 2;
  month: string;
  n_reviews: number;
  sentences: Array<{
    text: string;
    review_id: number;
    post_date: string;
    score: number;
  }>;
}

export const EXTRACTIVE_SUMMARIES_2012: ExtractiveSummary[] = [
  {
    property_id: 1,
    month: "2012-01",
    n_reviews: 36,
    sentences: [
      { text: "This hotel is perfectly located and has brilliant staff.", review_id: 29, post_date: "2012-01-29", score: 0.9709 },
      { text: "I stayed there for 4 days and they did everything possible to make our stay plesant and well.", review_id: 29, post_date: "2012-01-29", score: 0.9609 },
    ],
  },
  {
    property_id: 1,
    month: "2012-04",
    n_reviews: 79,
    sentences: [
      { text: "This hotel is stunning.", review_id: 144, post_date: "2012-04-02", score: 0.9793 },
      { text: "My daughters and I stayed 5 nights.", review_id: 167, post_date: "2012-04-12", score: 0.9713 },
    ],
  },
  {
    property_id: 1,
    month: "2012-06",
    n_reviews: 64,
    sentences: [
      { text: "Fancy feeling like a queen for a week?", review_id: 300, post_date: "2012-06-11", score: 0.9862 },
      { text: "My wonderful partner took me to this fabulous hotel for my birthday.", review_id: 300, post_date: "2012-06-11", score: 0.9762 },
    ],
  },
  {
    property_id: 1,
    month: "2012-08",
    n_reviews: 73,
    sentences: [
      { text: "Our stay with our family here was amazing.", review_id: 460, post_date: "2012-08-21", score: 0.9761 },
      { text: "Loved the hotel and the staff were wonderful.", review_id: 457, post_date: "2012-08-20", score: 0.967 },
    ],
  },
  {
    property_id: 1,
    month: "2012-09",
    n_reviews: 88,
    sentences: [
      { text: "We booked one bedroom suite (num A10) that could easy accommodates 4 people, the room is huge.", review_id: 501, post_date: "2012-09-06", score: 0.9701 },
      { text: "The Hotel is a true piece of history, wonderful to explore and enjoy.", review_id: 558, post_date: "2012-09-24", score: 0.9696 },
    ],
  },
  {
    property_id: 1,
    month: "2012-10",
    n_reviews: 56,
    sentences: [
      { text: "Great place, great location, good value.", review_id: 578, post_date: "2012-10-05", score: 0.9784 },
      { text: "The staff was superb and the beds were the most comfortable I have ever slept on.", review_id: 646, post_date: "2012-11-05", score: 0.971 },
    ],
  },
  {
    property_id: 1,
    month: "2012-12",
    n_reviews: 51,
    sentences: [
      { text: "Got a great offer to that hotel and didn´t think to long about taking that chance!", review_id: 755, post_date: "2012-12-16", score: 0.9755 },
      { text: "Everything was excellent Eat at the restaurant food/service great.", review_id: 728, post_date: "2012-12-06", score: 0.9727 },
    ],
  },
  {
    property_id: 2,
    month: "2012-01",
    n_reviews: 40,
    sentences: [
      { text: "This hotel was not only impeccably clean, but the staff was so helpful and courteous!", review_id: 778, post_date: "2012-01-15", score: 0.9762 },
    ],
  },
  {
    property_id: 2,
    month: "2012-04",
    n_reviews: 72,
    sentences: [
      { text: "It´s a modern, very clean and well situated hotel.", review_id: 979, post_date: "2012-04-14", score: 0.9826 },
      { text: "We loved our stay here.", review_id: 951, post_date: "2012-04-03", score: 0.9816 },
    ],
  },
  {
    property_id: 2,
    month: "2012-05",
    n_reviews: 73,
    sentences: [
      { text: "A small room with one of the most comfortable beds I have slept in.", review_id: 1074, post_date: "2012-05-25", score: 0.9728 },
    ],
  },
  {
    property_id: 2,
    month: "2012-08",
    n_reviews: 97,
    sentences: [
      { text: "We really enjoyed our two night stay.", review_id: 1295, post_date: "2012-08-15", score: 0.9728 },
    ],
  },
  {
    property_id: 2,
    month: "2012-09",
    n_reviews: 76,
    sentences: [
      { text: "Very modern and great and convenient location.", review_id: 1403, post_date: "2012-09-24", score: 0.9798 },
      { text: "Awesome and quiet room, awesome view!", review_id: 1380, post_date: "2012-09-17", score: 0.9778 },
    ],
  },
  {
    property_id: 2,
    month: "2012-10",
    n_reviews: 68,
    sentences: [
      { text: "Great Service, Great Location, Great Price. Clean and free 24hr coffee. The breakfast muffins are awesome!", review_id: 1485, post_date: "2012-10-29", score: 0.9717 },
      { text: "All business travel and its been great each time.", review_id: 1445, post_date: "2012-10-12", score: 0.9716 },
    ],
  },
  {
    property_id: 2,
    month: "2012-12",
    n_reviews: 50,
    sentences: [
      { text: "Brilliant value for money, with brilliant views from the 21st floor!", review_id: 1638, post_date: "2012-12-19", score: 0.9718 },
      { text: "The location is very central.", review_id: 1625, post_date: "2012-12-14", score: 0.9652 },
    ],
  },
];

export const LEAD_TIME_RISK_BUCKETS = [
  { bucket: "0–7g", bookings: 18304, cancelRate: 0.0843, avgLead: 2.3 },
  { bucket: "8–30g", bookings: 16340, cancelRate: 0.2537, avgLead: 17.8 },
  { bucket: "31–90g", bookings: 22744, cancelRate: 0.3201, avgLead: 56.8 },
  { bucket: "91–180g", bookings: 18243, cancelRate: 0.3498, avgLead: 131.7 },
  { bucket: ">180g", bookings: 11765, cancelRate: 0.3974, avgLead: 251.1 },
];

export const EMAIL_CLASSIFIER_BENCHMARK = {
  categoryMacroF1: 0.9901,
  urgencyMacroF1: 0.9659,
  syntheticTotal: 800,
};
