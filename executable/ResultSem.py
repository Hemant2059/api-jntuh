import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import executable.Codes as Codes

class Results:
    def __init__(self):
        self.url = "http://results.jntuh.ac.in/results/resultAction"
        self.results = {"Details": {}, "Result": {}}
        self.exam_codes = Codes.get_exam_codes()
        self.session = self.create_session()
        self.cache = {}  # Initialize cache as an empty dictionary

    def create_session(self):
        """ Create a session with connection pooling and retry mechanism. """
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=100, pool_maxsize=100)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @lru_cache(maxsize=100)  # Cache results to avoid duplicate requests
    def get_cached_result(self, roll_number, sem):
        return self.get_result(roll_number, sem)

    def get_result(self, roll_number, sem):
        self.roll_number = roll_number

        if (roll_number, sem) in self.cache:
            print(f"Cache hit for {roll_number}, {sem}")
            return self.cache[(roll_number, sem)]

        graduation_year = int(self.roll_number[:2])
        degree = "btech" if self.roll_number[5] == "A" else "bpharmacy"
        regulation = (
            "R22"
            if graduation_year >= 23 or (graduation_year == 22 and self.roll_number[4] != "5")
            else ("R18" if degree == "btech" else "R17")
        )
        exam_codes = self.exam_codes[degree][regulation].get(sem, [])
        if self.roll_number[4] == "5" and (sem == "1-1" or sem == "1-2"):
            return "No data available for this semester"

        tasks = []
        passed_all_subjects = False
        first_exam_code = exam_codes[0] if exam_codes else None
        with ThreadPoolExecutor(max_workers=100) as executor:
            for index, exam_code in enumerate(exam_codes):
                if passed_all_subjects and exam_code != first_exam_code:
                    break  # Skip checking other exam codes if all subjects are passed

                for result_type in ["null", "gradercrv"]:
                    payload = f"{self.url}?examCode={exam_code}&etype=r16&result={result_type}&grad=null&type=intgrade&degree={degree}&htno={self.roll_number}"
                    tasks.append((exam_code, executor.submit(self.fetch_url, payload)))

            for exam_code, future in tasks:
                try:
                    html_content = future.result()
                    if html_content:
                        self.scrape_results(html_content)
                        if exam_code == first_exam_code and self.all_subjects_passed():
                            passed_all_subjects = True  # Stop checking other exam codes
                            print(exam_code)
                except Exception as e:
                    print(f"Error processing examCode {exam_code}: {e}")

        if not self.results["Details"].get("Roll_No"):
            self.results["Details"]["Roll_No"] = "Invalid Hallticket Number"

        self.cache[(roll_number, sem)] = self.results
        return self.results

    def fetch_url(self, url):
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                return {"error":"Server Error"}
        except requests.exceptions.RequestException as e:
            return {"error":"Server Error"}

    def scrape_results(self, response):
        soup = BeautifulSoup(response, "html.parser")
        if soup.find("form", {"id": "myForm"}):            
            return  # Return if no results (invalid form)

        details_table = soup.find_all("table")[0].find_all("tr")
        Htno = details_table[0].find_all("td")[1].get_text()
        Name = details_table[0].find_all("td")[3].get_text()
        Father_Name = details_table[1].find_all("td")[1].get_text()
        College_Code = details_table[1].find_all("td")[3].get_text()

        if Htno != self.results["Details"].get("Roll_No"):
            self.results["Details"] = {
                "NAME": Name,
                "Roll_No": Htno,
                "FATHER_NAME": Father_Name,
                "COLLEGE_CODE": College_Code,
            }

        results_table = soup.find_all("table")[1].find_all("tr")
        for row in results_table[1:]:
            cells = row.find_all("td")
            subject_code = cells[0].get_text()
            self.results["Result"][subject_code] = {
                "name": cells[1].get_text(),
                "internal":cells[2].get_text(),
                "external":cells[3].get_text(),
                "total":cells[4].get_text(),
                "grade": cells[5].get_text(),
                "credits": cells[6].get_text(),
                "rcrv": "Change in Grade" in cells[-1].get_text(),
            }
    
    def all_subjects_passed(self):
        """ Check if the student has passed all subjects. """
        return all(subject["grade"] not in ["F", "Ab"] for subject in self.results["Result"].values())
