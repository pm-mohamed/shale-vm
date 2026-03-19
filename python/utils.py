# ============================================================================
# DO NOT MODIFY THIS FILE
# This is a read-only archive of the original utils.py from the old virtual machine.
# It exists solely as a historical reference. All changes should be made in
# backend/new-vm-utils.py (current VM code) or backend/utils.py (production code).
# ============================================================================

import os
import re
import subprocess
import psutil
from io import BytesIO
from pydantic import BaseModel
import pymupdf
import base64
import json
import cairosvg
import xml.etree.ElementTree as ET
from barcode import Code128
from openai import OpenAI

from definitions import (
	MARKDOWN_EXTRACTION_PROMPT,
	PRODUCT_LABEL_EXTRACTION_PROMPT_TEMPLATE,
	STANDARD_INGREDIENT_WARNING,
	get_translation_prompt,
	get_config
)

# OpenAI API Key
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)


class ProductLabel(BaseModel):
	verzehrsempfehlung: str
	inhaltsstoffe: str
	inhaltsstoffe_fussnoten: str
	empfohlene_tagesdosis: str
	zutaten: str
	warnhinweise: str


class TranslationFields(BaseModel):
	supplement_purpose: str
	consumption_recommendation: str
	ingredients_table: str
	ingredients_table_footnotes: str
	recommended_daily_dose: str
	ingredients_list: str
	warnings: str
	quantity: str


def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


def convert_pdf_to_base64_images(pdf_file_bytes):
	pdf_document = pymupdf.open("pdf", BytesIO(pdf_file_bytes))
	base64_images = []

	for page_num in range(len(pdf_document)):
		page = pdf_document.load_page(page_num)
		# Render the page to a pixmap
		pixmap = page.get_pixmap(dpi=150)
		# Convert pixmap to a PNG image
		img_bytes = pixmap.tobytes("png")
		# Encode the PNG image to base64
		img_base64 = base64.b64encode(img_bytes).decode('utf-8')
		# Append the base64 image string to the list
		base64_images.append(img_base64)

	pdf_document.close()
	return base64_images


def format_markdown_pages(markdown_pages):
	formatted_pages = []

	for i, content in enumerate(markdown_pages, start=1):
		formatted_pages.append(f"## Page {i}\n\n{content.strip()}")

	return "\n\n".join(formatted_pages)


def extract_markdown_page(base64_image):
	response = client.chat.completions.create(
		model="gpt-4o",
		messages=[
			{
				"role": "user",
				"content": [
					{
						"type": "text",
						"text": MARKDOWN_EXTRACTION_PROMPT
					},
					{
						"type": "image_url",
						"image_url": {
							"url": f"data:image/jpeg;base64,{base64_image}"
						},
					}
				]
			}
		]
	)
	return response.choices[0].message.content


def extract_product_label_information(markdown_pages):
	formatted_markdown_pages = format_markdown_pages(markdown_pages)

	completion = client.beta.chat.completions.parse(
		model="gpt-4o-2024-08-06",
		messages=[
			{
				"role": "user",
				"content": [
					{
						"type": "text",
						"text": PRODUCT_LABEL_EXTRACTION_PROMPT_TEMPLATE.format(
							markdown_input=formatted_markdown_pages),
					}
				],
			}
		],
		response_format=ProductLabel,
	)

	label_information = completion.choices[0].message.parsed
	format_ingredient_warnings(label_information)
	format_ingredients_table(label_information)
	format_ingredients_table_footnotes(label_information)

	return label_information


def translate_label_fields(input_data, target_language):
	translation_prompt = get_translation_prompt(input_data, target_language)

	completion = client.beta.chat.completions.parse(
		model="gpt-4o-2024-08-06",
		messages=[
			{
				"role": "user",
				"content": [
					{
						"type": "text",
						"text": translation_prompt,
					}
				],
			}
		],
		response_format=TranslationFields,
	)

	return completion.choices[0].message.parsed


def validate_label_information(product_label_information):
	lines = product_label_information.inhaltsstoffe.splitlines()
	non_empty_lines = [line for line in lines if line.strip()]
	return len(non_empty_lines) >= 2


def validate_label_translation_information(product_label_information):
	lines = product_label_information.ingredients_table.splitlines()
	non_empty_lines = [line for line in lines if line.strip()]
	return len(non_empty_lines) >= 2


def format_ingredient_warnings(product_label_information):
	ingredient_warnings = product_label_information.warnhinweise
	# Remove empty lines and join everything into a single line with spaces
	cleaned_warnings = " ".join(line.strip() for line in ingredient_warnings.splitlines() if line.strip())
	product_label_information.warnhinweise = (
												 cleaned_warnings + " " if cleaned_warnings else "") + STANDARD_INGREDIENT_WARNING


def format_ingredients_table(product_label_information):
	ingredients_table = product_label_information.inhaltsstoffe
	formatted_ingredients_table = re.sub(r'\b(davon)', r'  \1', ingredients_table)
	product_label_information.inhaltsstoffe = formatted_ingredients_table


def format_ingredients_table_footnotes(product_label_information):
	ingredients_table = product_label_information.inhaltsstoffe
	ingredients_table_footnotes = product_label_information.inhaltsstoffe_fussnoten.strip()

	if "***" in ingredients_table:
		ingredients_table_footnotes += "\n*** Keine Nährstoffbezugswerte bekannt"

	# cleanup any potential superscript artifacts
	ingredients_table_footnotes = re.sub(r'(\*+)\d*', r'\1', ingredients_table_footnotes)

	product_label_information.inhaltsstoffe_fussnoten = ingredients_table_footnotes


def fill_and_save_config_json(config_path, input_data, input_data_french, input_data_italian, input_data_spanish,
							  input_data_dutch):
	config = get_config(input_data, input_data_french, input_data_italian, input_data_spanish, input_data_dutch)

	try:
		with open(config_path, "w", encoding="utf-8") as json_file:
			json.dump(config, json_file, indent=4, ensure_ascii=False)
		print(f"Configuration successfully saved to {config_path}", flush=True)
	except Exception as e:
		print(f"An error occurred while saving the configuration: {e}", flush=True)


def is_valid_barcode(barcode):
	return barcode and barcode.strip()


def remove_light_margin_indicator_from_barcode(svg_path):
	tree = ET.parse(svg_path)
	root = tree.getroot()
	removed_x = None
	ns = '{http://www.w3.org/2000/svg}'

	for parent in root.iter():
		for child in list(parent):
			if child.tag == ns + 'text' and child.text == '>':
				removed_x = child.attrib.get('x')
				parent.remove(child)
				break
		if removed_x is not None:
			break

	if removed_x is not None:
		root.attrib['width'] = removed_x

	tree.write(svg_path)


def generate_and_save_barcode(barcode, barcode_path):
	if not is_valid_barcode(barcode):
		raise ValueError("The barcode must not be empty.")

	temp_svg_filepath = barcode_path.replace(".eps", ".svg")
	temp_svg_filename = os.path.splitext(temp_svg_filepath)[0]

	code128 = Code128(barcode)
	options = dict(module_width=0.4)
	code128.save(temp_svg_filename, options)

	remove_light_margin_indicator_from_barcode(temp_svg_filepath)

	try:
		cairosvg.svg2eps(url=temp_svg_filepath, write_to=barcode_path)
		print(f"Barcode saved as {barcode_path}")

	finally:
		if os.path.exists(temp_svg_filepath):
			os.remove(temp_svg_filepath)


def run_illustrator_script(script_path):
	print("Triggering Illustrator via Task Scheduler...", flush=True)
	try:
		# Run the task we created manually
		subprocess.run(["schtasks", "/run", "/tn", "RunIllustratorScript"], shell=True, check=True)
		print("Illustrator script execution triggered.", flush=True)
	except subprocess.CalledProcessError as e:
		print(f"Error triggering task: {e}", flush=True)
		raise


def stop_illustrator_script_task(script_path):
	print("Stopping Illustrator Task...", flush=True)
	try:
		# Run the task we created manually
		subprocess.run(["schtasks", "/end", "/tn", "RunIllustratorScript"], shell=True, check=True)
		print("Task stopped in Task Scheduler.", flush=True)
	except subprocess.CalledProcessError as e:
		print(f"Error triggering/stopping task: {e}", flush=True)
		raise


def is_illustrator_running():
	for process in psutil.process_iter(['pid', 'name']):
		if process.info['name'] and "illustrator" in process.info['name'].lower():
			return True
	return False
