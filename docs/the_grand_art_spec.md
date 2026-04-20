# The Grand Art Spec

## Goal

Generate high-quality full-body character art first, then convert the approved art into faithful `100x100` sprites.

## Locked Direction

- Overall tone: cool-forward
- Female characters: cute when charming, beautiful with a slightly dangerous allure
- Proportions: about 5 heads tall
- Gender readability: mostly clear, with selected androgynous characters where intended
- Costume density: luxurious
- Sprite conversion: faithful `100x100`, not simplified chibi reinterpretation
- Background: fully transparent
- Asset framing: single character, full body, centered, slight three-quarter angle, readable silhouette

## High-Risk Rule

Do not run the full 10-character batch until the preview batch is approved.

Preview batch file:

- [tmp/imagegen/the_grand_preview_prompts.jsonl](/C:/Users/halki/Documents/New%20project/01_creative_projects/game_prototypes/pit_territory_web/tmp/imagegen/the_grand_preview_prompts.jsonl)

Full batch file:

- [tmp/imagegen/the_grand_prompts.jsonl](/C:/Users/halki/Documents/New%20project/01_creative_projects/game_prototypes/pit_territory_web/tmp/imagegen/the_grand_prompts.jsonl)

Budget batch file:

- [tmp/imagegen/the_grand_budget_prompts.jsonl](/C:/Users/halki/Documents/New%20project/01_creative_projects/game_prototypes/pit_territory_web/tmp/imagegen/the_grand_budget_prompts.jsonl)

## Character Notes

### Speed Star

- Fully enclosed mechanical exosuit
- Huge leg rollers
- Visible boost machinery
- Glowing chest or upper-back reactor core
- Broken body inside a machine built for reckless speed
- Larger and rounder mecha body, not a slim hero suit

### Myano Marly

- Japanese woman with black hair
- Wayo-gothic lolita yukata
- Purple and pink costume accents
- Cursed doll motif in hair ornament or obi ornament

### Acha-ji

- Old soldier, not a forest ranger
- Military-flavored archer silhouette
- White, black, and brown base colors
- Very large visible arrow reserves
- Lighter battlefield equipment, not coat-heavy
- Medieval-European soldier flavor rather than woodsman or robe

### Leo Alex

- Mostly plain soldier look
- One visible red hair streak for heroic bloodline

### Van Clarissa

- White hair mandatory
- Black long coat mandatory
- Deep crimson lining inside the coat
- Harsh, battle-hardened beauty
- Handgun should be clearly visible

### Saint Aria

- Ornate sacred blindfold cloth
- Elegant holy relic feel, not plain bandage

### Yume Shirahoshi

- Very cute psychic schoolgirl
- Visible electricity from both hands

### Kojiro Sakurai

- Iaido-only coolness
- No flashy effects
- Pure stillness and lethal refinement

### Nick

- Visible identification markings
- Huge restraint device on the right arm only

### Mei Sphin

- Androgynous beauty
- Gold hair and blue eyes mandatory
- Medieval leather outfit
- Hawk on shoulder mandatory
- Waist pouch for animal treats or tools
- Communication item for trust-building with animals
- No beast transformation design

## Recommended Run Order

1. Generate one character at a time when cost control matters
2. Start with `speed_star`
3. Then `leader`
4. Then `archer`
5. Only move forward after approval
6. Run the remaining characters after the style is stable
7. Convert approved PNGs to `100x100` sprites with:

```powershell
python tools\the_grand_sprite_pipeline.py --src-dir output\imagegen\the_grand\source --out-dir output\imagegen\the_grand\sprite100 --size 100
```

## Preview Batch Command

```powershell
python "C:\Users\halki\.codex\skills\.system\imagegen\scripts\image_gen.py" generate-batch --input "tmp\imagegen\the_grand_preview_prompts.jsonl" --out-dir "output\imagegen\the_grand\preview" --concurrency 3 --max-attempts 2
```

## Full Batch Command

```powershell
python "C:\Users\halki\.codex\skills\.system\imagegen\scripts\image_gen.py" generate-batch --input "tmp\imagegen\the_grand_prompts.jsonl" --out-dir "output\imagegen\the_grand\source" --concurrency 2 --max-attempts 2
```

## Budget Batch Command

```powershell
python "C:\Users\halki\.codex\skills\.system\imagegen\scripts\image_gen.py" generate-batch --input "tmp\imagegen\the_grand_budget_prompts.jsonl" --out-dir "output\imagegen\the_grand\budget" --concurrency 2 --max-attempts 2
```

## Cost Control

- Always preview first
- Keep concurrency moderate
- Regenerate only failed or off-spec characters
- Do not rerun the whole set after small spec changes
- Use the budget batch for broad direction checks before paying for higher-quality reruns
