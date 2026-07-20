"""Research tracks, candidate profile ground-truth, and offline scoring."""
import math

# 8 research tracks: key -> (label, doc_focus, weighted keywords)
TRACKS = [
    {
        "key": "disorders",
        "label": "Psychiatric & transdiagnostic disorders",
        "doc_focus": "Frame clinical psychology training and transdiagnostic interest in emotion-cognition interaction.",
        "keywords": ["psychiatric", "psychopathology", "transdiagnostic", "depression", "anxiety",
                     "schizophrenia", "bipolar", "mood disorder", "clinical", "mental health", "rdoc"],
    },
    {
        "key": "eeg_fmri",
        "label": "EEG / fMRI & neuroimaging methods",
        "doc_focus": "Foreground hands-on EEG collection and fMRI exposure plus neuroimaging analysis skills.",
        "keywords": ["eeg", "fmri", "neuroimaging", "erp", "meg", "connectivity", "bold",
                     "electrophysiology", "cortical", "brain imaging", "mvpa"],
    },
    {
        "key": "attention",
        "label": "Attention & attentional control",
        "doc_focus": "Lead with the attentional-control-under-emotional-load dissertation and EyeLink work.",
        "keywords": ["attention", "attentional control", "selective attention", "distraction",
                     "cognitive control", "executive function", "inhibition", "eye movement", "gaze", "salience"],
    },
    {
        "key": "memory_dementia",
        "label": "Memory, aging & dementia",
        "doc_focus": "Highlight aging-cohort familiarity (UK Biobank) and memory / cognition interest.",
        "keywords": ["memory", "aging", "ageing", "dementia", "alzheimer", "mci", "cognitive decline",
                     "episodic memory", "working memory", "hippocampus", "older adults"],
    },
    {
        "key": "parkinsons",
        "label": "Parkinson's disease & neurodegeneration",
        "doc_focus": "Emphasise PPMI familiarity and interest in neurodegeneration biomarkers.",
        "keywords": ["parkinson", "neurodegeneration", "dopamine", "basal ganglia", "motor",
                     "ppmi", "substantia nigra", "movement disorder", "levodopa", "tremor"],
    },
    {
        "key": "impulse_reward",
        "label": "Impulse control, reward & substance use",
        "doc_focus": "Connect reward and impulse-control interest to reinforcement-learning modeling.",
        "keywords": ["impulsivity", "impulse control", "reward", "substance use", "addiction",
                     "craving", "risk taking", "reinforcement", "abcd", "delay discounting", "nucleus accumbens"],
    },
    {
        "key": "decision_making",
        "label": "Decision-making & computational modeling",
        "doc_focus": "Center the drift-diffusion / reinforcement-learning proposal and developing Python modeling.",
        "keywords": ["decision making", "decision-making", "computational modeling", "drift diffusion",
                     "ddm", "reinforcement learning", "value", "bayesian", "computational psychiatry",
                     "model fitting", "choice", "evidence accumulation"],
    },
    {
        "key": "multisensory_digital_health",
        "label": "Multisensory processing & digital health",
        "doc_focus": "Link multisensory integration and digital / wearable measurement interests.",
        "keywords": ["multisensory", "sensory integration", "digital health", "wearable", "mobile",
                     "ecological momentary", "audio-visual", "crossmodal", "mhealth", "smartphone"],
    },
]

TRACK_MAP = {t["key"]: t for t in TRACKS}

# Cross-cutting methods bonus keywords
METHODS = ["eye-tracking", "eyelink", "eeg", "fmri", "computational modeling", "drift diffusion",
           "reinforcement learning", "matlab", " r ", "spss", "python", "abcd", "uk biobank",
           "ppmi", "eye movement", "eye tracking", "modeling", "modelling"]

PROFILE_SUMMARY = (
    "Radhika Prakash Chhabria. MSc Cognitive Neuroscience (Durham University); "
    "MSc Clinical Psychology (Amity University). Dissertation on attentional control under "
    "emotional load using EyeLink 1000. Manuscript in preparation on decision-making predictors. "
    "Methods: EyeLink 1000 eye-tracking, EEG data collection, fMRI exposure, MATLAB, R, SPSS, "
    "Python (developing computational modeling). Familiar with ABCD, UK Biobank, PPMI datasets."
)

DEFAULT_PROFILE = {
    "id": "default",
    "name": "Radhika Prakash Chhabria",
    "summary": PROFILE_SUMMARY,
    "base_cv": """# Radhika Prakash Chhabria

## Education
- MSc Cognitive Neuroscience, Durham University
- MSc Clinical Psychology, Amity University

## Research Experience
- Dissertation: attentional control under emotional load, measured with EyeLink 1000 eye-tracking.
- Manuscript in preparation: decision-making predictors.

## Methods & Tools
- EyeLink 1000 eye-tracking
- EEG data collection
- fMRI exposure
- MATLAB, R, SPSS
- Python (developing - computational modeling)
- ABCD / UK Biobank / PPMI dataset familiarity
""",
    "base_proposal": """# Research Proposal (Core)

**Working title:** Computational signatures of attentional and value-based decision-making.

I propose to combine drift-diffusion modeling (DDM) and reinforcement learning (RL) frameworks
to characterise how attentional control shapes evidence accumulation under emotional load.
Building on my dissertation using EyeLink 1000 eye-tracking, I aim to link gaze dynamics to
latent decision parameters, using EEG and, where available, fMRI to constrain the models.
Large cohorts (ABCD, UK Biobank, PPMI) offer opportunities to test generalisability across
development, aging, and neurodegeneration.
""",
    "sample_email": """Subject: Prospective PhD student - attentional control & computational modeling

Dear Professor {LastName},

I am writing to express my strong interest in joining your lab. Your recent work on {topic}
resonates closely with my background in cognitive neuroscience and my dissertation on
attentional control under emotional load using EyeLink 1000 eye-tracking.

I hold an MSc in Cognitive Neuroscience from Durham University and an MSc in Clinical Psychology.
I have hands-on experience with EEG, exposure to fMRI, and I am developing computational modeling
skills (drift-diffusion and reinforcement learning) in Python, alongside MATLAB, R and SPSS.

I would welcome the chance to discuss whether you are taking PhD students for the coming cycle.
I have attached my CV, a statement of purpose, and a short research proposal tailored to your work.

Thank you for your time and consideration.

Warm regards,
Radhika Prakash Chhabria
""",
}


def _saturate(raw):
    return round(1.0 - math.exp(-raw / 4.0), 3)


def _text_of(prof):
    parts = [prof.get("focus", "") or ""]
    parts += prof.get("recent_papers", []) or []
    return " ".join(parts).lower()


def _rank_score(rank):
    if rank is None:
        return 0.50
    if rank <= 50:
        return 0.90
    if rank <= 100:
        return 0.75
    if rank <= 200:
        return 0.60
    return 0.50


def score_professor(prof):
    """Return the 4 sub-scores, overall score, and best track for a professor dict."""
    text = _text_of(prof)

    best_track, best_raw = None, -1.0
    for t in TRACKS:
        raw = 0.0
        for kw in t["keywords"]:
            if kw in text:
                raw += 1.5 if len(kw.split()) > 1 else 1.0
        if raw > best_raw:
            best_raw, best_track = raw, t["key"]
    score_research = _saturate(best_raw)

    methods_raw = sum(1.0 for m in METHODS if m in text)
    score_methods = _saturate(methods_raw)

    n_papers = len(prof.get("recent_papers", []) or [])
    score_lab = 0.85 if n_papers >= 2 else (0.60 if n_papers == 1 else 0.30)

    score_program = _rank_score(prof.get("rank"))

    content = score_research
    overall = min(1.0, content * 0.6 + score_methods * 0.4 + content * score_methods * 0.1)

    return {
        "best_track": best_track,
        "score_research": score_research,
        "score_methods": score_methods,
        "score_lab_activity": score_lab,
        "score_program": score_program,
        "match_score": round(overall, 3),
    }
