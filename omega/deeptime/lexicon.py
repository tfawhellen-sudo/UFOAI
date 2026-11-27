"""Deep-time lexicon: the 33 physical descriptors of the craft taxonomy (omega/taxonomy/features.py,
reused unchanged so modern and pre-modern codings are identical) plus three new families:

  FRAMES    what the witness/scribe compared the thing to (the cultural analogy)
  ENTITY    occupants, landings with beings, physical effects on people
  VOICE     compiler/UFO jargon ('object', 'craft', 'UFO', 'mysterious'). This is not a descriptor of
            the phenomenon. It measures how much of a text is the modern compiler talking.

Every pattern is a regex over lower-cased text, English + French (Obsequens and GEIPAN are French).
"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'taxonomy'))
from features import code_text as code_physical, FEATURES as PHYS_ALL, DUR_F  # noqa: E402

PHYS = [f for f in PHYS_ALL if f not in DUR_F]           # durations are too sparse pre-1900

FRAMES = [
    # pre-industrial analogies
    ('f_celestial', r"\b(stars?|moons?|suns?|planets?|venus|[ée]toiles?|lunes?|soleils?|astres?)\b"),
    ('f_comet',     r"\b(comets?|com[eè]tes?|bearded star|hairy star|tailed star)\b"),
    ('f_martial',   r"\b(shields?|swords?|spears?|lances?|javelins?|arrows?|arms|armies|army|armou?r\w*|soldiers|warriors|"
                    r"battles?|troops|cavalry|horsemen|boucliers?|[ée]p[ée]es?|armes|arm[ée]es?|soldats|combat\w*|bataille\w*|javelots?)\b"),
    ('f_religious', r"\b(cross|crosses|crucifix\w*|angels?|demons?|devils?|saints?|virgin|christ|god|gods|heaven\w*|divine|"
                    r"miracul\w*|miracles?|omens?|prodig\w*|portents?|croix|anges?|d[ée]mons?|diable|dieux?|ciel en feu)\b"),
    ('f_creature',  r"\b(dragons?|serpents?|snakes?|beasts?|birds?|eagles?|oiseaux?|aigles?)\b"),
    ('f_maritime',  r"\b(ships?|boats?|vessels?|sails?|fleet|cloud ?ships?|navires?|vaisseaux?|bateaux?|barques?|flotte)\b"),
    ('f_torch',     r"\b(torch\w*|firebrands?|beam of fire|fiery beam|torches?|flambeaux?|poutres?)\b"),
    ('f_wheel',     r"\b(wheels?|chariots?|roues?|chars?)\b"),
    # industrial / modern analogies, with the year the technology was in public view (see technology.py)
    ('f_balloon',   r"\b(balloons?|montgolfi\w*|ballons?)\b"),
    ('f_airship',   r"\b(air[- ]?ships?|dirigibles?|zeppelins?|aerial (machine|vessel|navigator|ship)s?|flying machines?|propellers?|searchlights?)\b"),
    ('f_aircraft',  r"\b(air ?planes?|aeroplanes?|aircraft|planes?|jets?|biplanes?|monoplanes?|helicopters?|avions?)\b"),
    ('f_rocket',    r"\b(rockets?|missiles?|fus[ée]es?)\b"),
    ('f_saucer',    r"\b(saucers?|soucoupes?|flying dis[ck]s?)\b"),
    ('f_space',     r"\b(space ?craft|space ?ships?|mother ?ships?|aliens?|extra-?terrestrial\w*|e\.t\.|martians?|vaisseau spatial|extraterrestres?)\b"),
    ('f_satellite', r"\b(satellites?|starlink|space station|iss)\b"),
    ('f_drone',     r"\b(drones?|quad ?copters?|uavs?)\b"),
    ('f_lantern',   r"\b(lanterns?|lanternes?)\b"),
]
ENTITY = [
    ('e_occupant',  r"\b(beings?|occupants?|entit(y|ies)|humanoids?|creatures?|pilots?|crew|little men|figures?|"
                    r"dwarfs?|giants?|men (came|got|stepped|emerged)|man (came|got|stepped|emerged)|[eê]tres?|occupants?)\b"),
    ('e_effect',    r"\b(heat|scorch\w*|burn(ed|t|s)? (the|his|her|their)|smell\w*|odou?r\w*|sulph?ur\w*|stench|paraly\w*|"
                    r"odeur\w*|chaleur|soufre)\b"),
]
VOICE = [
    ('v_object',    r"\b(objects?|craft|ufos?|unidentified|uap|ovnis?|objets?)\b"),
    ('v_mystery',   r"\b(mysterious\w*|enigmatic|unexplained|inexplicab\w*|anomal\w*|strange|peculiar|unusual|myst[ée]rieu\w*|[ée]trange\w*)\b"),
]
TECH_FRAMES = ['f_balloon', 'f_airship', 'f_aircraft', 'f_rocket', 'f_saucer', 'f_space', 'f_satellite', 'f_drone', 'f_lantern']
OLD_FRAMES = ['f_celestial', 'f_comet', 'f_martial', 'f_religious', 'f_creature', 'f_maritime', 'f_torch', 'f_wheel']
FRAME_F = [f for f, _ in FRAMES]
ENTITY_F = [f for f, _ in ENTITY]
VOICE_F = [f for f, _ in VOICE]
_RX = [(f, re.compile(p, re.I)) for f, p in FRAMES + ENTITY + VOICE]
ALL = PHYS + FRAME_F + ENTITY_F + VOICE_F

# compiler explanations: sentences that carry the compiler's own identification ("possibly a meteor",
# "[IN REALITY: Halley's comet]"). They mark the report as mundane AND are removed before coding,
# so the explanation's words ('meteor', 'comet') do not leak into the descriptors (same rule as GEIPAN).
MUNDANE = re.compile(
    r"(in reality|probabl\w*|possibl\w*|likely|perhaps|maybe|suggest\w*|interpret\w*|explained|identified|consistent with|"
    r"could (have )?be(en)?|might (have )?be(en)?|may (have )?be(en)?|thought to be|believed to be|appears to (have been|be)|"
    r"astronomers?|scientists?)\W+(\w+\W+){0,6}?"
    r"(a |an |the )?(meteors?|meteorites?|bolides?|comets?|aurora\w*|northern lights|halos?|parhel\w*|paraselen\w*|mock suns?|"
    r"sun ?dogs?|ball lightning|lightning|supernova\w*|nova|venus|jupiter|mars|eclipse|zodiacal|noctilucent|mirage|"
    r"atmospheric|optical|natural|meteorological|ignis fatuus|will-o'?-the-wisp|marsh gas|fireball)", re.I)
MUNDANE_FR = re.compile(r"(en r[ée]alit[ée]|il s'agi(ssai)?t|probablement|sans doute)\W+(\w+\W+){0,6}?"
                        r"(com[eè]te|m[ée]t[ée]or\w*|bolide|aurore|halo|parh[ée]lie)", re.I)


def split_explanation(text):
    """Return (witness_text, mundane_flag). Sentences carrying a compiler identification are dropped."""
    sents = re.split(r'(?<=[.!?;\]])\s+|\[|\]', text or '')
    keep, flag = [], False
    for s in sents:
        if MUNDANE.search(s) or MUNDANE_FR.search(s):
            flag = True
            continue
        keep.append(s)
    return ' '.join(keep), flag


def code(text):
    """All deep-time features for one text (physical descriptors use the taxonomy lexicon v2)."""
    t = (text or '').lower()
    out = set(f for f in code_physical(t) if f not in DUR_F)
    out |= {f for f, rx in _RX if rx.search(t)}
    return out
