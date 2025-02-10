import os
import requests
from bs4 import BeautifulSoup
import json
import time
import re

def get_file_path(filename):
    """Get the absolute path of a file in the same directory as this script."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def extract_exam_code(result_link):
    """Extract the exam code from the result link using regex."""
    match = re.search(r"examCode=(\d+)", result_link)
    return match.group(1) if match else None

def categorize_exam_code(result_text):
    """Categorize the exam code based on the result text."""
    categories = {
        " I Year I ": "1-1", " I Year II ": "1-2", 
        " II Year I ": "2-1", " II Year II ": "2-2", 
        " III Year I ": "3-1", " III Year II ": "3-2", 
        " IV Year I ": "4-1", " IV Year II ": "4-2"
    }
    return next((value for key, value in categories.items() if key in result_text), None)

def extract_exam_codes():
    """Scrape exam codes from the results page and structure them properly."""
    url = "http://results.jntuh.ac.in/jsp/home.jsp"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return {}

    soup = BeautifulSoup(response.content, "html.parser")
    exam_codes = {"btech": {"R18": {}, "R22": {}}, "bpharmacy": {"R17": {}, "R22": {}}}

    degree_types = list(exam_codes.keys())

    for table_index, degree in enumerate(degree_types):
        try:
            results = soup.find_all("table")[table_index].find_all("tr")
        except IndexError:
            print(f"Warning: No table found for {degree}")
            continue

        for result in results:
            try:
                link = result.find("a")
                if not link:
                    continue

                result_link = link["href"]
                result_text = result.get_text()
                exam_code = extract_exam_code(result_link)

                if not exam_code:
                    continue

                for regulation in exam_codes[degree]:
                    if regulation in result_text:
                        category = categorize_exam_code(result_text)
                        if category:
                            exam_codes[degree][regulation].setdefault(category, set()).add(exam_code)
            except Exception as e:
                print(f"Error processing result: {e}")

    # Convert sets to sorted lists
    for degree in exam_codes:
        for regulation in exam_codes[degree]:
            for category in exam_codes[degree][regulation]:
                exam_codes[degree][regulation][category] = sorted(exam_codes[degree][regulation][category])

    # Remove "1690" from "3-1" in "btech R18"
    exam_codes["btech"]["R18"].get("3-1", []).remove("1690") if "3-1" in exam_codes["btech"]["R18"] else None

    return exam_codes

def save_exam_codes(exam_codes, filename="exam_codes.json"):
    """Save exam codes to a JSON file."""
    try:
        with open(get_file_path(filename), "w") as f:
            json.dump({"data": exam_codes, "timestamp": time.time()}, f)
        print(f"Exam codes saved to {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")

def load_exam_codes(filename="exam_codes.json"):
    """Load exam codes from a JSON file."""
    try:
        with open(get_file_path(filename), "r") as f:
            return json.load(f)["data"]
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def is_data_fresh(filename="exam_codes.json", max_age=86400):
    """Check if the cached exam codes file is still fresh."""
    try:
        with open(get_file_path(filename), "r") as f:
            data = json.load(f)
        return time.time() - data.get("timestamp", 0) < max_age
    except (FileNotFoundError, json.JSONDecodeError):
        return False

def get_exam_codes():
    """Return fresh exam codes from cache or scrape new ones."""
    if is_data_fresh():
        return load_exam_codes()
    else:
        exam_codes = extract_exam_codes()
        save_exam_codes(exam_codes)
        return exam_codes
