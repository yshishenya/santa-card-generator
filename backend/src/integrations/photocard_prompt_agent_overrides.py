"""High-priority style overrides for P4.0 photocard generation.

Drop this file next to the main Gemini client module so it can be imported as:
    from .photocard_prompt_agent_overrides import PHOTOCARD_AGENT_STYLE_OVERRIDES

These overrides are intentionally strict. They are calibrated to the supplied
brand brief and visual references:
- square 1:1 tile
- dominant central motif ~70-80% of frame
- light background
- limited secondary detail
- strict palette
- vector / flat illustration only
"""

PHOTOCARD_AGENT_STYLE_OVERRIDES = {
    "_global": """
REFERENCE-FIRST EXECUTION MODE:
- Treat the provided references as binding art direction, not loose inspiration.
- Match the reference images as closely as possible in:
  1) central motif scale in frame,
  2) background lightness,
  3) density of details,
  4) line weight / module thickness,
  5) palette proportions,
  6) silhouette simplification,
  7) whitespace ratio.
- The result must read clearly at very small size inside a large mosaic logo.
- Keep exactly one dominant central motif occupying roughly 70-80% of the tile.
- Keep all secondary icons/details subordinate and close to the main motif.
- Background must remain very light, preferably #FFFFFF or #B9CDFF.
- Use only the approved brand colors. Never introduce foreign hues.
- Hard ban on photorealism, 3D rendering, gradients, painterly texture, typography, logos, seasonal iconography.
- This is a polished production tile, not an exploratory concept sketch.
""".strip(),

    "bento_grid": """
BENTO GRID CALIBRATION:
- Build a crisp modular tile in the spirit of the supplied bento references.
- Use a 3x3 or 4x3 rectangular grid with one dominant connected central cluster.
- The main figure/object may fragment across neighboring modules, but the overall cluster must still read as a single clear subject.
- Keep the main motif at roughly 70-80% of the total frame through connected modules.
- Allow only 1-3 tiny hobby-icon modules in the remaining cells. They must be secondary.
- Structural tiles must stay rectangular with sharp separations.
- Circles and simple arcs are allowed inside the motif/icons, but not as the structural grid itself.
- Use 4-5 palette colors plus black/white.
- Prefer white or light blue as the outer background.
- Optional depth between modules must be extremely subtle; the illustration still has to feel flat and vector-clean.
- Reject noisy abstract patterning, large empty interior gaps, detached decorative side blocks, and dark background fields.
""".strip(),

    "minimalist_corporate_line_art": """
MINIMALIST LINE-ART CALIBRATION:
- Ignore any earlier instruction that makes the figure tiny. The dominant figure/object must occupy roughly 70-80% of the tile.
- Keep the silhouette centered and instantly readable at thumbnail size.
- Use clean fixed-weight black contour lines, closed shapes, and large calm negative space.
- Hair/clothes can be solid black fills. Skin/open areas should be white negative space.
- Use only black, white, and 1-2 accent colors from the brand palette.
- Thin geometric UI-like frames, tabs, arrows, stars, or similar symbols are allowed only as small supporting details near the main silhouette.
- Do not scatter details around the whole tile.
- No large dark background panels. No gradients. No textures. No facial realism.
- Overall feeling must stay technological, neat, and professional.
""".strip(),

    "quirky_hand_drawn_flat": """
QUIRKY HAND-DRAWN CALIBRATION:
- Ignore any earlier instruction that makes the mascot tiny. The main rounded figure/object must occupy roughly 70-80% of the tile.
- Keep the silhouette soft, friendly, and immediately readable.
- Use black or dark-graphite marker/tush line with lively variation in thickness.
- Use flat bright fills from the approved palette with slight deliberate misregistration / color-offset relative to the contour.
- Keep only 2-5 tiny doodle accents, close to the main motif.
- Do not fill the whole tile with doodle noise.
- Preserve a light, open background and a warm charismatic feel.
- Ban sharp angular anatomy, heavy shading, gradients, realistic texture, and clutter.
""".strip(),
}
