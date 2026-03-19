# definitions.py

STANDARD_INGREDIENT_WARNING = "Die angegebene empfohlene tägliche Verzehrmenge darf nicht überschritten werden. Nahrungsergänzungsmittel dürfen nicht als Ersatz für eine ausgewogene, abwechslungsreiche Ernährung und eine gesunde Lebensweise verwendet werden. Für Kinder und Jugendliche nicht geeignet. Geschlossen, kühl, trocken und außerhalb der Reichweite von Kindern aufbewahren. Nicht für Schwangere und Stillende geeignet."

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

MARKDOWN_EXTRACTION_PROMPT = """You are an expert in text extraction and Markdown formatting for medicine or dietary supplements. Your task is to convert the content of the provided image of a PDF page into **accurate and structured Markdown**. All text, tables, headings, bullet points, and formatting should be **precisely** extracted and represented in Markdown without any alterations or omissions.

---

## Instructions:

### Your Task:
Extract and convert all content from the provided image into structured Markdown:
- **Headings**: Use proper Markdown syntax (`#`, `##`, etc.).
- **Text**: Reproduce all plain text exactly as it appears.
- **Lists**: Convert numbered and bulleted lists using `-` for bullets and `1.` for numbers.
- **Tables**: Represent tables using proper Markdown table syntax (note: "%NRV" should always be represented in a separate column):
  | Nährstoff                | Pro 100 g             | NRV%** | Einzelportion (1.293,8 mg) | NRV%** | Tagesportion (7.762,8 mg)* | NRV%** |
  |--------------------------|-----------------------|--------|----------------------------|--------|----------------------------|---------|
  | L-Citrullin-DL-Malat 2:1 | 44.891 mg             |        | 581 mg                     |        | 3.485 mg                   |         |
  | davon L-Citrullin        | 28.057 mg             |        | 363 mg                     |        | 2.178 mg                   |         |
- **Line Breaks**: Use `\n` to separate paragraphs or preserve intentional spacing.
- **Bold/Italic**: Use `**bold**` or `*italic*` for any stylized text.

### What to Exclude:
- Do **not** extract any introductory content at the very top of the document (like titles and descriptions).
- Do **not** extract any additional details, branding, logos, or addresses found at the very bottom of the document.
- Do **not** include illegible content. If any text is unclear, mark it clearly as `[Unclear: ...]`.

### Accuracy:
Ensure that every part of the main page content is extracted **exactly as it appears** in the image:
- Do **not** summarize, omit, or alter content.

### Output Format:
Return **only** the extracted content strictly in **plain Markdown syntax**.
- Do **not** wrap the Markdown in code blocks or provide any explanations, comments, or additional text."""

PRODUCT_LABEL_EXTRACTION_PROMPT_TEMPLATE = """## Instruction:

You will extract specific structured information from the given Markdown input, which describes a medicine or dietary supplement. The extracted information should be presented in a structured JSON format in **German**.

- Ensure that all fields are filled accurately based on the input content.
- If a field is not present in the input, leave it empty.
- The field **"inhaltsstoffe"** must be extracted from the **"Nährwerte"** section in the input.
  - This field should only include the table-like structure of the ingredients:
  	- The table must only include information for the **daily portion** and its corresponding **NRV%** values (or **single portion** if daily is not provided).
    - Each cell is separated by a **tab** (`\t`).
    - Each row is separated by a **line break** (`\n`).
    - The table must always include three columns with the following names: "Inhaltsstoffe", "Pro Tagesportion*" or "Pro Einzelportion*", and "NRV%**".
    - The column "NRV%**" must include "***" as a placeholder for any cell where no value is provided.
    - Any gram numbers or other measurements in the column headers should be removed.
- The field **"inhaltsstoffe_fussnoten"** must be extracted separately and include only the explanatory text for the asterisks ("*", "**", ...) from the **"Nährwerte"** section.
	- The extracted text should begin with *, **, or other asterisk-based markers but should not include numerical superscripts (e.g., ¹, ²).
- The field **"empfohlene_tagesdosis"** can oftentimes be extracted from the explanatory text for the asterisks. If the information can't be found, use an empty string.
- The field **"zutaten"** must be extracted from the **"Zutatenliste"** section in the input.
- The field **"warnhinweise"** must be extracted from the **"Warnhinweise"** section in the input. If the section **"Warnhinweise"** is not present, leave the string empty.

### Example Output:
{{
  "verzehrsempfehlung": "6 Kapseln pro Tag mit reichlich Wasser einnehmen.",
  "inhaltsstoffe": "Nährstoff\tPro Tagesportion*\tNRV%**\nL-Citrullin-DL-Malat 2:1\t3.485 mg\t***\ndavon L-Citrullin\t2.178 mg\t***",
  "inhaltsstoffe_fussnoten": "* 6 Kapseln pro Tag mit reichlich Wasser einnehmen.\n** Prozentsatz %NRV der Nährstoffbezugswerte (Nutrient Reference Values) nach Verordnung (EU) Nr. 1169/2011.",
  "empfohlene_tagesdosis": "6 Kapseln",
  "zutaten": "L-Citrullin-DL-Malat 2:1, L-Arginin, Hydroxypropylmethylcellulose",
  "warnhinweise": "Das Produkt ist für Schwangere nicht geeignet."
}}

### Input Section:
### BEGIN_MARKDOWN
{markdown_input}
### END_MARKDOWN

### Notes:
- The output must strictly follow the JSON structure provided above.
- If a section is missing in the input, ensure the corresponding field in the JSON is empty.
- Pay attention to the formatting of German text (e.g., umlauts, capitalization).
- The **"Nährwerte"** section must be used to extract the **"inhaltsstoffe"** and **"inhaltsstoffe_fussnoten"** fields as described above.
- The **"Zutatenliste"** section must be used to extract the **"zutaten"** field.
- The **"Warnhinweise"** section must be used to extract the **"warnhinweise"** field if its there."""

REQUIRED_EXPORT_FIELDS = {
    "label_size",
	"barcode",
    "product_name",
    "key_features",
    "additional_info",
    "supplement_purpose",
	"consumption_recommendation",
	"ingredients_table",
	"ingredients_table_footnotes",
	"recommended_daily_dose",
	"ingredients_list",
	"warnings",
	"quantity",
	"net_weight"
}

def get_translation_prompt(input_data, target_language):
	return f"""You are an expert language translator and JSON processor. Your task is to translate the values in a JSON object into a target language while keeping the keys untouched and preserving the exact format of the value strings.

### Instructions:
1. **Do not modify the keys of the JSON object.**
2. **Only translate the values into the target language.**
3. **Maintain the formatting within the value strings, including special characters, new line characters, tabs, whitespace and punctuation.**
4. **If a value contains technical terms, leave them untranslated unless they have a widely accepted equivalent in the target language.**

### shortened Input JSON Example:
{{
  "ingredients_table": "Inhaltsstoffe\tPro Einzelportion*\tNRV%\n**Biotin\t10.000 µg\t20000\nZink\t10 mg\t100\nSelen\t55 µg\t100",
  "ingredients_list": "Akazienfaser, Zinkbisglycinat, D-Biotin, Selenhefe, L-Selenomethionin, Natriumselenit",
}}

### Expected shortened Output in Spanish:
{{
  "ingredients_table": "Componentes\tPor porción única*\tVRN%**\nBiotina\t10.000 µg\t20000\nZinc\t10 mg\t100\nSelenio\t55 µg\t100",
  "ingredients_list": "Fibra de acacia, Bisglicinato de zinc, D-Biotina, Levadura de selenio, L-Seleniometionina, Selenito de sodio",
}}

---

###Target Language:
{target_language}

###Input
{{
  "supplement_purpose": {input_data["supplement_purpose"]},
  "consumption_recommendation": {input_data["consumption_recommendation"]},
  "ingredients_table": {input_data["ingredients_table"]},
  "ingredients_table_footnotes": {input_data["ingredients_table_footnotes"]},
  "recommended_daily_dose": {input_data["recommended_daily_dose"]},
  "ingredients_list": {input_data["ingredients_list"]},
  "warnings": {input_data["warnings"]},
  "quantity": {input_data["quantity"]}
}}"""

def get_config(input_data, input_data_french, input_data_italian, input_data_spanish, input_data_dutch, main_language="DE", main_data_override=None):
	layout_data = main_data_override if main_data_override else input_data
	ingredients_table_column_names, ingredients_table_cells = layout_data["ingredients_table"].split('\n', 1)
	ingredients_table_column_names_french, ingredients_table_cells_french = input_data_french[
		"ingredients_table"].split('\n', 1)
	ingredients_table_column_names_italian, ingredients_table_cells_italian = input_data_italian[
		"ingredients_table"].split('\n', 1)
	ingredients_table_column_names_spanish, ingredients_table_cells_spanish = input_data_spanish[
		"ingredients_table"].split('\n', 1)
	ingredients_table_column_names_dutch, ingredients_table_cells_dutch = input_data_dutch["ingredients_table"].split(
		'\n', 1)

	return {
		"labelSize": input_data["label_size"],
		"layers": [
			{
				"name": "Logo",
				"groups": [
					{
						"name": "MainLogoGroup",
						"textFrames": [
							{
								"name": "ProductName",
								"content": input_data["product_name"]
							},
							{
								"name": "AdditionalInfo",
								"content": input_data["additional_info"]
							},
							{
								"name": "KeyFeatures",
								"content": input_data["key_features"]
							}
						]
					}
				]
			},
			{
				"name": "Layout",
				"groups": [
					{
						"name": "IngredientsTableGroup",
						"textFrames": [
							{
								"name": "IngredientsTableColumnNames",
								"content": ingredients_table_column_names
							},
							{
								"name": "IngredientsTableCells",
								"content": ingredients_table_cells
							},
							{
								"name": "IngredientsTableFootnotes",
								"content": layout_data["ingredients_table_footnotes"]
							}
						]
					},
					{
						"name": "MeasurementGroup",
						"groups": [
							{
								"name": "WeightGroup",
								"textFrames": [
									{
										"name": "NetWeight",
										"content": input_data["net_weight"]
									}
								]
							}
						],
						"textFrames": [
							{
								"name": "Quantity",
								"content": layout_data["quantity"]
							}
						]
					}
				],
				"textFrames": [
					{
						"name": "SupplementPurpose",
						"content": layout_data["supplement_purpose"]
					},
					{
						"name": "IngredientsList",
						"prefix": LANGUAGE_PREFIXES[main_language]["ingredients_list"],
						"content": layout_data["ingredients_list"]
					},
					{
						"name": "Guidelines",
						"content": LANGUAGE_PREFIXES[main_language]["consumption_recommendation"] + layout_data["consumption_recommendation"] + "\n\n" + LANGUAGE_PREFIXES[main_language]["warnings"] + layout_data["warnings"] + "\n\n" + LANGUAGE_PREFIXES[main_language]["lot_info"]
					}
				]
			},
			{
				"name": "Languages",
				"groups": [
					{
						"name": "FrGroup",
						"textFrames": [
							{
								"name": "IngredientsTableColumnNames",
								"content": ingredients_table_column_names_french
							},
							{
								"name": "IngredientsTableCells",
								"content": ingredients_table_cells_french
							},
							{
								"name": "IngredientsTableFootnotes",
								"content": input_data_french["ingredients_table_footnotes"]
							},
							{
								"name": "Quantity",
								"content": input_data_french["quantity"]
							},
							{
								"name": "NetWeight",
								"content": input_data["net_weight"]
							},
							{
								"name": "SupplementPurpose",
								"content": input_data_french["supplement_purpose"]
							},
							{
								"name": "IngredientsList",
								"prefix": "Ingrédients: ",
								"content": input_data_french["ingredients_list"]
							},
							{
								"name": "ConsumptionRecommendation",
								"prefix": "Mode d’emploi: ",
								"content": input_data_french["consumption_recommendation"]
							},
							{
								"name": "Warnings",
								"prefix": "Avertissement: ",
								"content": input_data_french["warnings"]
							},
							{
								"name": "RecommendedDailyDose",
								"prefix": "Dose journalière recommandée: ",
								"content": input_data_french["recommended_daily_dose"]
							}
						]
					},
					{
						"name": "ItGroup",
						"textFrames": [
							{
								"name": "IngredientsTableColumnNames",
								"content": ingredients_table_column_names_italian
							},
							{
								"name": "IngredientsTableCells",
								"content": ingredients_table_cells_italian
							},
							{
								"name": "IngredientsTableFootnotes",
								"content": input_data_italian["ingredients_table_footnotes"]
							},
							{
								"name": "Quantity",
								"content": input_data_italian["quantity"]
							},
							{
								"name": "NetWeight",
								"content": input_data["net_weight"]
							},
							{
								"name": "SupplementPurpose",
								"content": input_data_italian["supplement_purpose"]
							},
							{
								"name": "IngredientsList",
								"prefix": "Ingredienti: ",
								"content": input_data_italian["ingredients_list"]
							},
							{
								"name": "ConsumptionRecommendation",
								"prefix": "Modalita' d'uso: ",
								"content": input_data_italian["consumption_recommendation"]
							},
							{
								"name": "Warnings",
								"prefix": "Avvertenze: ",
								"content": input_data_italian["warnings"]
							},
							{
								"name": "RecommendedDailyDose",
								"prefix": "Dose giornaliera raccomandata: ",
								"content": input_data_italian["recommended_daily_dose"]
							}
						]
					},
					{
						"name": "EsGroup",
						"textFrames": [
							{
								"name": "IngredientsTableColumnNames",
								"content": ingredients_table_column_names_spanish
							},
							{
								"name": "IngredientsTableCells",
								"content": ingredients_table_cells_spanish
							},
							{
								"name": "IngredientsTableFootnotes",
								"content": input_data_spanish["ingredients_table_footnotes"]
							},
							{
								"name": "Quantity",
								"content": input_data_spanish["quantity"]
							},
							{
								"name": "NetWeight",
								"content": input_data["net_weight"]
							},
							{
								"name": "SupplementPurpose",
								"content": input_data_spanish["supplement_purpose"]
							},
							{
								"name": "IngredientsList",
								"prefix": "Ingredientes: ",
								"content": input_data_spanish["ingredients_list"]
							},
							{
								"name": "ConsumptionRecommendation",
								"prefix": "Modo de empleo: ",
								"content": input_data_spanish["consumption_recommendation"]
							},
							{
								"name": "Warnings",
								"prefix": "Advertencias: ",
								"content": input_data_spanish["warnings"]
							},
							{
								"name": "RecommendedDailyDose",
								"prefix": "Dosis diaria recomendada: ",
								"content": input_data_spanish["recommended_daily_dose"]
							}
						]
					},
					{
						"name": "NlGroup",
						"textFrames": [
							{
								"name": "IngredientsTableColumnNames",
								"content": ingredients_table_column_names_dutch
							},
							{
								"name": "IngredientsTableCells",
								"content": ingredients_table_cells_dutch
							},
							{
								"name": "IngredientsTableFootnotes",
								"content": input_data_dutch["ingredients_table_footnotes"]
							},
							{
								"name": "Quantity",
								"content": input_data_dutch["quantity"]
							},
							{
								"name": "NetWeight",
								"content": input_data["net_weight"]
							},
							{
								"name": "SupplementPurpose",
								"content": input_data_dutch["supplement_purpose"]
							},
							{
								"name": "IngredientsList",
								"prefix": "Ingrediënten: ",
								"content": input_data_dutch["ingredients_list"]
							},
							{
								"name": "ConsumptionRecommendation",
								"prefix": "Gebruiksaanwijzing: ",
								"content": input_data_dutch["consumption_recommendation"]
							},
							{
								"name": "Warnings",
								"prefix": "Waarschuwingen: ",
								"content": input_data_dutch["warnings"]
							},
							{
								"name": "RecommendedDailyDose",
								"prefix": "Aanbevolen dagelijkse dosis: ",
								"content": input_data_dutch["recommended_daily_dose"]
							}
						]
					}
				]
			}
		]
	}
