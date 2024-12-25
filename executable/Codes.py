import os
import requests
from bs4 import BeautifulSoup
import json
import time

def get_file_path(filename):
    # Get the absolute path for the file in the same directory as this script
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Gets the directory of this script
    return os.path.join(current_dir, filename)


def extract_exam_code(result_link):
    # Extract the exam code from the result link
    try:
        exam_code_index = result_link.find("examCode")
        exam_code = result_link[exam_code_index + 9:exam_code_index + 13]
        if exam_code[3] == '&':
            return exam_code[:3]
        return exam_code
    except Exception as e:
        print(f"Error extracting exam code: {e}")
        return None


def categorize_exam_code(result_text):
    # Categorize the exam code based on the result text
    year_categories = {
        " I Year I ": "1-1", " I Year II ": "1-2", 
        " II Year I ": "2-1", " II Year II ": "2-2", 
        " III Year I ": "3-1", " III Year II ": "3-2", 
        " IV Year I ": "4-1", " IV Year II ": "4-2"
    }
    for key, value in year_categories.items():
        if key in result_text:
            return value
    return None



def extract_exam_codes():
    url = "http://results.jntuh.ac.in/jsp/home.jsp"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    exam_codes = {
        "btech": {"R18": {}, "R22": {}},
        "bpharmacy": {"R17": {}, "R22": {}},
    }
    degree = list(exam_codes.keys())

    for table_index, degree_type in enumerate(degree):
        results = soup.find_all("table")[table_index].find_all("tr")
        regulations = exam_codes[degree_type].keys()

        # Iterate through each result in the table
        for result in results:
            try:
                result_link = result.find_all("td")[0].find_all("a")[0]["href"]
                result_text = result.get_text()
               
                # Check if the result text contains any of the regulations
                for regulation in regulations:
                    if regulation in result_text:
                        exam_code = extract_exam_code(result_link)
                        if exam_code:
                            category = categorize_exam_code(result_text)
                            if category:
                                exam_codes[degree_type][regulation].setdefault(category, [])
                                if exam_code not in exam_codes[degree_type][regulation][category]:
                                    exam_codes[degree_type][regulation][category].append(exam_code)
            except Exception as e:
                print(f"Error processing result: {e}")
                continue

        # Sort the exam codes within each category and sort the categories
        for regulation in regulations:
            for category, codes in exam_codes[degree_type][regulation].items():
                exam_codes[degree_type][regulation][category] = sorted(codes)
            exam_codes[degree_type][regulation] = dict(sorted(exam_codes[degree_type][regulation].items(), key=lambda x: x[0]))

    
    # Remove "1690" from semester 3-1 before returning
    if "btech" in exam_codes:
        if "R18" in exam_codes["btech"]:
            if "3-1" in exam_codes["btech"]["R18"]:
                exam_codes["btech"]["R18"]["3-1"] = [code for code in exam_codes["btech"]["R18"]["3-1"] if code != "1690"]
    

    return exam_codes



def save_exam_codes(exam_codes, filename="exam_codes.json"):
    file_path = get_file_path(filename)
    with open(file_path, "w") as f:
        json.dump({"data": exam_codes, "timestamp": time.time()}, f)
    print(f"Exam codes saved to {file_path}")


def is_data_fresh(filename="exam_codes.json", max_age=86400):
    try:
        file_path = get_file_path(filename)
        with open(file_path, "r") as f:
            data = json.load(f)
        return time.time() - data["timestamp"] < max_age
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return False


def load_exam_codes(filename="exam_codes.json"):
    try:
        file_path = get_file_path(filename)
        with open(file_path, "r") as f:
            return json.load(f)["data"]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return {}


def get_exam_codes():
    if is_data_fresh():
        return load_exam_codes()
    else:
        exam_codes = extract_exam_codes()
        save_exam_codes(exam_codes)
        return exam_codes

# You can now use get_exam_codes() to get the data from the website or the local file.

# Example usage:
exam_codes = get_exam_codes()