"""Google Gemini AI integration for text and image generation via LiteLLM proxy.

This module provides a client for interacting with Google Gemini API
through LiteLLM proxy to generate stylized greeting card text and festive images.

Features:
- 5 text styles (ode, future, haiku, newspaper, standup)
- 15 image styles (knitted, magic_realism, pixel_art, vintage_russian,
  soviet_poster, hyperrealism, digital_3d, fantasy, comic_book, watercolor,
  cyberpunk, paper_cutout, pop_art, lego, linocut)
- Text generation via gemini-2.5-flash
- Image generation via gemini-3.1-flash-image-preview
- Automatic retry on transient errors
- Comprehensive error handling
- Structured logging
"""

import json
import logging
import base64
import random
import re
from dataclasses import dataclass
from typing import Optional, Any, Dict, List, Tuple

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Named constants for configuration
HTTP_TIMEOUT_SECONDS = 120.0
TEXT_MAX_TOKENS = 8192
IMAGE_MAX_TOKENS = 4096
ANALYSIS_MAX_TOKENS = 1024
TEXT_TEMPERATURE = 0.8
ANALYSIS_TEMPERATURE = 0.3  # Lower temperature for more consistent analysis
MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 2
RETRY_MAX_WAIT = 10
PHOTOCARD_PRIMARY_TEMPERATURE = 0.05
PHOTOCARD_RETRY_TEMPERATURE = 0.5

PHOTOCARD_BRAND_PALETTE = {
    "main": ["#FFFFFF", "#B9CDFF", "#1F2A3A", "#0A0A0A"],
    "additional": ["#F15A5A", "#F8C44D", "#58B8D9", "#7CD4A5", "#FFB8DE"],
}

_PHOTOCARD_STYLE_VARIATIONS = {
    "bento_grid": {
        "composition": "connected central cluster occupying 70-80% across 3x3 or 4x3 modules",
    },
    "minimalist_corporate_line_art": {
        "composition": "single dominant centered motif occupying 70-80% with generous breathing room",
    },
    "quirky_hand_drawn_flat": {
        "composition": "single rounded central figure occupying 70-80% with lively doodle accents",
    },
}

_PHOTOCARD_STYLE_PALETTES = {
    "bento_grid": [
        (["#FFFFFF", "#B9CDFF", "#E8ECFF"], ["#F15A5A", "#F8C44D"]),
        (["#FFFFFF", "#DCE8FF", "#B9CDFF"], ["#58B8D9", "#7CD4A5"]),
    ],
    "minimalist_corporate_line_art": [
        (["#FFFFFF", "#0A0A0A"], ["#B9CDFF"]),
        (["#F7F8FA", "#111111"], ["#B9CDFF", "#58B8D9"]),
    ],
    "quirky_hand_drawn_flat": [
        (["#FFFFFF", "#B9CDFF", "#EFF4FF"], ["#F15A5A", "#F8C44D"]),
        (["#FFFFFF", "#DDE8FF", "#DDF7FF"], ["#7CD4A5", "#FFB8DE"]),
    ],
}

_PHOTOCARD_AGENT_OVERRIDES: dict[str, str] | None = None


def _get_photocard_agent_overrides(style: str) -> str:
    """Load optional photocard prompt overrides and return merged override block."""
    global _PHOTOCARD_AGENT_OVERRIDES
    if _PHOTOCARD_AGENT_OVERRIDES is None:
        try:
            from .photocard_prompt_agent_overrides import PHOTOCARD_AGENT_STYLE_OVERRIDES

            if isinstance(PHOTOCARD_AGENT_STYLE_OVERRIDES, dict):
                _PHOTOCARD_AGENT_OVERRIDES = {
                    key: str(value)
                    for key, value in PHOTOCARD_AGENT_STYLE_OVERRIDES.items()
                    if isinstance(key, str) and isinstance(value, str)
                }
            else:
                _PHOTOCARD_AGENT_OVERRIDES = {}
        except Exception:
            _PHOTOCARD_AGENT_OVERRIDES = {}

    if not _PHOTOCARD_AGENT_OVERRIDES:
        return ""

    global_override = _PHOTOCARD_AGENT_OVERRIDES.get("_global", "").strip()
    style_override = _PHOTOCARD_AGENT_OVERRIDES.get(style, "").strip()
    if global_override and style_override:
        return f"{global_override}\n\n{style_override}"
    return global_override or style_override


def _get_photocard_variation(style: str) -> dict[str, str]:
    """Return a stable style variation hint set for photocard generation."""
    if style in _PHOTOCARD_STYLE_VARIATIONS:
        return _PHOTOCARD_STYLE_VARIATIONS[style]
    return {"composition": "dominant central motif occupies roughly 70-80% of the tile"}


def _sample_photocard_palette(style: str) -> Tuple[List[str], List[str]]:
    """Return style-tuned color palette for photocard generation."""
    variations = _PHOTOCARD_STYLE_PALETTES.get(style, [])
    if variations:
        primary_colors, accent_colors = random.choice(variations)
        return list(primary_colors), list(accent_colors)
    return PHOTOCARD_BRAND_PALETTE["main"][:3], PHOTOCARD_BRAND_PALETTE["additional"][:2]

from .exceptions import (
    GeminiTextGenerationError,
    GeminiImageGenerationError,
    GeminiRateLimitError,
    GeminiConfigError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Visual Concept Analysis
# ============================================================================


@dataclass
class VisualConcept:
    """Result of analyzing gratitude text for visual representation.

    This structured data is used to generate images that represent
    the meaning of gratitude rather than literal text.

    Extended with Nano Banana principles for better image generation:
    - composition: camera angle and shot type for compositional control
    - lighting: specific light source and quality for mood
    """

    core_theme: str  # Main theme: teamwork, innovation, leadership, support, etc.
    visual_metaphor: str  # Concrete visual description (Subject + Action + Environment)
    key_elements: List[str]  # 5 specific elements to include in the image
    mood: str  # Emotional atmosphere
    composition: str = "medium shot, eye level"  # Camera angle and framing
    lighting: str = "soft balanced daylight"  # Light source and quality


# ============================================================================
# Diverse Fallback Concepts Pool
# 15 concepts organized by metaphor category for maximum diversity
# Each category is mapped to specific image styles for deterministic fallback
# ============================================================================

FALLBACK_VISUAL_CONCEPTS = [
    # Category 1: CELESTIAL - for ethereal styles
    VisualConcept(
        core_theme="appreciation",
        visual_metaphor="A vintage brass orrery with crystalline planetary spheres catching the light of a late autumn sunset, turning gears reflected in warm polished metal",
        key_elements=["brass orrery", "planetary spheres", "golden highlights", "detailed gears", "sunset glow"],
        mood="wonder and cosmic harmony",
        composition="low angle, medium shot with shallow DoF",
        lighting="warm sunset glow from behind, cool ambient fill",
    ),
    # Category 2: BOTANICAL - for organic, natural styles
    VisualConcept(
        core_theme="gratitude",
        visual_metaphor="A Victorian glass terrarium filled with resilient flowers - translucent blossoms and metallic petals growing from mineral-rich soil, condensation beading on the curved glass walls",
        key_elements=["glass terrarium", "metallic petals", "unusual flowers", "condensation droplets", "curved walls"],
        mood="delicate nurturing beauty",
        composition="close-up, eye level, layered depth",
        lighting="soft diffused daylight through glass, subtle internal glow",
    ),
    # Category 3: MECHANICAL/CLOCKWORK - for precision styles
    VisualConcept(
        core_theme="innovation",
        visual_metaphor="An antique astronomical clock on a glass stand, its exposed golden mechanisms turning as moonlight catches each precisely crafted gear and celestial indicator",
        key_elements=["astronomical clock", "golden gears", "moonlight", "celestial dials", "precision mechanics"],
        mood="precision and timeless ingenuity",
        composition="medium shot, slight dutch angle",
        lighting="cool moonlight from above, warm brass reflections",
    ),
    # Category 4: ARCHITECTURAL - for grand, structural styles
    VisualConcept(
        core_theme="support",
        visual_metaphor="A magnificent stone viaduct with graceful arches spanning a deep valley, evening fog clinging to weathered stones while a distant train creates a plume of steam against the twilight sky",
        key_elements=["stone viaduct", "graceful arches", "ancient engineering", "steam plume", "twilight sky"],
        mood="enduring strength and connection",
        composition="wide establishing shot, eye level",
        lighting="golden twilight with blue shadows, warm steam accent",
    ),
    # Category 5: CRAFTSMANSHIP - for artisanal styles
    VisualConcept(
        core_theme="excellence",
        visual_metaphor="A master glassblower's workshop with a half-formed ornament glowing orange on the end of a blowpipe, light spilling through large windows, tools arranged with reverent precision",
        key_elements=["glowing glass", "blowpipe", "ornament", "studio windows", "artisan tools"],
        mood="focused mastery and creation",
        composition="medium shot, warm-cool contrast",
        lighting="orange furnace glow vs cool window light",
    ),
    # Category 6: NAVIGATION/JOURNEY - for adventure styles
    VisualConcept(
        core_theme="mentorship",
        visual_metaphor="An ancient mariner's sextant and star charts spread on a captain's desk, the brass instrument catching lamplight while distant constellations glow past a compass-windowed cabin",
        key_elements=["brass sextant", "star charts", "captain's desk", "maritime compass", "constellations"],
        mood="guidance through unknown waters",
        composition="close-up with deep background",
        lighting="warm oil lamp glow, cool starlight accent",
    ),
    # Category 7: MUSICAL - for harmonious, elegant styles
    VisualConcept(
        core_theme="teamwork",
        visual_metaphor="A string quartet's instruments arranged in a glass pavilion at dusk - violin, viola, cello, and bass forming a perfect constellation, sheet music pages turning slowly in still air",
        key_elements=["string instruments", "pavilion", "floating sheet music", "dusk light", "perfect arrangement"],
        mood="harmony held in a perfect moment",
        composition="wide shot, slightly elevated",
        lighting="golden dusk rim light, blue ambient shadows",
    ),
    # Category 8: ELEMENTAL - for dramatic, dynamic styles
    VisualConcept(
        core_theme="perseverance",
        visual_metaphor="A cascade of autumn leaves transforming into glowing seed-like motes, the moment of change suspended in time above a forest floor patterned in warm and cool tones",
        key_elements=["autumn leaves", "transforming motes", "forest floor", "suspended motion", "dual palette"],
        mood="beautiful metamorphosis",
        composition="medium shot, eye level, magical realism",
        lighting="soft diffused light, subtle sparkle on transitions",
    ),
    # Category 9: SYMBOLIC OBJECTS - for meaningful, intimate styles
    VisualConcept(
        core_theme="dedication",
        visual_metaphor="A perfectly balanced antique scale with polished glass cubes on one plate and golden leaves on the other, both sides in strict equilibrium on a marble pedestal",
        key_elements=["antique scale", "glass cubes", "golden leaves", "perfect balance", "marble pedestal"],
        mood="harmony through balance",
        composition="close-up, centered, symmetrical",
        lighting="soft even lighting, subtle highlights on metal",
    ),
    # Category 10: NATURE TRANSFORMATIONS - for organic change styles
    VisualConcept(
        core_theme="creativity",
        visual_metaphor="A suspended waterfall in reverse: reflected water strands glittering in motion, prismatic light dancing through the formations as morning sun hits each sculptural curve",
        key_elements=["suspended waterfalls", "crystal strands", "prismatic light", "morning sun", "architectural form"],
        mood="nature's sculptural artistry",
        composition="low angle looking up, dramatic",
        lighting="backlit morning sun, rainbow refractions",
    ),
    # Category 11: TEXTILE/CRAFT - specifically for knitted style
    VisualConcept(
        core_theme="warmth",
        visual_metaphor="A cozy reading nook with hand-knitted blankets draped over an antique armchair, a warm mug of tea on the side table, late light falling softly through an open window",
        key_elements=["knitted blankets", "antique armchair", "warm mug", "open window", "soft light"],
        mood="comfort and cherished moments",
        composition="medium shot, inviting warmth",
        lighting="warm interior glow, cool blue from window",
    ),
    # Category 12: RETRO/NOSTALGIC - for vintage styles
    VisualConcept(
        core_theme="celebration",
        visual_metaphor="A vintage gramophone with its brass horn angled toward an open window, vinyl records stacked nearby, musical notes materializing as bright arcs of light in the room",
        key_elements=["brass gramophone", "vinyl records", "light arcs", "open window", "musical traces"],
        mood="nostalgia and timeless joy",
        composition="medium shot, warm nostalgic tones",
        lighting="soft afternoon light, warm brass highlights",
    ),
    # Category 13: TECHNOLOGICAL/FUTURISTIC - for modern styles
    VisualConcept(
        core_theme="innovation",
        visual_metaphor="A holographic geometry projection floating above a sleek crystalline surface, its geometric patterns constantly shifting while particle glints drift around it, blending digital and natural rhythms",
        key_elements=["holographic geometry", "crystalline surface", "shifting patterns", "drifting particles", "digital-natural blend"],
        mood="future meets tradition",
        composition="close-up, centered, high-tech aesthetic",
        lighting="cool blue holographic glow, soft ambient",
    ),
    # Category 14: MINIATURE/DIORAMA - for cute/playful styles
    VisualConcept(
        core_theme="joy",
        visual_metaphor="A miniature craft village inside a glass orb, tiny houses with warm windows and a reflective central pool, all viewed from an intimate macro perspective as if we've shrunk down",
        key_elements=["glass orb", "miniature village", "warm windows", "reflective pool", "macro perspective"],
        mood="whimsical enchantment",
        composition="macro close-up, inside looking out",
        lighting="warm village glow, soft neutral haze",
    ),
    # Category 15: PRINTMAKING/GRAPHIC - for bold graphic styles
    VisualConcept(
        core_theme="strength",
        visual_metaphor="A majestic stag-shaped sculpture standing proud on a granite ridge, antlers silhouetted against a full moon while distant pines frame deep negative space",
        key_elements=["stag sculpture", "antler silhouette", "full moon", "granite ridge", "pine forest"],
        mood="noble strength and solitude",
        composition="wide shot, high contrast, graphic",
        lighting="strong moonlight backlight, deep shadows",
    ),
]

# Style-to-fallback mapping for deterministic diversity
# Each image style gets a specific fallback concept from a different category
STYLE_FALLBACK_MAPPING = {
    "knitted": 10,        # TEXTILE/CRAFT - cozy reading nook
    "magic_realism": 7,   # ELEMENTAL - leaves transformation
    "pixel_art": 13,      # MINIATURE/DIORAMA - craft village scene
    "vintage_russian": 11, # RETRO/NOSTALGIC - gramophone
    "soviet_poster": 14,  # PRINTMAKING/GRAPHIC - sculptural stag motif
    "hyperrealism": 9,    # NATURE TRANSFORMATIONS - sculptural water forms
    "digital_3d": 13,     # MINIATURE/DIORAMA - miniature village
    "fantasy": 0,         # CELESTIAL - brass orrery
    "comic_book": 7,      # ELEMENTAL - leaves transformation
    "watercolor": 1,      # BOTANICAL - terrarium flowers
    "cyberpunk": 12,      # TECHNOLOGICAL - holographic geometry
    "paper_cutout": 3,    # ARCHITECTURAL - viaduct
    "pop_art": 8,         # SYMBOLIC OBJECTS - balanced scale
    "lego": 13,           # MINIATURE/DIORAMA - miniature village
    "linocut": 14,        # PRINTMAKING/GRAPHIC - symbolic stag motif
}


def get_fallback_visual_concept() -> VisualConcept:
    """Get a random fallback visual concept for diversity."""
    return random.choice(FALLBACK_VISUAL_CONCEPTS)


def get_fallback_visual_concept_for_style(style: str) -> VisualConcept:
    """Get a deterministic fallback concept based on image style.
    
    This ensures that even in fallback scenarios, each image style
    receives a different visual concept from an appropriate category.
    
    Args:
        style: Image style code (e.g., 'knitted', 'pixel_art')
        
    Returns:
        VisualConcept appropriate for the given style
    """
    index = STYLE_FALLBACK_MAPPING.get(style, random.randint(0, len(FALLBACK_VISUAL_CONCEPTS) - 1))
    return FALLBACK_VISUAL_CONCEPTS[index]


def get_diverse_fallback_concepts(count: int = 4) -> List[VisualConcept]:
    """Get a set of diverse fallback concepts ensuring no duplicates.
    
    Uses stratified sampling to ensure concepts come from different
    metaphor categories.
    
    Args:
        count: Number of diverse concepts needed
        
    Returns:
        List of VisualConcept objects from different categories
    """
    if count >= len(FALLBACK_VISUAL_CONCEPTS):
        return FALLBACK_VISUAL_CONCEPTS[:count]
    
    # Use stratified sampling - pick from evenly spaced indices
    step = len(FALLBACK_VISUAL_CONCEPTS) // count
    indices = [i * step for i in range(count)]
    return [FALLBACK_VISUAL_CONCEPTS[i] for i in indices]


# Legacy constant for backwards compatibility
FALLBACK_VISUAL_CONCEPT = FALLBACK_VISUAL_CONCEPTS[0]


# ============================================================================
# Visual Concept Analysis Prompt
# Designed with Nano Banana principles for diverse, high-quality image generation
# ============================================================================

# Categories of visual metaphors for diversity (model picks from different semantic fields)
METAPHOR_CATEGORIES = """
METAPHOR CATEGORIES (choose ONE category, then create a specific scene):

1. NATURE TRANSFORMATIONS - seeds awakening, hidden springs, suspended water lines, aurora-like light fields
2. MECHANICAL/CLOCKWORK - gears interlocking, compass pointing north, vintage clock mechanisms, brass instruments
3. ARCHITECTURAL - bridges connecting cliffs, arched doorways with light, spiral staircases, observatory towers
4. CRAFTSMANSHIP - hands shaping pottery (silhouette), weaving on a loom, blacksmith's anvil, origami birds
5. NAVIGATION/JOURNEY - maps with routes, ships in harbor, mountain paths, footprints on ancient stone leading forward
6. MUSICAL - orchestral instruments in harmony, music notes as light trails, grand piano in reflective spaces
7. BOTANICAL - greenhouse with rare flowers, bonsai tree, root systems in deep soil, living architecture
8. CELESTIAL - constellation patterns, moon phases, northern lights, planets aligning
9. ELEMENTAL - fire and water meeting, wind carrying petals and dust, crystal formations
10. SYMBOLIC OBJECTS - hourglasses, scales in balance, keys and locks, vintage books with bookmarks
"""

# Prompt for analyzing gratitude and extracting visual concepts
VISUAL_ANALYSIS_PROMPT = """You are an expert visual concept designer specializing in corporate greeting cards.
Your task: transform gratitude into a UNIQUE, CREATIVE visual metaphor for image generation.

═══════════════════════════════════════════════════════════════════════════════
INPUT DATA / ВХОДНЫЕ ДАННЫЕ:
═══════════════════════════════════════════════════════════════════════════════
Кому (Recipient): {recipient}
За что (Reason for gratitude): {reason}
Послание (Personal message): {message}

IMPORTANT: The "За что" (reason) field is CRITICAL - it describes the specific achievement
or contribution being celebrated. Use it to inform the emotional theme and visual metaphor.

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK: Create a visual concept following this process:
═══════════════════════════════════════════════════════════════════════════════

STEP 1 - IDENTIFY CORE THEME:
Analyze the gratitude and select ONE primary theme:
• teamwork (collaboration, unity, joint effort)
• innovation (new ideas, breakthroughs, creative solutions)
• leadership (guidance, vision, inspiring others)
• support (helping, being there, reliability)
• perseverance (overcoming obstacles, determination)
• creativity (artistic thinking, original approaches)
• dedication (commitment, going above and beyond)
• problem_solving (finding solutions, analytical thinking)
• mentorship (teaching, sharing knowledge)
• excellence (high quality, outstanding results)

STEP 2 - SELECT METAPHOR CATEGORY:
""" + METAPHOR_CATEGORIES + """

STEP 3 - CREATE SPECIFIC SCENE:
Design a concrete, filmable scene with:
• SUBJECT: The main object/element (be specific: "brass astrolabe" not "instrument")
• ACTION: What is happening (dynamic verb: "rotating", "unfolding", "emerging")
• ENVIRONMENT: Where it takes place (specific setting with clear, identifiable details)
• LIGHTING: Light source and quality (e.g., "warm golden hour backlight", "cool moonlight from above")

STEP 4 - DEFINE COMPOSITION:
Specify camera framing:
• ANGLE: low angle / eye level / bird's eye / dutch angle
• SHOT: extreme close-up / close-up / medium / wide / establishing
• DEPTH: shallow DoF with bokeh / deep focus / layered foreground-background

═══════════════════════════════════════════════════════════════════════════════
CRITICAL CONSTRAINTS:
═══════════════════════════════════════════════════════════════════════════════
✗ NO text, words, letters, numbers, or written symbols
✗ NO realistic human faces (silhouettes and hands from behind are OK)
✗ NO cliché light sources: lanterns, lighthouses, candles, torches, glowing orbs
✗ NO generic "magical glow" - be specific about light source
✓ YES strong symbolic imagery when it naturally supports the narrative
✓ YES specific, concrete objects (not abstract concepts)
✓ YES dynamic elements suggesting movement or transformation

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT (JSON only, no markdown, no explanation):
═══════════════════════════════════════════════════════════════════════════════
{{"core_theme": "theme_name", "visual_metaphor": "Complete scene description in one paragraph: subject + action + environment + lighting", "key_elements": ["element1", "element2", "element3", "element4", "element5"], "mood": "emotional atmosphere", "composition": "camera angle and shot type", "lighting": "specific light source and quality"}}

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES (notice the diversity in metaphor categories):
═══════════════════════════════════════════════════════════════════════════════

Input: reason="внедрение новой CRM системы", message="Спасибо за инициативу и упорство"
Category: MECHANICAL/CLOCKWORK
Output: {{"core_theme": "innovation", "visual_metaphor": "A complex brass orrery mechanism emerging from the first light of dawn, polished gears beginning to turn as a focused beam catches the metal, tiny crystalline particles suspended mid-air around rotating planetary spheres", "key_elements": ["brass orrery", "interlocking gears", "planetary spheres", "dawn light", "sunrise reflections"], "mood": "awakening and precision", "composition": "low angle close-up, shallow depth of field", "lighting": "warm sunrise from the right, golden hour quality"}}

Input: reason="поддержку команды в сложный квартал", message="Ты был надёжной опорой"
Category: ARCHITECTURAL
Output: {{"core_theme": "support", "visual_metaphor": "An ancient stone bridge arching over a deep river gorge, its weathered pillars standing firm while morning fog rolls between them, a warm amber glow visible from windows of a small cabin beyond", "key_elements": ["stone arch bridge", "river gorge", "weathered pillars", "distant cabin", "warm interior glow"], "mood": "steadfast reliability and safe passage", "composition": "wide establishing shot, eye level", "lighting": "overcast soft daylight with warm cabin accent"}}

Input: reason="креативные идеи для маркетинга", message="Твои идеи всегда вдохновляют"
Category: BOTANICAL
Output: {{"core_theme": "creativity", "visual_metaphor": "A vintage glass greenhouse in a wild botanical courtyard, inside which impossible flowers bloom in impossible colors, all tended by gardening tools left mid-work", "key_elements": ["Victorian greenhouse", "crystal-like roses", "impossible tulips", "vintage watering can", "lush microclimate"], "mood": "wonder and cultivation", "composition": "medium shot through glass, layered depth", "lighting": "soft diffused daylight filtering through glass panels"}}

Input: reason="обучение новых сотрудников", message="Благодаря тебе команда стала сильнее"
Category: NAVIGATION/JOURNEY
Output: {{"core_theme": "mentorship", "visual_metaphor": "An antique brass compass resting on a weathered leather map case atop a mountain summit cairn, the needle pointing toward distant peaks glowing in dusk light, with a deliberate path visible below", "key_elements": ["brass compass", "leather map case", "stone cairn", "mountain peaks", "leading path"], "mood": "guidance and achievement", "composition": "close-up with deep background, slight low angle", "lighting": "alpenglow from distant peaks, crisp evening shadows"}}

Input: reason="успешное закрытие года", message="Отличная работа всей команды"
Category: MUSICAL
Output: {{"core_theme": "teamwork", "visual_metaphor": "A grand piano stands in a forest clearing, its lid open to reveal keys in soft focus, while sheet music pages circle in controlled motion like a synchronized rhythm", "key_elements": ["grand piano", "floating sheet music", "forest clearing", "multiple viewpoints", "synchronized motion"], "mood": "harmony and celebration", "composition": "wide shot, slightly elevated angle", "lighting": "soft morning light with subtle rim accents on piano edges"}}

═══════════════════════════════════════════════════════════════════════════════
Now analyze the input above and respond with JSON only:"""


# ============================================================================
# Multi-Agent Ultrathink Batch Visual Concept Generation
# Generates N diverse concepts in a single pass using chain-of-thought reasoning
# Each concept uses a DIFFERENT metaphor category for maximum thematic diversity
# ============================================================================

BATCH_VISUAL_ANALYSIS_PROMPT = """You are an elite multi-agent visual concept system. Your task is to generate {count} COMPLETELY DIFFERENT visual concepts that all represent the same core gratitude, but through ENTIRELY DIFFERENT visual metaphors.

═══════════════════════════════════════════════════════════════════════════════
INPUT DATA / ВХОДНЫЕ ДАННЫЕ
═══════════════════════════════════════════════════════════════════════════════
Кому (Recipient): {recipient}
За что (Reason for gratitude): {reason}
Послание (Personal message): {message}

IMPORTANT: The "За что" (reason) field is CRITICAL - it describes the specific achievement
or contribution being celebrated. Use it to inform the emotional theme and visual metaphor.

═══════════════════════════════════════════════════════════════════════════════
MULTI-AGENT REASONING PROCESS (think through each step)
═══════════════════════════════════════════════════════════════════════════════

<AGENT_1: THEME_ANALYST>
First, identify the CORE emotional theme from the gratitude:
- teamwork, innovation, leadership, support, perseverance, creativity,
- dedication, problem_solving, mentorship, excellence, celebration, growth
Select ONE theme that best captures the essence.
</AGENT_1>

<AGENT_2: CATEGORY_DISTRIBUTOR>
Assign EXACTLY ONE unique metaphor category to each of the {count} concepts.
You MUST use {count} DIFFERENT categories from this list (no repeats!):

1. CELESTIAL - orreries, astrolabes, star charts, moon phases, constellations
2. BOTANICAL - terrariums, greenhouses, indoor gardens, impossible flowers, bonsai
3. MECHANICAL - clockwork, gears, astronomical clocks, precision instruments
4. ARCHITECTURAL - viaducts, arched bridges, towers, spiral staircases, doorways
5. CRAFTSMANSHIP - glassblowing, pottery, weaving, metalwork, woodcarving
6. NAVIGATION - sextants, compasses, maps, ships, mountain paths, cairns
7. MUSICAL - string instruments, pianos, sheet music, orchestras, gramophones
8. ELEMENTAL - transformation moments, fire-ice meeting, crystal formations
9. SYMBOLIC - scales, hourglasses, keys, vintage books, compasses
10. NATURE - cascading waterways, ancient trees, migrating birds, seasons changing

Distribution for {count} concepts:
{category_assignments}
</AGENT_2>

<AGENT_3: UNIQUENESS_VALIDATOR>
Before generating, verify:
✗ NO two concepts share similar subjects (e.g., no "compass" AND "sextant" - both navigation)
✗ NO overlapping key elements between concepts
✗ NO repeated lighting setups - each must have distinct lighting
✓ Each concept must feel like it belongs to a completely different world
</AGENT_3>

<AGENT_4: SCENE_GENERATORS - one per concept>
For EACH assigned category, create a unique scene with:
• SUBJECT: Specific named object ("Victorian brass orrery" not "instrument")
• ACTION: Dynamic state ("emerging", "transforming", "awakening")
• ENVIRONMENT: Unique setting with distinct characteristics
• LIGHTING: Specific, different light source for each (no repeats!)
• COMPOSITION: Varied camera angles (mix of: low angle, eye level, bird's eye, close-up, wide)
</AGENT_4>

<AGENT_5: COHERENCE_CHECKER>
Verify all concepts:
✓ Share the SAME core_theme (connecting thread)
✓ Have DIFFERENT visual_metaphor subjects
✓ Have DIFFERENT moods within the same emotional family
✓ Would each make a beautiful, distinct greeting card image
</AGENT_5>

═══════════════════════════════════════════════════════════════════════════════
CRITICAL CONSTRAINTS (apply to ALL concepts)
═══════════════════════════════════════════════════════════════════════════════
✗ NO text, words, letters, numbers, or written symbols in any concept
✗ NO realistic human faces (silhouettes and hands are OK)
✗ NO lanterns, lighthouses, candles, torches, or generic glowing orbs
✗ NO concept should share more than 1 key element with another concept
✓ YES culturally neutral celebratory imagery naturally integrated
✓ YES specific, concrete, visually distinct objects
✓ YES each concept should work beautifully in its own artistic style

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT (JSON array, no markdown, no explanation)
═══════════════════════════════════════════════════════════════════════════════
[
  {{"core_theme": "shared_theme", "visual_metaphor": "Scene 1 description", "key_elements": ["el1", "el2", "el3", "el4", "el5"], "mood": "mood1", "composition": "composition1", "lighting": "lighting1"}},
  {{"core_theme": "shared_theme", "visual_metaphor": "Scene 2 description", "key_elements": ["el1", "el2", "el3", "el4", "el5"], "mood": "mood2", "composition": "composition2", "lighting": "lighting2"}},
  ... ({count} total, each from a DIFFERENT category)
]

═══════════════════════════════════════════════════════════════════════════════
EXAMPLE: 4 diverse concepts for "teamwork on a project"
═══════════════════════════════════════════════════════════════════════════════
[
  {{"core_theme": "teamwork", "visual_metaphor": "A Victorian brass orrery with four interlocking planetary rings, each sphere a different precious metal, rotating in synchronized dance above a velvet display", "key_elements": ["brass orrery", "planetary rings", "precious metal spheres", "velvet base", "synchronized motion"], "mood": "precision harmony", "composition": "low angle, medium shot, shallow DoF", "lighting": "warm spotlight from above, cool ambient fill"}},
  {{"core_theme": "teamwork", "visual_metaphor": "Four distinct instruments - violin, cello, flute, and harp - arranged in a glass pavilion, each casting musical note-shaped shadows that interweave on the tiled floor", "key_elements": ["four instruments", "music pavilion", "interweaving shadows", "musical note shapes", "evening light"], "mood": "harmonic unity", "composition": "wide shot, slightly elevated, symmetrical", "lighting": "golden sidelight, smooth long shadows"}},
  {{"core_theme": "teamwork", "visual_metaphor": "A greenhouse atrium where four different vine species have grown together to form a living arch, their leaves touching at the peak above a reflective pool", "key_elements": ["living vine arch", "four plant species", "reflective pool", "greenhouse atrium", "intertwined growth"], "mood": "organic collaboration", "composition": "medium shot, eye level, through the arch", "lighting": "soft diffused daylight, green leaf glow"}},
  {{"core_theme": "teamwork", "visual_metaphor": "An ancient stone bridge with four distinctive arches, each built in a slightly different masonry style yet forming one unified span across a mountain stream", "key_elements": ["four-arch bridge", "varied masonry", "mountain stream", "architectural unity", "unified structure"], "mood": "diverse strength", "composition": "wide establishing shot, eye level, centered", "lighting": "overcast soft light with specular highlights"}}
]

═══════════════════════════════════════════════════════════════════════════════
Now generate {count} MAXIMALLY DIVERSE concepts. Output JSON array only:"""


def _build_category_assignments(count: int) -> str:
    """Build category assignment instructions based on count."""
    if count == 4:
        return """Concept 1: CELESTIAL or MECHANICAL (precision/cosmic)
Concept 2: MUSICAL or CRAFTSMANSHIP (artistry/creation)
Concept 3: BOTANICAL or NATURE (organic/growth)
Concept 4: ARCHITECTURAL or NAVIGATION (structure/journey)"""
    elif count == 3:
        return """Concept 1: CELESTIAL, MECHANICAL, or SYMBOLIC
Concept 2: MUSICAL, CRAFTSMANSHIP, or BOTANICAL
Concept 3: ARCHITECTURAL, NATURE, or NAVIGATION"""
    elif count == 2:
        return """Concept 1: CELESTIAL, MECHANICAL, MUSICAL, or CRAFTSMANSHIP
Concept 2: BOTANICAL, ARCHITECTURAL, NATURE, or NAVIGATION"""
    else:
        # For any other count, distribute categories evenly
        categories = [
            "CELESTIAL", "BOTANICAL", "MECHANICAL", "ARCHITECTURAL",
            "CRAFTSMANSHIP", "NAVIGATION", "MUSICAL", "ELEMENTAL",
            "SYMBOLIC", "NATURE"
        ]
        assignments = []
        for i in range(count):
            cat_idx = i % len(categories)
            assignments.append(f"Concept {i+1}: {categories[cat_idx]}")
        return "\n".join(assignments)


# ============================================================================
# Text style prompts in Russian for corporate greeting cards
# Best practices: concise, persona-first, few-shot examples, structured input
TEXT_STYLE_PROMPTS = {
    "ode": """<persona>Ты — придворный поэт с чувством юмора</persona>

<task>Преврати поздравление в торжественную оду (400-600 символов)</task>

<input>
Кому: {recipient}
От: {sender}
За что: {reason}
Текст: {message}
</input>

<example>
Input: "Спасибо за помощь с отчётом"
Output: "О, великий {recipient}! В час, когда тьма квартальных отчётов сгущалась над нашими головами, ты явился подобно лучу света средь бури! Цифры, что казались хаосом, под твоей рукой сложились в симфонию, и дедлайн был повержен!"
</example>

Пиши возвышенно, с лёгкой иронией. Упомяни {recipient}. Выведи только текст оды.""",

    "future": """<persona>Ты — историк из 2030 года</persona>

<task>Напиши ретроспективную заметку о событии декабря 2025 (350-500 символов)</task>

<input>
Герой: {recipient}
Автор благодарности: {sender}
Достижение: {reason}
Контекст: {message}
</input>

<example>
Input: "внедрение новой CRM"
Output: "2030 год. Листая архивы, понимаем: когда {recipient} в декабре 2025-го запустил новую CRM, это казалось рядовым апдейтом. Никто не знал, что именно этот момент станет точкой отсчёта новой эры продаж..."
</example>

Стиль: "мы тогда не понимали масштаб". Выведи только текст.""",

    "haiku": """<persona>Ты — мастер хайку</persona>

<task>Напиши 2-3 хайку по мотивам поздравления</task>

<input>
Адресат: {recipient}
От: {sender}
Повод: {reason}
Слова: {message}
</input>

<rules>
- Образы с атмосферой (свет, вода, воздух)
- Имя {recipient} минимум один раз
- Пустая строка между хайку
</rules>

<example>
Input: "за поддержку в трудный момент"
Output:
Лёгкий туман
по утру стережёт окно —
Всё стало проще

Словно миг в тишине
Мы чувствуем твою опору
В нём теплота
</example>

Выведи только хайку, без пояснений.""",

    "newspaper": """<persona>Ты — журналист корпоративной газеты</persona>

<task>Напиши новостную заметку с заголовком (400-600 символов)</task>

<input>
Герой статьи: {recipient}
Источник: {sender}
Событие: {reason}
Цитата: {message}
</input>

<format>
**Заголовок: цепляющий, с именем героя**
Текст заметки в журналистском стиле
</format>

<example>
Input: "спас проект от срыва"
Output:
**{recipient}: как один человек спас квартальный проект**
Редакция выяснила подробности. Когда до дедлайна оставались часы, а ситуация казалась безнадёжной, именно {recipient} взял ответственность на себя...
</example>

Тон тёплый, но профессиональный. Выведи заголовок и текст.""",

    "standup": """<persona>Ты — добрый комик на корпоративе</persona>

<task>Напиши тёплый стендап-монолог (350-500 символов)</task>

<input>
Кому: {recipient}
От кого: {sender}
За что: {reason}
Послание: {message}
</input>

<rules>
- Обращение на "ты"
- Шутки над ситуацией, НЕ над человеком
- Финал — искренняя благодарность
</rules>

<example>
Input: "за терпение с правками"
Output: "{recipient}, слушай, я тут посчитал — ты героически пережил 47 версий моих правок. Сорок. Семь. И ни разу не закатил глаза! Ну, может закатил, но я не видел, а значит не считается. Серьёзно, твоё терпение — это суперсила уровня Marvel. Спасибо тебе огромное!"
</example>

Выведи только монолог.""",
}


# ============================================================================
# Image style prompts for Gemini - using VisualConcept structured data
# Redesigned with Nano Banana principles:
# - Natural language descriptions (not keyword soup)
# - Structured: Subject + Action + Environment + Lighting
# - Composition control via {composition} placeholder
# - Lighting control via {lighting} placeholder
# - Clear negative constraints
# ============================================================================

IMAGE_STYLE_PROMPTS = {
    "knitted": """Generate a cozy greeting card image in knitted wool texture style.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE scene that expresses the theme of "{core_theme}" through the knitted wool aesthetic.
You must REINTERPRET the inspiration into something that works perfectly for knitted texture -
think of warm handcrafted objects, meaningful scenes, or artisanal moments that would look beautiful as knitted art.

STYLE SPECIFICATIONS:
Render the entire scene as if made from knitted wool fabric. Every object should have the texture of hand-knitted yarn with visible stitches, fuzzy fibers, and yarn loops. Think of a premium knit accessory or textile craft come to life.

TECHNICAL REQUIREMENTS:
- Macro photography quality, 8K resolution
- Realistic wool texture with individual yarn fibers visible
- Shallow depth of field with soft bokeh on edges
- Warm, cozy color palette: deep red, cream white, forest green, touches of gold thread
- Soft directional lighting creating gentle shadows in the knit texture

FORBIDDEN: No text, letters, numbers, words, or any written symbols woven into the fabric.""",

    "magic_realism": """Generate a dreamlike magic realism greeting card illustration.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE scene that expresses "{core_theme}" through magic realism.
Reimagine the inspiration as something surreal - objects behaving impossibly, dreamlike physics,
the ordinary made extraordinary. Choose subjects that work for this mystical, cinematic style.

STYLE SPECIFICATIONS:
Reality bends subtly. Objects have photorealistic textures but behave impossibly - things float, scale shifts, physics is dreamlike. The style of Gabriel García Márquez visualized.

TECHNICAL REQUIREMENTS:
- Cinematic quality, film grain optional
- Hyperdetailed textures on key objects
- Deep atmospheric perspective with layered depth
- Color palette: midnight blues, bioluminescent cyans, warm golds, deep violet shadows
- Volumetric lighting with visible light rays

FORBIDDEN: No text or letters. No realistic human faces (silhouettes acceptable). No generic "magical sparkles" - magic should feel grounded.""",

    "pixel_art": """Generate a nostalgic 16-bit pixel art greeting card scene.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE pixel art scene expressing "{core_theme}" as a classic video game would.
Transform the inspiration into charming 16-bit sprites - think of what objects and scenes
work best as pixel art: treasure chests, crystals, retro consoles, city corners, transport hubs.

STYLE SPECIFICATIONS:
Authentic Super Nintendo / Sega Genesis era pixel art. Clean pixel grid with deliberate placement. Isometric or side-scroller framing. The charm of retro gaming.

TECHNICAL REQUIREMENTS:
- Limited 32-color palette, carefully chosen
- Crisp pixels with NO anti-aliasing or smoothing
- Dithering patterns for gradients and shadows
- Vibrant saturated colors: festive reds, greens, ice blues
- Decorative pixel border frame optional

FORBIDDEN: No text, UI elements, health bars, score displays, or any alphanumeric characters.""",

    "vintage_russian": """Generate a vintage Russian postcard illustration circa 1905-1915.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE scene expressing "{core_theme}" as a turn-of-century Russian artist would paint it.
Reimagine the inspiration using period-appropriate imagery: troikas, samovars, birch forests,
city streets, tram lines, ornate decorations, folk motifs.

STYLE SPECIFICATIONS:
Pre-revolutionary Russian postcard aesthetic. Art Nouveau influence with flowing organic lines. Hand-drawn feel with delicate linework.

TECHNICAL REQUIREMENTS:
- Aged paper texture with visible grain
- Subtle scratches, foxing spots, slight color fading
- Ornate decorative border in Art Nouveau style
- Color palette: muted pastels, sepia undertones, faded gold leaf, dusty rose, soft spruce green
- Soft, diffused lighting as if painted from memory

FORBIDDEN: No text, Cyrillic letters, dates, typography, or any written elements.""",

    "soviet_poster": """Generate a Soviet Constructivist propaganda-style greeting card poster.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE graphic composition expressing "{core_theme}" through bold Soviet aesthetics.
Transform the inspiration into geometric shapes, dynamic diagonals, heroic symbolism.
Think: industrial progress, collective achievement, bold graphic forms.

STYLE SPECIFICATIONS:
Bold Soviet Constructivism meets Rodchenko and El Lissitzky. Geometric abstraction, dynamic diagonals, flat shapes. Heroic optimism through pure graphic design.

TECHNICAL REQUIREMENTS:
- Flat vector illustration style
- Strong geometric shapes, clean hard edges
- Dynamic diagonal composition, strong perspective
- Color palette: dominant red (Kumach), teal/cyan, cream, black, occasional gold
- Grainy lithograph print texture overlay
- High contrast, minimal gradients

FORBIDDEN: No text, slogans, Cyrillic lettering, or any typographic elements. Pure graphic symbolism.""",

    "hyperrealism": """Generate a hyperrealistic still life photograph for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE photorealistic still life expressing "{core_theme}" through tangible objects.
Choose subjects that photograph beautifully with extreme detail: glass objects,
metallic surfaces, glass, crystal-like textures, natural textures, studio-ready materials.

STYLE SPECIFICATIONS:
National Geographic or high-end commercial photography quality. Every surface tells a story through texture. Detail captured with scientific precision.

TECHNICAL REQUIREMENTS:
- 8K resolution, extreme sharpness on focal point
- Macro lens perspective with creamy bokeh background
- Obsessive detail: fine textures, micro particles, material textures
- Color palette: icy whites, cool blues, silver, with one warm accent (gold or red)
- Caustic light patterns, realistic reflections, subsurface scattering

FORBIDDEN: No text, labels, engravings, or watermarks. No human faces. Objects and textures only.""",

    "digital_3d": """Generate a cute 3D isometric render for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE isometric 3D scene expressing "{core_theme}" with toylike charm.
Transform the inspiration into cute, chunky 3D objects: miniature buildings, studio props,
stylized nature, whimsical machines - things that look delightful as clay or plastic models.

STYLE SPECIFICATIONS:
Modern 3D digital art (Blender/Cinema4D style). Claymorphism aesthetic with soft, tactile materials. Product visualization meets toy-like charm.

TECHNICAL REQUIREMENTS:
- Clean isometric or slight isometric-offset view
- Floating elements on clean gradient background
- Soft plastic or clay material with subsurface scattering
- Color palette: soft pastels, matte finish - pink, baby blue, mint, cream, lavender
- Soft global illumination, ambient occlusion, smooth rounded edges

FORBIDDEN: No text, numbers, interface elements, or UI components. Pure sculptural form.""",

    "fantasy": """Generate an epic high fantasy illustration for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE fantasy scene expressing "{core_theme}" with epic grandeur.
Reimagine the inspiration as something from a fantasy world: enchanted forests, mystical artifacts,
ancient towers, magical creatures (silhouettes), legendary items, cloud-crowned kingdoms.

STYLE SPECIFICATIONS:
Lord of the Rings concept art meets classic fantasy illustration. Epic scope with intimate detail. Oil painting quality with visible brushwork. Magic feels ancient and earned.

TECHNICAL REQUIREMENTS:
- Painterly brushstrokes, visible texture
- Wide cinematic composition, rule of thirds
- Dramatic atmospheric perspective with depth haze
- Color palette: deep shadows, metallic gold/silver, mystical blues, firelight orange
- Volumetric lighting, god rays through clouds or trees
- Epic sense of scale

FORBIDDEN: No text, readable runes, or letter-like symbols. No photorealistic human faces.""",

    "comic_book": """Generate a dynamic comic book panel for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE comic book scene expressing "{core_theme}" with explosive energy.
Transform the inspiration into dynamic action: objects in motion, dramatic reveals,
heroic moments, visual explosions of celebration. What would make a great splash page?

STYLE SPECIFICATIONS:
Modern American comic book aesthetic. Bold confident ink lines, dramatic cel-shading. The energy of a splash page that makes you hear the action.

TECHNICAL REQUIREMENTS:
- Bold black outlines, confident linework
- Flat colors with cel-shading and dramatic shadows
- CMYK-style vibrant colors, slight halftone dot texture
- Dynamic composition: Dutch angles, forced perspective, action lines
- High contrast with deep black shadows
- Visual energy effects (speed lines, impact marks) where appropriate

FORBIDDEN: No text, speech bubbles, sound effects, or any lettering. Pure visual storytelling.""",

    "watercolor": """Generate a soft watercolor painting for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE watercolor scene expressing "{core_theme}" with delicate beauty.
Reimagine the inspiration as something that flows beautifully in watercolor: city streets,
delicate flowers, soft ambient light, birds, peaceful nature scenes.

STYLE SPECIFICATIONS:
Authentic wet-on-wet watercolor technique. Beautiful unpredictability of pigment meeting water. Loose, expressive, emotionally evocative.

TECHNICAL REQUIREMENTS:
- Visible cold-pressed paper texture
- Translucent color layers with natural bleeding and blooming
- Deliberate white space (paper showing through)
- Color palette: soft pastels, watery blues, indigo, violet, touches of warm ochre
- Organic soft edges, occasional controlled hard edges for contrast
- Paint drips, splashes, and happy accidents

FORBIDDEN: No text, sharp digital lines, or perfect geometric shapes. Must feel hand-painted.""",

    "cyberpunk": """Generate a futuristic cyberpunk scene for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE cyberpunk scene expressing "{core_theme}" in a neon-drenched future.
Transform the inspiration into high-tech imagery: holographic displays, chrome machinery,
neon-lit streets, futuristic devices, sci-fi reimaginings of iconic objects.

STYLE SPECIFICATIONS:
Blade Runner meets cyberpunk noir. High-tech low-life aesthetic where advanced technology coexists with gritty urban decay.

TECHNICAL REQUIREMENTS:
- Night scene with rain, steam, or drifting light particles
- Neon glow effects with bloom and chromatic aberration
- Reflections on wet surfaces, puddles, chrome
- Color palette: hot neon pink, electric cyan, acid green, deep black shadows
- Holographic elements, scan lines, subtle digital glitches
- Atmospheric haze and volumetric lighting

FORBIDDEN: No readable text, binary code, alphanumeric data, or legible signage.""",

    "paper_cutout": """Generate a layered paper cutout diorama for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE paper diorama expressing "{core_theme}" through layered silhouettes.
Transform the inspiration into paper craft: layered city silhouettes, architectural elements,
seasonal-neutral landscapes, decorative forms - things that work as cut paper layers.

STYLE SPECIFICATIONS:
Exquisite paper craft in kirigami tradition. Multiple layers creating depth and dimension. Premium pop-up book or museum installation quality.

TECHNICAL REQUIREMENTS:
- 5-7 distinct paper layers creating parallax depth
- Realistic paper texture: slight fiber visibility, clean cut edges
- Dramatic shadows between layers from side lighting
- Color palette: premium paper - white, cream, gold foil, silver, royal blue, deep red
- Sharp scissor/laser-cut edges on each layer
- Subtle paper curl and dimensional quality

FORBIDDEN: No printed text, words, or letters. Imagery through cut shapes and silhouettes only.""",

    "pop_art": """Generate a Pop Art poster for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE pop art composition expressing "{core_theme}" as Warhol would.
Transform the inspiration into bold graphic icons: everyday objects made iconic,
consumer symbols as graphic motifs, bold repetition, striking simple shapes.

STYLE SPECIFICATIONS:
Classic Pop Art in Andy Warhol and Roy Lichtenstein tradition. Bold, iconic, reproducible. Advertising language as fine art.

TECHNICAL REQUIREMENTS:
- Bold flat colors with hard edges
- Ben-Day dots / halftone pattern visible
- Slight CMYK registration offset for silkscreen effect
- Color palette: clashing brights - hot pink, electric yellow, cyan, black, white
- Iconic central subject, possibly repeated in grid
- High contrast, minimal gradients

FORBIDDEN: No text, brand names, or lettering of any kind. Pure graphic iconography.""",

    "lego": """Generate a scene built entirely from plastic toy bricks for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE brick-built scene expressing "{core_theme}" as a master builder would.
Transform the inspiration into brick constructions: miniature cities, vehicles,
characters (minifig style), dynamic landscapes - anything that could be built from toy bricks.

STYLE SPECIFICATIONS:
Everything is awesome in interlocking plastic bricks. Miniature world of toy blocks photographed with loving macro attention.

TECHNICAL REQUIREMENTS:
- Every object constructed from recognizable brick shapes with studs
- Macro photography perspective with tilt-shift blur effect
- Shiny ABS plastic texture with subsurface scattering
- Color palette: primary colors (red, blue, yellow) plus white, green, black
- Visible brick studs and connection points
- Miniature world scale with dramatic depth of field

FORBIDDEN: No printed graphics or text on any brick surface. Pure brick construction only.""",

    "linocut": """Generate a linocut print for a greeting card.

THEME TO INTERPRET: {core_theme}
INSPIRATION (adapt creatively, don't copy literally): {visual_metaphor}
MOOD TO CONVEY: {mood}

YOUR CREATIVE TASK:
Create a UNIQUE linocut expressing "{core_theme}" through bold carved shapes.
Transform the inspiration into high-contrast graphics: simplified symbolic scenes,
folk art animals, decorative patterns, strong silhouettes - things that carve beautifully.

STYLE SPECIFICATIONS:
Traditional relief printmaking aesthetic. Hand-carved linoleum transferred to paper. Folk art meets fine art. Bold, graphic, with subtle imperfections.

TECHNICAL REQUIREMENTS:
- High contrast with strong negative/positive space interplay
- Visible carving marks and gouge textures
- Slightly uneven ink coverage (authentic print quality)
- Color options: black ink on cream/white paper, OR two-color (black + red/blue)
- Bold simplified shapes, no fine detail smaller than a carving tool could make
- Paper texture visible in unprinted areas

FORBIDDEN: No text, letters, or legible symbols. Carved shapes and ink texture only.""",
}


# ============================================================================
# RANDOMIZATION POOLS FOR MAXIMUM DIVERSITY
# Each image generation picks random elements from these pools to ensure
# that even with identical input, every card looks completely different
# ============================================================================

# Atmospheric conditions - affects lighting and mood
RANDOM_ATMOSPHERES = [
    "soft city dawn with rising warm light",
    "clear night with distant constellations",
    "golden sunset reflecting off glass surfaces",
    "misty dawn with suspended particles",
    "aurora-like gradients dancing above",
    "soft overcast with diffused silver light",
    "twilight blue hour with warm lights glowing",
    "bright morning haze over reflective surfaces",
    "moonlit scene with gentle highlights",
    "after-storm stillness with dramatic clouds parting",
    "cozy lamplight glow against evening backdrop",
    "sunlight breaking through dense branches",
]

# Focal subjects - the main object/scene to feature
RANDOM_SUBJECTS = [
    "an ornate vintage music box playing silently",
    "a crystal sphere containing a miniature world",
    "an ancient brass telescope pointed at the stars",
    "a grandfather clock with precision pendulum",
    "a Victorian greenhouse with impossible flowers",
    "a handcrafted workshop table with velvet textures",
    "an enchanted forest clearing with glowing mushrooms",
    "a stone bridge arching over a flowing stream",
    "a vintage typewriter with fresh ink strokes",
    "a compass rose embedded in carved stone",
    "a grand piano with warm reflections on keys",
    "an artisan's workshop with tools mid-project",
    "a ship's wheel from a deep-ocean vessel",
    "a mechanical orrery with spinning planets",
    "a antique hourglass with slow-falling sand",
    "a collection of vintage components in a box",
    "a solitary cabin with warm windows glowing",
    "an architect's model in careful construction",
    "a treasure chest overflowing with bright tokens",
    "a vintage camera capturing the perfect moment",
    "a spiral staircase leading to somewhere magical",
    "a baker's table with crafted sweets",
    "a library corner with warm lamplight reflections",
    "a vintage hot air balloon basket in clear air",
    "a clockwork bird singing in a glass garden",
]

# Composition variations - camera angles and framing
RANDOM_COMPOSITIONS = [
    "intimate macro close-up with creamy bokeh",
    "sweeping wide shot with epic sense of scale",
    "dramatic low angle looking upward heroically",
    "gentle bird's eye view from above",
    "dutch angle adding dynamic energy",
    "perfectly centered symmetrical composition",
    "rule of thirds with subject off-center",
    "through a window frame or archway",
    "reflected in a puddle or mirror",
    "layered depth with foreground interest",
    "silhouette against dramatic sky",
    "extreme close-up of a single detail",
]

# Color accent variations - unique color emphasis for each card
RANDOM_COLOR_ACCENTS = [
    "rich crimson red like polished lacquer",
    "burnished gold with cinematic highlights",
    "deep sapphire blue of evening studios",
    "warm copper and brass tones",
    "silver and platinum shimmer",
    "forest green of layered foliage",
    "soft rose gold blush",
    "royal purple of warm dusk",
    "amber and honey warmth",
    "teal and aquamarine tones",
    "burgundy wine richness",
    "champagne and cream elegance",
]

# Mood/emotion variations
RANDOM_MOODS = [
    "nostalgic warmth and cherished memories",
    "wonder and magical discovery",
    "peaceful serenity and calm",
    "joyful celebration and festivity",
    "cozy comfort and togetherness",
    "elegant sophistication and refinement",
    "whimsical playfulness and delight",
    "majestic grandeur and awe",
    "intimate tenderness and care",
    "hopeful anticipation and excitement",
    "timeless classic beauty",
    "dreamy ethereal enchantment",
]

# Semantic theme mapping - maps gratitude reasons to visual themes
SEMANTIC_THEME_MAPPING = {
    # Work-related keywords -> visual themes
    "project": ["clockwork precision", "architectural achievement", "masterful construction"],
    "team": ["orchestra in harmony", "constellation of stars", "interconnected gears"],
    "leadership": ["lighthouse beacon", "compass pointing true", "captain at the helm"],
    "support": ["ancient bridge", "steady foundation", "sheltering tree"],
    "innovation": ["emerging mechanism", "blooming in momentum", "light breaking through"],
    "deadline": ["clock striking midnight", "finish line crossed", "last piece of puzzle"],
    "help": ["warm hands offering", "bridge across chasm", "light in darkness"],
    "mentor": ["guiding star", "ancient map", "wise owl silhouette"],
    "dedication": ["eternal flame", "carved stone monument", "deep roots"],
    "creativity": ["artist's palette", "aurora colors", "impossible flowers"],
}


def _get_random_variation() -> dict:
    """Generate a unique random variation for image generation.
    
    Returns a dictionary with random elements to inject variety
    into every single image generation.
    """
    return {
        "atmosphere": random.choice(RANDOM_ATMOSPHERES),
        "subject": random.choice(RANDOM_SUBJECTS),
        "composition": random.choice(RANDOM_COMPOSITIONS),
        "color_accent": random.choice(RANDOM_COLOR_ACCENTS),
        "mood": random.choice(RANDOM_MOODS),
        "seed_phrase": f"unique variation #{random.randint(1000, 9999)}",
    }


def _extract_semantic_theme(reason: str | None, message: str | None) -> str:
    """Extract a visual theme from the gratitude reason/message.
    
    Analyzes the text and maps it to visual concepts that work well
    for image generation.
    """
    text = f"{reason or ''} {message or ''}".lower()
    
    matched_themes = []
    for keyword, themes in SEMANTIC_THEME_MAPPING.items():
        if keyword in text:
            matched_themes.extend(themes)
    
    if matched_themes:
        return random.choice(matched_themes)
    
    # Default creative themes if no match
    default_themes = [
        "celebration of achievement",
        "warmth of gratitude",
        "creative transformation and wonder",
        "joy of connection",
        "beauty of appreciation",
    ]
    return random.choice(default_themes)


class GeminiClient:
    """Client for Google Gemini API via LiteLLM proxy.

    Provides methods for generating stylized text and images for cards.
    Handles errors, retries, and logging automatically.

    Example:
        >>> client = GeminiClient(
        ...     api_key="your-key",
        ...     base_url="https://litellm.pro-4.ru/v1"
        ... )
        >>> text = await client.generate_text(
        ...     prompt="",
        ...     style="ode",
        ...     recipient="Иван Петров",
        ...     reason="отличную работу над проектом"
        ... )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://litellm.pro-4.ru/v1",
        text_model: str = "gemini-2.5-flash",
        image_model: str = "gemini/gemini-3.1-flash-image-preview",
    ):
        """Initialize Gemini client via LiteLLM proxy.

        Args:
            api_key: LiteLLM API key
            base_url: LiteLLM proxy base URL
            text_model: Model for text generation
            image_model: Model for image generation

        Raises:
            GeminiConfigError: If API key is missing or invalid
        """
        if not api_key or not api_key.strip():
            raise GeminiConfigError(
                message="Gemini API key is required",
                missing_param="api_key",
            )

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._text_model = text_model
        self._image_model = image_model
        self._http_client: Optional[httpx.AsyncClient] = None

        logger.info(
            "Gemini client initialized (LiteLLM proxy)",
            extra={
                "base_url": self._base_url,
                "text_model": self._text_model,
                "image_model": self._image_model,
            },
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=HTTP_TIMEOUT_SECONDS,
            )
        return self._http_client

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def analyze_for_visual(
        self,
        recipient: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
    ) -> VisualConcept:
        """Analyze gratitude text and extract visual concepts for image generation.

        This method transforms user's gratitude text into structured visual concepts
        that can be used to generate meaningful images without literal text.

        Args:
            recipient: Name of the person receiving the greeting
            reason: Reason for gratitude (optional)
            message: Personal message from sender (optional)

        Returns:
            VisualConcept with theme, metaphor, elements, and mood

        Raises:
            GeminiTextGenerationError: If analysis fails
            GeminiRateLimitError: If rate limit is exceeded
        """
        # Build the analysis prompt
        full_prompt = VISUAL_ANALYSIS_PROMPT.format(
            recipient=recipient,
            reason=reason or "профессиональные достижения",
            message=message or "Спасибо за отличную работу!",
        )

        logger.debug(
            "Analyzing gratitude for visual concept",
            extra={
                "recipient": recipient,
                "has_reason": bool(reason),
                "has_message": bool(message),
            },
        )

        try:
            client = await self._get_client()

            response = await client.post(
                "/chat/completions",
                json={
                    "model": self._text_model,
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": ANALYSIS_MAX_TOKENS,
                    "temperature": ANALYSIS_TEMPERATURE,
                    "response_format": {"type": "json_object"},
                },
            )

            if response.status_code == 400 and "response_format" in str(response.text or "").lower():
                logger.warning(
                    "OpenAI compatibility rejected response_format for visual analysis, retrying without it",
                    extra={"recipient": recipient},
                )
                response = await client.post(
                    "/chat/completions",
                    json={
                        "model": self._text_model,
                        "messages": [
                            {"role": "user", "content": full_prompt}
                        ],
                        "max_tokens": ANALYSIS_MAX_TOKENS,
                        "temperature": ANALYSIS_TEMPERATURE,
                    },
                )

            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))

            response.raise_for_status()
            data = response.json()

            if not data.get("choices"):
                raise GeminiTextGenerationError(
                    message="Gemini API вернул пустой ответ при анализе",
                    details={"recipient": recipient},
                )

            response_text = data["choices"][0]["message"]["content"].strip()

            try:
                parsed_text = self._extract_json_payload(response_text)
                parsed = json.loads(parsed_text)

                # Extract all fields with sensible defaults
                visual_concept = VisualConcept(
                    core_theme=parsed.get("core_theme", "gratitude"),
                    visual_metaphor=parsed.get(
                        "visual_metaphor",
                        "A vintage compass on weathered map in a warm urban environment"
                    ),
                    key_elements=parsed.get(
                        "key_elements",
                        ["compass", "map", "warm tones", "clear pathway", "adventure"]
                    ),
                    mood=parsed.get("mood", "discovery and appreciation"),
                    composition=parsed.get("composition", "medium shot, eye level"),
                    lighting=parsed.get("lighting", "soft natural daylight"),
                )

                logger.info(
                    f"Visual concept analyzed: theme='{visual_concept.core_theme}', "
                    f"elements={len(visual_concept.key_elements)}, "
                    f"composition='{visual_concept.composition}'",
                    extra={
                        "core_theme": visual_concept.core_theme,
                        "mood": visual_concept.mood,
                        "composition": visual_concept.composition,
                        "lighting": visual_concept.lighting,
                    },
                )

                return visual_concept

            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse visual analysis JSON: {e}, using random fallback",
                    extra={
                        "response_text": response_text[:220],
                        "parsed_text": parsed_text[:220],
                    },
                )
                # Use random fallback for diversity
                return get_fallback_visual_concept()

        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during visual analysis: {e}",
                extra={"status_code": e.response.status_code},
                exc_info=True,
            )
            raise GeminiTextGenerationError(
                message=f"HTTP ошибка при анализе: {e.response.status_code}",
                details={"recipient": recipient},
                original_error=e,
            )
        except (httpx.RequestError, httpx.TimeoutException) as e:
            # Network errors that weren't caught by retry - use random fallback
            logger.warning(
                f"Network error during visual analysis: {e}, using random fallback",
                extra={"recipient": recipient, "error_type": type(e).__name__},
            )
            return get_fallback_visual_concept()

        except (KeyError, TypeError, ValueError) as e:
            # Data parsing errors - use random fallback
            logger.warning(
                f"Data parsing error during visual analysis: {e}, using random fallback",
                extra={"recipient": recipient, "error_type": type(e).__name__},
            )
            return get_fallback_visual_concept()

    @staticmethod
    def _extract_json_payload(response_text: str, expect_array: bool = False) -> str:
        """Extract pure JSON text from model output that may contain wrappers."""
        text = response_text.strip()
        if not text:
            return ""

        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                if line.startswith("```") and in_json:
                    break
                if in_json:
                    json_lines.append(line)
            text = "\n".join(json_lines).strip()

        if expect_array:
            start_idx = text.find("[")
            end_idx = text.rfind("]") + 1
        else:
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1

        if start_idx >= 0 and end_idx > start_idx:
            text = text[start_idx:end_idx]

        # Some models leak trailing commas in JSON
        text = re.sub(r",\s*([\]\}])", r"\\1", text)
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        return text

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def analyze_for_visual_batch(
        self,
        recipient: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        count: int = 4,
        styles: Optional[List[str]] = None,
    ) -> List[VisualConcept]:
        """Analyze gratitude and generate MULTIPLE diverse visual concepts.

        This multi-agent ultrathink method generates N distinct visual concepts
        in a single API call, ensuring each uses a different metaphor category
        for maximum thematic diversity while maintaining semantic coherence.

        The method uses a sophisticated prompt with simulated agents:
        - Theme Analyst: Extracts core emotional theme
        - Category Distributor: Assigns different metaphor categories
        - Uniqueness Validator: Ensures no duplicate subjects/elements
        - Scene Generators: Creates distinct scenes for each category
        - Coherence Checker: Verifies thematic unity across concepts

        Args:
            recipient: Name of the person receiving the greeting
            reason: Reason for gratitude (optional)
            message: Personal message from sender (optional)
            count: Number of diverse concepts to generate (default 4)
            styles: Optional list of image style codes for style-aware fallback

        Returns:
            List of VisualConcept objects, each from a different metaphor category

        Raises:
            GeminiTextGenerationError: If analysis fails
            GeminiRateLimitError: If rate limit is exceeded
        """
        # Build the batch analysis prompt with dynamic category assignments
        category_assignments = _build_category_assignments(count)
        full_prompt = BATCH_VISUAL_ANALYSIS_PROMPT.format(
            recipient=recipient,
            reason=reason or "профессиональные достижения",
            message=message or "Спасибо за отличную работу!",
            count=count,
            category_assignments=category_assignments,
        )

        logger.info(
            f"Analyzing gratitude for {count} diverse visual concepts (ultrathink batch)",
            extra={
                "recipient": recipient,
                "count": count,
                "has_reason": bool(reason),
                "has_message": bool(message),
            },
        )

        try:
            client = await self._get_client()

            # Use slightly higher temperature for creative diversity
            # and more tokens for multiple concepts
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self._text_model,
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": ANALYSIS_MAX_TOKENS * 2,  # More tokens for batch
                    "temperature": 0.5,  # Balanced: creative but consistent
                },
            )

            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))

            response.raise_for_status()
            data = response.json()

            if not data.get("choices"):
                raise GeminiTextGenerationError(
                    message="Gemini API вернул пустой ответ при batch анализе",
                    details={"recipient": recipient, "count": count},
                )

            response_text = data["choices"][0]["message"]["content"].strip()

            # Parse JSON array response
            concepts = self._parse_batch_concepts(response_text, count, styles)

            logger.info(
                f"Generated {len(concepts)} diverse visual concepts: "
                f"themes={[c.core_theme for c in concepts]}",
                extra={
                    "count": len(concepts),
                    "themes": [c.core_theme for c in concepts],
                    "moods": [c.mood for c in concepts],
                },
            )

            return concepts

        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during batch visual analysis: {e}",
                extra={"status_code": e.response.status_code},
                exc_info=True,
            )
            # Fall back to diverse fallbacks
            return self._get_diverse_fallbacks(count, styles)
        except (httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning(
                f"Network error during batch visual analysis: {e}, using diverse fallbacks",
                extra={"recipient": recipient, "error_type": type(e).__name__},
            )
            return self._get_diverse_fallbacks(count, styles)
        except Exception as e:
            logger.warning(
                f"Unexpected error during batch visual analysis: {e}, using diverse fallbacks",
                extra={"recipient": recipient, "error_type": type(e).__name__},
            )
            return self._get_diverse_fallbacks(count, styles)

    def _parse_batch_concepts(
        self,
        response_text: str,
        expected_count: int,
        styles: Optional[List[str]] = None,
    ) -> List[VisualConcept]:
        """Parse JSON array of visual concepts from API response.

        Handles various response formats including markdown code blocks.
        Falls back to diverse fallback concepts if parsing fails.

        Args:
            response_text: Raw response text from API
            expected_count: Expected number of concepts
            styles: Optional list of style codes for style-aware fallback

        Returns:
            List of VisualConcept objects
        """
        try:
            cleaned_text = self._extract_json_payload(response_text, expect_array=True)
            if not cleaned_text.startswith("["):
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    cleaned_text = response_text[start_idx:end_idx]

            parsed_array = json.loads(cleaned_text)

            if not isinstance(parsed_array, list):
                raise ValueError("Expected JSON array")

            concepts = []
            for item in parsed_array:
                if isinstance(item, dict):
                    concept = VisualConcept(
                        core_theme=item.get("core_theme", "gratitude"),
                        visual_metaphor=item.get(
                        "visual_metaphor",
                            "A vintage compass on weathered map in a warm urban environment"
                        ),
                        key_elements=item.get(
                            "key_elements",
                            ["compass", "map", "warm tones", "clear pathway", "adventure"]
                        ),
                        mood=item.get("mood", "discovery and appreciation"),
                        composition=item.get("composition", "medium shot, eye level"),
                        lighting=item.get("lighting", "soft natural daylight"),
                    )
                    concepts.append(concept)

            # Validate we got enough concepts
            if len(concepts) >= expected_count:
                return concepts[:expected_count]
            elif len(concepts) > 0:
                # Pad with diverse fallbacks if we got partial results
                logger.warning(
                    f"Got {len(concepts)} concepts, expected {expected_count}, padding with fallbacks"
                )
                remaining = expected_count - len(concepts)
                fallbacks = self._get_diverse_fallbacks(remaining, styles)
                return concepts + fallbacks
            else:
                raise ValueError("No valid concepts parsed")

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning(
                f"Failed to parse batch visual concepts: {e}, using diverse fallbacks",
                extra={"response_preview": response_text[:300]},
            )
            return self._get_diverse_fallbacks(expected_count, styles)

    def _get_diverse_fallbacks(
        self,
        count: int,
        styles: Optional[List[str]] = None,
    ) -> List[VisualConcept]:
        """Get diverse fallback concepts, optionally style-aware.

        If styles are provided, uses style-specific fallback mapping.
        Otherwise uses stratified sampling for diversity.

        Args:
            count: Number of fallback concepts needed
            styles: Optional list of style codes

        Returns:
            List of diverse VisualConcept objects
        """
        if styles and len(styles) >= count:
            # Use style-specific fallbacks for maximum appropriateness
            return [
                get_fallback_visual_concept_for_style(style)
                for style in styles[:count]
            ]
        else:
            # Use stratified sampling for diversity
            return get_diverse_fallback_concepts(count)

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def generate_text(
        self,
        prompt: str,
        style: str,
        recipient: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> str:
        """Generate stylized greeting text using Gemini.

        Args:
            prompt: Base prompt (usually empty, style template is used)
            style: Text style code (ode, future, haiku, newspaper, standup)
            recipient: Name of the person receiving the greeting
            reason: Reason for gratitude (optional)
            message: Additional message from sender (optional)
            sender: Name of the person sending the greeting (optional)

        Returns:
            Generated text content

        Raises:
            GeminiTextGenerationError: If generation fails
            GeminiRateLimitError: If rate limit is exceeded

        Example:
            >>> text = await client.generate_text(
            ...     prompt="",
            ...     style="haiku",
            ...     recipient="Анна Смирнова",
            ...     reason="успешный запуск нового продукта",
            ...     message="за вклад в развитие продукта!",
            ...     sender="Иван Петров"
            ... )
        """
        if style not in TEXT_STYLE_PROMPTS:
            raise GeminiTextGenerationError(
                message=f"Неизвестный стиль текста: {style}",
                details={"style": style, "available_styles": list(TEXT_STYLE_PROMPTS.keys())},
            )

        # Build the prompt from template
        style_template = TEXT_STYLE_PROMPTS[style]
        full_prompt = style_template.format(
            recipient=recipient,
            reason=reason or "вклад в развитие компании",
            message=message or "Спасибо за работу!",
            sender=sender or "коллеги",
        )

        logger.debug(
            f"Generating text with style '{style}' for recipient",
            extra={
                "style": style,
                "has_reason": bool(reason),
                "has_message": bool(message),
            },
        )

        try:
            client = await self._get_client()

            # OpenAI-compatible chat completions request
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self._text_model,
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": TEXT_MAX_TOKENS,
                    "temperature": TEXT_TEMPERATURE,
                },
            )

            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))

            response.raise_for_status()
            data = response.json()

            # Extract text from response
            if not data.get("choices"):
                raise GeminiTextGenerationError(
                    message="Gemini API вернул пустой ответ",
                    details={"style": style},
                )

            generated_text = data["choices"][0]["message"]["content"].strip()

            logger.info(
                f"Text generated successfully: {len(generated_text)} characters",
                extra={
                    "style": style,
                    "text_length": len(generated_text),
                },
            )

            return generated_text

        except GeminiTextGenerationError:
            raise
        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during text generation: {e}",
                extra={"status_code": e.response.status_code},
                exc_info=True,
            )
            raise GeminiTextGenerationError(
                message=f"HTTP ошибка при генерации текста: {e.response.status_code}",
                details={"style": style},
                original_error=e,
            )
        except Exception as e:
            logger.error(
                f"Text generation failed: {e}",
                extra={
                    "style": style,
                    "recipient": recipient,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Check for rate limit errors
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise GeminiRateLimitError(original_error=e)

            raise GeminiTextGenerationError(
                message=f"Не удалось сгенерировать текст в стиле '{style}'",
                details={"style": style},
                original_error=e,
            )

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def generate_image(
        self,
        visual_concept: VisualConcept,
        style: str,
    ) -> Tuple[bytes, str]:
        """Generate an image using Gemini image model.

        Uses structured VisualConcept data instead of raw text to avoid
        literal text appearing in images.

        Args:
            visual_concept: Analyzed visual concept with metaphor and elements
            style: Image style code (knitted, pixel_art, fantasy, etc.)

        Returns:
            Tuple of (image_bytes, prompt_used) where image_bytes is PNG format

        Raises:
            GeminiImageGenerationError: If generation fails
            GeminiRateLimitError: If rate limit is exceeded

        Example:
            >>> concept = VisualConcept(
            ...     core_theme="innovation",
            ...     visual_metaphor="A brass orrery mechanism emerging at dawn",
            ...     key_elements=["orrery", "gears", "sunrise", "light"],
            ...     mood="awakening and precision",
            ...     composition="low angle close-up, shallow depth of field",
            ...     lighting="warm sunrise from the right, golden hour quality"
            ... )
            >>> image_bytes, prompt = await client.generate_image(concept, "fantasy")
        """
        if style not in IMAGE_STYLE_PROMPTS:
            raise GeminiImageGenerationError(
                message=f"Неизвестный стиль изображения: {style}",
                details={"style": style, "available_styles": list(IMAGE_STYLE_PROMPTS.keys())},
            )

        # Build the prompt from template using VisualConcept
        # Key change: pass core_theme so each style can REINTERPRET the concept creatively
        # This creates diversity - same theme, different visual interpretations per style
        style_template = IMAGE_STYLE_PROMPTS[style]
        full_prompt = style_template.format(
            core_theme=visual_concept.core_theme,
            visual_metaphor=visual_concept.visual_metaphor,
            key_elements=", ".join(visual_concept.key_elements),
            mood=visual_concept.mood,
        )

        logger.debug(
            f"Generating image with style '{style}'",
            extra={
                "style": style,
                "core_theme": visual_concept.core_theme,
                "mood": visual_concept.mood,
            },
        )

        try:
            client = await self._get_client()

            def _build_payload(*, image_config: bool = True) -> dict:
                payload = {
                    "model": self._image_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Generate an image based on this description:\n\n{full_prompt}"
                        }
                    ],
                    "max_tokens": IMAGE_MAX_TOKENS,
                    "modalities": ["image", "text"],
                }
                if image_config:
                    payload["extra_body"] = {"imageConfig": {"aspectRatio": "2:3"}}
                return payload

            # Request image generation via chat completions
            # Gemini image models use modalities parameter for image generation
            # Using 2:3 aspect ratio for vertical A6 postcard format (105x148mm)
            response = await client.post(
                "/chat/completions",
                json=_build_payload(image_config=False),
            )

            if response.status_code == 400 and "imageconfig" in str(response.text or "").lower():
                logger.warning(
                    "Upstream rejected imageConfig, retrying with imageConfig",
                    extra={"style": style},
                )
                response = await client.post(
                    "/chat/completions",
                    json=_build_payload(image_config=True),
                )

            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))

            response.raise_for_status()
            data = response.json()

            # Extract image from response
            image_bytes = self._extract_image_from_response(data, style)

            logger.info(
                f"Image generated successfully: {len(image_bytes)} bytes",
                extra={
                    "style": style,
                    "image_size": len(image_bytes),
                },
            )

            return image_bytes, full_prompt

        except GeminiImageGenerationError:
            raise
        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during image generation: {e}",
                extra={"status_code": e.response.status_code},
                exc_info=True,
            )
            raise GeminiImageGenerationError(
                message=f"HTTP ошибка при генерации изображения: {e.response.status_code}",
                details={"style": style},
                original_error=e,
            )
        except Exception as e:
            logger.error(
                f"Image generation failed: {e}",
                extra={
                    "style": style,
                    "core_theme": visual_concept.core_theme,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Check for rate limit errors
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise GeminiRateLimitError(original_error=e)

            raise GeminiImageGenerationError(
                message=f"Не удалось сгенерировать изображение в стиле '{style}'",
                details={"style": style},
                original_error=e,
            )

    def _extract_image_from_response(self, data: Dict[str, Any], style: str) -> bytes:
        """Extract image bytes from API response.

        Handles multiple response formats:
        1. LiteLLM format: message.images[0]["image_url"]["url"]
        2. Direct base64 in message content
        3. Image URL in response
        4. Inline data with base64 encoding

        Args:
            data: API response data
            style: Image style (for error context)

        Returns:
            Image bytes in PNG format

        Raises:
            GeminiImageGenerationError: If image extraction fails
        """
        if not data.get("choices"):
            raise GeminiImageGenerationError(
                message="API вернул пустой ответ",
                details={"style": style},
            )

        choice = data["choices"][0]
        message = choice.get("message", {})

        # Format 0: LiteLLM Gemini image format - message.images array
        images = message.get("images", [])
        if images and len(images) > 0:
            image_obj = images[0]
            if isinstance(image_obj, dict) and "image_url" in image_obj:
                url = image_obj["image_url"]
                if isinstance(url, dict):
                    url = url.get("url", "")
                if url.startswith("data:image"):
                    base64_data = url.split("base64,")[1]
                    return base64.b64decode(base64_data)

        content = message.get("content", "")

        # Try to extract base64 image from content
        # Format 1: Direct base64 string
        if content and not content.startswith("http"):
            try:
                # Check if it's a base64 image
                if "base64," in content:
                    # data:image/png;base64,... format
                    base64_data = content.split("base64,")[1]
                else:
                    # Raw base64
                    base64_data = content

                # Clean and decode
                base64_data = base64_data.strip()
                image_bytes = base64.b64decode(base64_data)

                # Verify it's valid image data (PNG starts with specific bytes)
                if image_bytes[:4] == b"\x89PNG" or image_bytes[:2] == b"\xff\xd8":
                    return image_bytes

            except (ValueError, base64.binascii.Error) as e:
                logger.debug(
                    "Failed to decode base64 from direct content, trying other formats",
                    extra={"error": str(e), "style": style},
                )

        # Format 2: Check for image_url in content parts
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if "image_url" in part:
                        url = part["image_url"]
                        if isinstance(url, dict):
                            url = url.get("url", "")
                        if url.startswith("data:image"):
                            base64_data = url.split("base64,")[1]
                            return base64.b64decode(base64_data)
                    if "inline_data" in part:
                        inline = part["inline_data"]
                        if "data" in inline:
                            return base64.b64decode(inline["data"])

        # Format 3: Check message for image data
        if "image" in message:
            image_data = message["image"]
            if isinstance(image_data, str):
                return base64.b64decode(image_data)
            if isinstance(image_data, dict) and "data" in image_data:
                return base64.b64decode(image_data["data"])

        # Format 4: Check for data field directly
        if "data" in data:
            for item in data.get("data", []):
                if "b64_json" in item:
                    return base64.b64decode(item["b64_json"])
                if "url" in item and item["url"].startswith("data:"):
                    base64_data = item["url"].split("base64,")[1]
                    return base64.b64decode(base64_data)

        # Log detailed response structure for debugging
        content_preview = str(content)[:500] if content else "empty"
        logger.error(
            f"Failed to extract image from response. "
            f"style={style}, response_keys={list(data.keys()) if data else []}, "
            f"choice_keys={list(choice.keys()) if choice else []}, "
            f"message_keys={list(message.keys()) if message else []}, "
            f"content_type={type(content).__name__}, has_images={bool(images)}, "
            f"content_preview={content_preview}"
        )
        raise GeminiImageGenerationError(
            message="Не удалось извлечь изображение из ответа API",
            details={
                "style": style,
                "response_keys": list(data.keys()) if data else [],
                "message_keys": list(message.keys()) if message else [],
            },
        )

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def generate_image_direct(
        self,
        style: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Tuple[bytes, str]:
        """Generate unique image directly with built-in randomization.
        
        This is the NEW one-stage generation approach that produces highly diverse
        images by injecting random variations into each call. No intermediate
        analysis step needed.
        
        Args:
            style: Image style code (knitted, pixel_art, fantasy, etc.)
            reason: Optional reason for gratitude (used for semantic theming)
            message: Optional personal message (used for semantic theming)
            
        Returns:
            Tuple of (image_bytes, prompt_used) where image_bytes is PNG format
            
        Raises:
            GeminiImageGenerationError: If generation fails
            GeminiRateLimitError: If rate limit is exceeded
        """
        if style not in IMAGE_STYLE_PROMPTS:
            raise GeminiImageGenerationError(
                message=f"Неизвестный стиль изображения: {style}",
                details={"style": style, "available_styles": list(IMAGE_STYLE_PROMPTS.keys())},
            )
        
        # Generate unique random variation for this specific call
        variation = _get_random_variation()
        semantic_theme = _extract_semantic_theme(reason, message)
        
        # Build the direct generation prompt
        style_template = IMAGE_STYLE_PROMPTS[style]
        
        # Create a rich, unique prompt combining:
        # 1. Random subject from our diverse pool
        # 2. Semantic theme extracted from gratitude
        # 3. Random atmospheric and compositional elements
        # 4. Style-specific requirements
        
        direct_prompt = f"""Generate a BEAUTIFUL and UNIQUE corporate celebration card image.

═══════════════════════════════════════════════════════════════════════════════
THIS CARD'S UNIQUE IDENTITY - {variation['seed_phrase']}
═══════════════════════════════════════════════════════════════════════════════

FEATURED SUBJECT: {variation['subject']}
ATMOSPHERE: {variation['atmosphere']}
COMPOSITION: {variation['composition']}
COLOR ACCENT: {variation['color_accent']}
EMOTIONAL MOOD: {variation['mood']}
SEMANTIC THEME: {semantic_theme}

═══════════════════════════════════════════════════════════════════════════════
GRATITUDE CONTEXT (inspire the image, don't show as text):
═══════════════════════════════════════════════════════════════════════════════
За что (Reason): {reason or 'вклад в общее дело'}
Послание (Message): {message or 'Спасибо за вклад в рост компании!'}

Interpret the FEELING behind this gratitude. Let it guide the emotional tone,
but DO NOT render any words or text in the image.

═══════════════════════════════════════════════════════════════════════════════
STYLE REQUIREMENTS:
═══════════════════════════════════════════════════════════════════════════════
{style_template.format(
    core_theme=semantic_theme,
    visual_metaphor=variation['subject'],
    mood=variation['mood'],
)}

═══════════════════════════════════════════════════════════════════════════════
ABSOLUTE REQUIREMENTS:
═══════════════════════════════════════════════════════════════════════════════
✗ NEVER render any text, letters, numbers, words, or symbols
✗ NEVER show realistic human faces (silhouettes are acceptable)
✗ NEVER use cliché objects: lanterns, lighthouses, candles, generic glowing orbs
✓ MUST be professional and culturally neutral
✓ MUST be professional greeting card quality - beautiful and polished
✓ MUST feel unique and special - this is a one-of-a-kind card

Now create this unique, beautiful greeting card image."""
        
        logger.debug(
            f"Generating direct image with style '{style}'",
            extra={
                "style": style,
                "semantic_theme": semantic_theme,
                "variation_seed": variation['seed_phrase'],
                "subject": variation['subject'][:50],
            },
        )
        
        try:
            client = await self._get_client()
            
            def _build_payload(*, image_config: bool = True) -> dict:
                payload = {
                    "model": self._image_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Generate an image based on this description:\n\n{direct_prompt}"
                        }
                    ],
                    "max_tokens": IMAGE_MAX_TOKENS,
                    "modalities": ["image", "text"],
                }
                if image_config:
                    payload["extra_body"] = {"imageConfig": {"aspectRatio": "2:3"}}
                return payload

            response = await client.post(
                "/chat/completions",
                json=_build_payload(image_config=False),
            )

            if response.status_code == 400 and "imageconfig" in str(response.text or "").lower():
                logger.warning(
                    "Upstream rejected imageConfig, retrying with imageConfig",
                    extra={"style": style},
                )
                response = await client.post(
                    "/chat/completions",
                    json=_build_payload(image_config=True),
                )
            
            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))
            
            response.raise_for_status()
            data = response.json()
            
            image_bytes = self._extract_image_from_response(data, style)
            
            logger.info(
                f"Direct image generated successfully: {len(image_bytes)} bytes",
                extra={
                    "style": style,
                    "image_size": len(image_bytes),
                    "variation_seed": variation['seed_phrase'],
                },
            )
            
            return image_bytes, direct_prompt
            
        except GeminiImageGenerationError:
            raise
        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during direct image generation: {e}",
                extra={"status_code": e.response.status_code, "style": style},
                exc_info=True,
            )
            raise GeminiImageGenerationError(
                message=f"HTTP ошибка при генерации изображения: {e.response.status_code}",
                details={"style": style},
                original_error=e,
            )
        except Exception as e:
            logger.error(
                f"Direct image generation failed: {e}",
                extra={"style": style, "error_type": type(e).__name__},
                exc_info=True,
            )
            
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise GeminiRateLimitError(original_error=e)
            
            raise GeminiImageGenerationError(
                message=f"Не удалось сгенерировать изображение в стиле '{style}'",
                details={"style": style},
                original_error=e,
            )

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("Gemini client closed")
