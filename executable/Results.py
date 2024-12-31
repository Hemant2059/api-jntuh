import requests, json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import executable.Codes as Codes


class Results:
    def __init__(self):
       
        self.url = "http://results.jntuh.ac.in/results/resultAction"
        self.results = {"Details": {}, "Result": {}}
        self.exam_codes = Codes.get_exam_codes()
        self.session = requests.Session()  # Use session to reuse connections

    def get_result(self, roll_number):
        self.roll_number = roll_number
        # Determine degree and exam codes
        graduation_year = int(self.roll_number[:2])
        degree = "btech" if self.roll_number[5] == "A" else "bpharmacy"
        regulation = (
            "R22"
            if graduation_year >= 23 or (graduation_year == 22 and self.roll_number[4] != "5")
            else ("R18" if degree == "btech" else "R17")
        )
        exam_codes = self.exam_codes[degree][regulation] if regulation in self.exam_codes[degree] else {}
        if self.roll_number[4] == "5":
            exam_codes.pop("1-1")  # Remove 1-1 semester for lateral entry students
            exam_codes.pop("1-2")  # Remove 1-1 semester for lateral entry students


        # Prepare tasks
        tasks = []
        with ThreadPoolExecutor(max_workers=20) as executor:  # Increase max_workers for better parallelism
            for semester, codes in exam_codes.items():
                for exam_code in codes:
                    for result_type in ["null", "gradercrv"]:
                        payload = f"{self.url}?examCode={exam_code}&etype=r16&result={result_type}&grad=null&type=intgrade&degree={degree}&htno={self.roll_number}"
                       
                        tasks.append((semester, exam_code, executor.submit(self.fetch_url, payload)))

            # Process results
            for semester, exam_code, future in tasks:
                try:
                    html_content = future.result()
                    if html_content:
                        self.scrape_results(semester, html_content)
                except Exception as e:
                    return "Failed to fetch URL"

        
        return json.dumps(self.results)

    @lru_cache(maxsize=100)  # Cache results to avoid duplicate requests
    def fetch_url(self, url):
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
            else:
                return "Failed to fetch URL"
            
        except requests.exceptions.RequestException as e:
           
            return "Failed to fetch URL"

    def scrape_results(self, semester_code, response):
        soup = BeautifulSoup(response, "html.parser")
        if soup.find("form", {"id": "myForm"}):
            return

        # Extract student details
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

        # Extract results
        results_table = soup.find_all("table")[1].find_all("tr")
        column_names = [col.text for col in results_table[0].findAll("b")]
        indices = {
            "subject_code": column_names.index("SUBJECT CODE"),
            "subject_name": column_names.index("SUBJECT NAME"),
            "grade": column_names.index("GRADE"),
            "credits": column_names.index("CREDITS(C)"),
        }
        optional_indices = {
            "internal": column_names.index("INTERNAL") if "INTERNAL" in column_names else None,
            "external": column_names.index("EXTERNAL") if "EXTERNAL" in column_names else None,
            "total": column_names.index("TOTAL") if "TOTAL" in column_names else None,
        }

        self.results["Result"].setdefault(semester_code, {})
        for row in results_table[1:]:
            cells = row.find_all("td")
            subject_code = cells[indices["subject_code"]].get_text()
            self.results["Result"][semester_code][subject_code] = {
                "name": cells[indices["subject_name"]].get_text(),
                "grade": cells[indices["grade"]].get_text(),
                "credits": cells[indices["credits"]].get_text(),
                "internal": cells[optional_indices["internal"]].get_text() if optional_indices["internal"] else "",
                "external": cells[optional_indices["external"]].get_text() if optional_indices["external"] else "",
                "total": cells[optional_indices["total"]].get_text() if optional_indices["total"] else "",
                "rcrv": "Change in Grade" in cells[-1].get_text(),
            }

