import concurrent.futures
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from waitress import serve
from werkzeug.exceptions import Unauthorized

from definitions import REQUIRED_EXPORT_FIELDS
from utils import (
	allowed_file,
	convert_pdf_to_base64_images,
	extract_markdown_page,
	extract_product_label_information,
	validate_label_information,
	validate_label_translation_information,
	translate_label_fields,
	fill_and_save_config_json,
	generate_and_save_barcode,
	run_illustrator_script,
	stop_illustrator_script_task,
	is_illustrator_running,
)

app = Flask(__name__)

FLASK_TOKEN = os.environ.get("FLASK_TOKEN") or 'GsLT8RuQkjWv06ZdNj0ybdfmE31wU6GI89lWbaIJ1u32WjvMPO'

# Define base directory of the script
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SCRIPT_FOLDER'] = os.path.join(BASE_DIR, 'illustrator_script')
app.config['LABELS_FOLDER'] = os.path.join(app.config['SCRIPT_FOLDER'], 'labels')
app.config['TEMP_FOLDER'] = os.path.join(app.config['SCRIPT_FOLDER'], 'temp')
app.config['OUTPUT_FOLDER'] = os.path.join(app.config['TEMP_FOLDER'], 'output')

os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

#export_lock = threading.Lock()

# Enable CORS
CORS(app)

def token_required(f):
	@wraps(f)
	def decorator(*args, **kwargs):
		if 'Token' in request.headers:
			token = request.headers['Token']
			if token != FLASK_TOKEN:
				raise Unauthorized(description="a valid token is missing")
		else:
			raise Unauthorized(description="a valid token is missing")
		return f(*args, **kwargs)

	return decorator

def clean_output_folder():
	"""Delete all files in the output folder."""
	for file in os.listdir(app.config['OUTPUT_FOLDER']):
		file_path = os.path.join(app.config['OUTPUT_FOLDER'], file)
		try:
			os.remove(file_path)
		except Exception as e:
			print(f"Error deleting file {file_path}: {str(e)}", flush=True)


@app.route('/labels', methods=['GET'])
@token_required
def get_labels():
	labels_folder = app.config['LABELS_FOLDER']

	# Check if the folder exists
	if not os.path.isdir(labels_folder):
		return jsonify({'error': 'Labels folder does not exist'}), 400

	# Get all .ai files
	ai_files = [f for f in os.listdir(labels_folder) if f.endswith('.ai')]

	# Check if the folder contains .ai files
	if not ai_files:
		return jsonify({'error': 'No .ai files found'}), 400

	# Remove .ai extension from file names
	labels = [os.path.splitext(f)[0] for f in ai_files]

	return jsonify(labels), 200


@app.route('/upload', methods=['POST'])
@token_required
def upload_file():
	if 'pdf_file' not in request.files:
		return jsonify({'error': 'No file part in the request'}), 400

	file = request.files['pdf_file']

	if file.filename == '':
		return jsonify({'error': 'Empty filename'}), 400

	if file and allowed_file(file.filename):
		pdf_bytes = file.read()
		print("Converting pdf to base64 images", flush=True)
		base64_images = convert_pdf_to_base64_images(pdf_bytes)
		print("Converted base64 images", flush=True)

		print("Extracting Markdown pages", flush=True)
		with ThreadPoolExecutor() as executor:
			markdown_pages = list(executor.map(extract_markdown_page, base64_images))
		print("Extracted Markdown pages", flush=True)

		for attempt in range(5):
			try:
				print(f"Attempt {attempt + 1}: Extracting product label information", flush=True)
				product_label_information = extract_product_label_information(markdown_pages)

				if validate_label_information(product_label_information):
					json_result = jsonify(product_label_information.model_dump())
					return json_result
				else:
					print(f"Validation failed on attempt {attempt + 1}", flush=True)
			except Exception as e:
				print(f"Error on attempt {attempt + 1}: {str(e)}", flush=True)

		return jsonify({'error': 'Failed to extract valid product label information after 5 attempts'}), 500


@app.route('/export', methods=['POST'])
@token_required
def export_file():
	#if not export_lock.acquire(blocking=False):
	#	return jsonify({"error": "Export process is currently running. Please try again later."}), 429
	try:
		json_data = request.get_json()

		if json_data is None:
			return jsonify({"error": "No JSON data provided"}), 400

		missing_fields = REQUIRED_EXPORT_FIELDS - json_data.keys()
		if missing_fields:
			return jsonify({"error": "Missing fields", "missing_fields": list(missing_fields)}), 400

		label_path = os.path.join(app.config['LABELS_FOLDER'], json_data["label_size"] + '.ai')
		if not os.path.exists(label_path):
			return jsonify({"error": "Label file not found", "path": label_path}), 404

		# Clean output folder and delete old config file
		clean_output_folder()

		config_path = os.path.join(app.config['TEMP_FOLDER'], 'config.json')
		if os.path.exists(config_path):
			os.remove(config_path)

		barcode_path = os.path.join(app.config['TEMP_FOLDER'], 'barcode.eps')
		if os.path.exists(barcode_path):
			os.remove(barcode_path)

		main_language = json_data.get("main_language", "DE")
		if main_language not in ("DE", "EN"):
			return jsonify({"error": "Invalid main_language. Must be 'DE' or 'EN'."}), 400

		target_languages = ["french", "italian", "spanish", "dutch"]
		if main_language == "EN":
			target_languages.append("english")

		def translate_with_retries(data, language):
			for attempt in range(5):
				try:
					print(f"Attempt {attempt + 1}: Translating to {language}", flush=True)
					translation_result = translate_label_fields(data, language)

					if validate_label_translation_information(translation_result):
						return translation_result
					else:
						print(f"Validation failed for {language} on attempt {attempt + 1}", flush=True)
				except Exception as e:
					print(f"Error translating to {language} on attempt {attempt + 1}: {str(e)}", flush=True)

			raise ValueError(f"Failed to produce a valid translation for {language} after 5 attempts")

		with concurrent.futures.ThreadPoolExecutor() as executor:
			future_to_language = {executor.submit(translate_with_retries, json_data, lang): lang for lang in
								  target_languages}
			results = {future_to_language[future]: future.result() for future in
					   concurrent.futures.as_completed(future_to_language)}

		base_languages = ["french", "italian", "spanish", "dutch"]
		if any("error" in results[lang] for lang in target_languages):
			return jsonify({"error": "Failed to translate to all target languages", "details": results}), 500

		main_data_override = results["english"].model_dump() if main_language == "EN" else None

		fill_and_save_config_json(config_path, json_data, *[results[lang].model_dump() for lang in base_languages],
								  main_language=main_language, main_data_override=main_data_override)

		generate_and_save_barcode(json_data['barcode'], barcode_path)

		illustrator_script_path = os.path.join(app.config['SCRIPT_FOLDER'], 'script.jsx')
		run_illustrator_script(illustrator_script_path)

		timeout = 1200  # Wait up to 20 minutes for the AI file to be generated
		startup_grace = 30  # Wait up to 30 seconds for Illustrator to launch
		output_filename = "output.ai"
		output_folder = app.config['OUTPUT_FOLDER']
		ai_file_path = os.path.join(output_folder, output_filename)

		# Wait for Illustrator to start before monitoring
		while startup_grace > 0 and not is_illustrator_running():
			if os.path.exists(ai_file_path):
				break
			time.sleep(1)
			startup_grace -= 1
			print(f"Waiting for Illustrator to start... ({30 - startup_grace}s)", flush=True)

		while timeout > 0:
			if os.path.exists(ai_file_path):
				print("output file detected", flush=True)
				print(ai_file_path, flush=True)
				return send_file(ai_file_path, mimetype="application/octet-stream", as_attachment=True,
								 download_name=output_filename)
			if not is_illustrator_running():
				return jsonify({"error": "Illustrator closed unexpectedly. Please try again."}), 500
			time.sleep(1)
			timeout -= 1

		return jsonify({"error": "AI file not found after processing"}), 500

	except Exception as e:
		print(f"Export error: {str(e)}", flush=True)
		return jsonify({"error": str(e)}), 500

	finally:
		illustrator_script_path = os.path.join(app.config['SCRIPT_FOLDER'], 'script.jsx')
		stop_illustrator_script_task(illustrator_script_path)
		#export_lock.release()


if os.getenv('HTTP_PLATFORM_PORT'):
	serve(app, host='0.0.0.0', port=os.getenv('HTTP_PLATFORM_PORT'))  # Port is overridden by IIS
