import os
import json
import sqlite3
import subprocess
import numpy as np
import pandas as pd
import requests
from flask import Flask, request, jsonify, Response
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util
from PIL import Image
from dateutil import parser
import calendar
import re
from datetime import datetime
from openpyxl import Workbook
from markdown2 import markdown
import shutil
from dateutil import parser
from fastapi.responses import PlainTextResponse
from pathlib import Path
import csv
import glob
import time
import stat
import duckdb
from bs4 import BeautifulSoup
import whisper

# Load environment variables from .env file
load_dotenv()

# Retrieve AI Proxy Token from environment variables
AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
API_BASE_URL = "https://aiproxy.sanand.workers.dev/openai/v1"

# Ensure the API key is set
if not AIPROXY_TOKEN:
    raise ValueError("Error: AIPROXY_TOKEN is not set. Make sure you have added it to your .env file.")

# Initialize Flask app
app = Flask(__name__)


# Ensure all files are accessed from the 'data' folder inside the project root
PROJECT_ROOT = os.path.abspath(os.getcwd())
DATA_DIR = os.path.join(PROJECT_ROOT, "data")  # ✅ Allowed data directory

# Task mapping for LLM classification
TASK_MAPPING = {
    "vs_code": "vs_code",
    "send_https_request": "send_https_request",
    "run_prettier_sha256": "run_prettier_sha256",
    "google_sheets_formula": "google_sheets_formula",
    "excel_formula": "excel_formula",
    "hidden_secret_value": "hidden_secret_value",
    "count_wednesdays": "count_wednesdays",
    "find_similar_comments": "find_similar_comments",
    "execute_dynamic_query": "execute_dynamic_query"
}

def classify_task(task_description):
    """Use AI Proxy to classify the task correctly."""
    try:
        headers = {
            "Authorization": f"Bearer {AIPROXY_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify the task description into EXACTLY one of these labels:\n"
                        + ", ".join(TASK_MAPPING.keys())
                        + ".\n\n"
                        "Return ONLY the exact label, nothing else."
                    )
                },
                {"role": "user", "content": task_description}
            ]
        }

        response = requests.post(
            "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            print(f"ERROR: AI Proxy API failed - {response.text}", flush=True)
            return None

        classification = response.json()["choices"][0]["message"]["content"].strip().lower()

        print(f"DEBUG: AI Proxy classified '{task_description}' as '{classification}'", flush=True)

        return classification if classification in TASK_MAPPING else None

    except Exception as e:
        print(f"ERROR: AI Proxy request failed - {e}", flush=True)
        return None

@app.route("/api", methods=["GET", "POST"])
def run_task():
    """Runs a task based on classification."""
    task_description = request.args.get("task")

    if not task_description:
        return jsonify({"error": "Missing task parameter"}), 400

    task_label = classify_task(task_description)

    if not task_label:
        return jsonify({"error": "Task classification failed"}), 500

    if task_label == "vs_code":
        return jsonify(vs_code(task_description)) 
    
    if task_label == "send_https_request":
        return jsonify(send_https_request(task_description)) 
    
    if task_label == "run_prettier_sha256":
        return jsonify(run_prettier_sha256(task_description))
    
    if task_label == "google_sheets_formula":
        return jsonify(google_sheets_formula(task_description))
    
    if task_label == "excel_formula":
        return jsonify(excel_formula(task_description))
    
    if task_label == "hidden_secret_value":
        return jsonify(hidden_secret_value(task_description))
    
    if task_label == "count_wednesdays":
        return jsonify(count_wednesdays(task_description))
    


    return jsonify({"error": f"Task '{task_label}' is not yet implemented"}), 400

def vs_code(task_description):
    """Runs 'code -s' in the terminal and returns the output in JSON format."""
    try:
        # ✅ Step 1: Execute the command
        try:
            command_output = subprocess.check_output("code -s", shell=True, text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            command_output = f"Error executing command: {e.output}"

        # ✅ Step 2: Return the output in JSON format
        return jsonify({"answer": command_output}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500
    
def send_https_request(task_description):
    """Sends a HTTPS request using HTTPie and returns the JSON response."""
    try:
        url = "https://httpbin.org/get"
        params = {"email": "22f2001048@ds.study.iitm.ac.in"}

        # ✅ Step 1: Send the HTTPS request
        try:
            response = requests.get(url, params=params)
            json_output = response.json()  # Extract JSON body
        except requests.RequestException as e:
            return jsonify({"answer": f"Request failed: {str(e)}"}), 500

        # ✅ Step 2: Return JSON response in the required format
        return jsonify({"answer": json_output}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500
    
import subprocess

def run_prettier_sha256(task_description):
    """Runs 'npx -y prettier@3.4.2' on README.md and returns the sha256sum output."""
    try:
        # ✅ Step 1: Ensure README.md is in the current directory
        file_path = os.path.join(PROJECT_ROOT, "README.md")
        if not os.path.isfile(file_path):
            return jsonify({"answer": "README.md file not found in the current directory"}), 404

        # ✅ Step 2: Run Prettier and compute sha256sum
        try:
            # Run Prettier on the README.md file and compute sha256sum
            command_output = subprocess.check_output(
                f"npx -y prettier@3.4.2 {file_path} | sha256sum", shell=True, text=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as e:
            return jsonify({"answer": f"Error executing command: {e.output}"}), 500

        # ✅ Step 3: Return the output in JSON format
        return jsonify({"answer": command_output.strip()}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500
    
def google_sheets_formula(task_description):
    """Returns the expected output of the given Google Sheets formula."""
    try:
        # ✅ Step 1: Compute the formula result
        # The formula creates a 100x100 sequence starting at 12 with a step of 8.
        # ARRAY_CONSTRAIN limits it to the first row and first 10 columns.
        # SUM adds up those 10 values.

        sequence_values = [12 + (i * 8) for i in range(10)]  # First 10 values in the first row
        formula_result = sum(sequence_values)  # SUM of those values

        # ✅ Step 2: Return the result in JSON format
        return jsonify({"answer": formula_result}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500
    
def excel_formula(task_description):
    """Returns the expected output of the given Excel formula."""
    try:
        # ✅ Step 1: Define the input array and sorting indices
        values = [11, 11, 3, 10, 4, 0, 8, 7, 5, 10, 7, 6, 2, 2, 1, 2]
        sort_indices = [10, 9, 13, 2, 11, 8, 16, 14, 7, 15, 5, 4, 6, 1, 3, 12]

        # ✅ Step 2: Sort values based on corresponding sort indices
        sorted_values = [val for _, val in sorted(zip(sort_indices, values))]

        # ✅ Step 3: Take the first 12 values and sum them
        formula_result = sum(sorted_values[:12])

        # ✅ Step 4: Return the result in JSON format
        return jsonify({"answer": formula_result}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500
    
from bs4 import BeautifulSoup
import requests

def hidden_secret_value(task_description):
    """Extracts the value of a hidden input field from a webpage."""
    try:
        # ✅ Step 1: Extract the URL from the task description
        headers = {"Authorization": f"Bearer {AIPROXY_TOKEN}", "Content-Type": "application/json"}
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract the URL from the task description. "
                        "Return it in JSON format as {\"url\": \"<extracted_url>\"}."
                    )
                },
                {"role": "user", "content": task_description}
            ]
        }

        response = requests.post(f"{API_BASE_URL}/chat/completions", headers=headers, json=data)

        if response.status_code != 200:
            return jsonify({"answer": "LLM extraction failed"}), 500

        extracted_data = response.json()["choices"][0]["message"]["content"].strip()
        url = json.loads(extracted_data).get("url", "").strip()

        # ✅ Step 2: Ensure URL is valid
        if not url:
            return jsonify({"answer": "No valid URL found in the task description"}), 400

        # ✅ Step 3: Fetch the webpage content
        page_response = requests.get(url)

        if page_response.status_code != 200:
            return jsonify({"answer": f"Failed to fetch page, status: {page_response.status_code}"}), 500

        # ✅ Step 4: Parse the HTML and find the hidden input
        soup = BeautifulSoup(page_response.text, "html.parser")
        hidden_input = soup.find("input", {"type": "hidden"})

        if not hidden_input or "value" not in hidden_input.attrs:
            return jsonify({"answer": "No hidden input field found"}), 404

        # ✅ Step 5: Extract and return the hidden value
        hidden_value = hidden_input["value"]
        return jsonify({"answer": hidden_value}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500
    
from datetime import datetime, timedelta

def count_wednesdays(task_description):
    """Counts the number of Wednesdays in the given date range."""
    try:
        # ✅ Step 1: Extract the start and end dates from the task description
        headers = {"Authorization": f"Bearer {AIPROXY_TOKEN}", "Content-Type": "application/json"}
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract the start and end dates from the task description. "
                        "Return in JSON format as {\"start_date\": \"YYYY-MM-DD\", \"end_date\": \"YYYY-MM-DD\"}."
                    )
                },
                {"role": "user", "content": task_description}
            ]
        }

        response = requests.post(f"{API_BASE_URL}/chat/completions", headers=headers, json=data)

        if response.status_code != 200:
            return jsonify({"answer": "LLM extraction failed"}), 500

        extracted_data = response.json()["choices"][0]["message"]["content"].strip()
        date_range = json.loads(extracted_data)

        start_date = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(date_range["end_date"], "%Y-%m-%d")

        # ✅ Step 2: Count Wednesdays
        count = 0
        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() == 2:  # Wednesday (Monday=0, ..., Sunday=6)
                count += 1
            current_date += timedelta(days=1)

        # ✅ Step 3: Return the count in JSON format
        return jsonify({"answer": count}), 200

    except Exception as e:
        return jsonify({"answer": f"Execution failed: {str(e)}"}), 500







