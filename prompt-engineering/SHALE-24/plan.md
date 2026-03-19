 SHALE-24: Main Label Language Selection (DE / EN)                                                                                                                                                                                               
 Context

 The main label (Logo + Layout layers in Illustrator) is currently hardcoded to German. The business is expanding to the UK market, so users need the option to export the main label in English. When English is selected, the German-extracted
  data will be translated to English via GPT-4o (same pipeline as FR/IT/ES/NL), and the Layout layer will use English text and prefixes.

 Approach

 1. Backend: Add language prefix mapping (definitions.py)

 Add a LANGUAGE_PREFIXES dict after STANDARD_INGREDIENT_WARNING (line 3):

 LANGUAGE_PREFIXES = {
     "DE": {
         "ingredients_list": "Zutaten: ",
         "consumption_recommendation": "Verzehrempfehlung: ",
         "warnings": "Hinweise: ",
         "lot_info": "Lot Nr./ Mindestens haltbar bis Ende:\nSiehe Bodenaufdruck",
     },
     "EN": {
         "ingredients_list": "Ingredients: ",
         "consumption_recommendation": "Consumption recommendation: ",
         "warnings": "Warnings: ",
         "lot_info": "Lot No./ Best before end:\nSee bottom imprint",
     },
 }

 2. Backend: Modify get_config() (definitions.py:135)

 - Add parameters: main_language="DE", main_data_override=None
 - Create layout_data = main_data_override if main_data_override else input_data
 - Split layout_data["ingredients_table"] (not input_data) for the Layout layer table
 - Replace all input_data[...] references in the Layout layer (lines 172-227) with layout_data[...]
 - Replace hardcoded German prefixes with LANGUAGE_PREFIXES[main_language] lookups
 - Logo layer (lines 150-169) stays using input_data (brand names, user-entered)
 - Languages layer (lines 228-427) stays completely unchanged

 3. Backend: Modify /export endpoint (app.py:131)

 - Extract main_language = json_data.get("main_language", "DE") (optional, backward-compatible)
 - Validate: must be "DE" or "EN"
 - If "EN": add "english" to the target_languages list so it runs in parallel with FR/IT/ES/NL
 - After translation results collected: main_data_override = results["english"].model_dump() if EN
 - Pass main_language and main_data_override through to fill_and_save_config_json()

 4. Backend: Update fill_and_save_config_json() (utils.py:200)

 - Add main_language="DE" and main_data_override=None parameters
 - Pass them through to get_config()

 5. Frontend: SSR file (nuxt/server/chunks/build/upload-DAKQfgSN.mjs)

 In the Step2 component (_sfc_main$3, line 5213):
 - setup(): Add mainLanguage = ref("Deutsch") and mainLanguageOptions = ["Deutsch", "English"]
 - handleExport(): Add main_language: mainLanguage.value === "English" ? "EN" : "DE" to labelObject
 - return: Expose mainLanguage, mainLanguageOptions
 - SSR render: Add a USelectMenu dropdown labeled "Hauptsprache" in the same row as Etikettengröße (after label size, before barcode row)

 6. Frontend: Client bundle (nuxt/public/_nuxt/CAFrQbEf.js)

 Mirror the same changes in the minified client-side JS:
 - Add mainLanguage ref and options
 - Add main_language to the labelObject
 - Add USelectMenu rendering for the dropdown

 Files to Modify

 ┌──────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────┐
 │                     File                     │                                Change                                │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ python/definitions.py                        │ Add LANGUAGE_PREFIXES; modify get_config() for language-aware Layout │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ python/app.py                                │ Add main_language handling; conditional EN translation in parallel   │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ python/utils.py                              │ Update fill_and_save_config_json() signature                         │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ nuxt/server/chunks/build/upload-DAKQfgSN.mjs │ Add language dropdown + include in export payload                    │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────┤
 │ nuxt/public/_nuxt/CAFrQbEf.js                │ Mirror frontend changes in client bundle                             │
 └──────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────┘

 Key Design Decisions

 - main_language is optional (defaults to "DE") — full backward compatibility
 - Logo layer (ProductName, AdditionalInfo, KeyFeatures) NOT translated — these are brand names/user-entered
 - English translation runs in parallel with FR/IT/ES/NL — zero extra wall-clock time
 - REQUIRED_EXPORT_FIELDS not modified — main_language is optional

 Verification

 1. DE (default): Export without main_language field → same behavior as before
 2. DE (explicit): Export with main_language: "DE" → same as default
 3. EN: Export with main_language: "EN" → Layout layer shows English text, English prefixes ("Ingredients:", "Warnings:", etc.), Logo stays as user-entered, Languages layer (FR/IT/ES/NL) unchanged
 4. Test the UI dropdown appears and persists selection
 5. Verify the generated config.json has correct English content in Layout layer