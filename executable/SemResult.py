import asyncio, json
import aiohttp
from bs4 import BeautifulSoup

import executable.Codes as codes


url = "https://results.jntuh.ac.in/results/resultAction?degree={}&examCode={}&etype=r16&result={}&grad=null&type=intgrade&htno={}"

results = {"Details": {}, "Result": {}}
exam_codes = codes.get_exam_codes()
etype = ['null', 'gradercrv']



def get_result(session, hallticket,sem):
    graduation_year = int(hallticket[:2])
    degree = "btech" if hallticket[5] == "A" else "bpharmacy"
    regulation = "R22" if graduation_year >= 23 or (graduation_year == 22 and hallticket[4] != "5") else ("R18" if degree == "btech" else "R17")
    e_code = exam_codes[degree][regulation][sem] if sem in exam_codes[degree][regulation] else []    
    
    tasks = [
        session.get(url.format(degree, code, e, hallticket), ssl=False)
        for code in e_code for e in etype
    ]
    return tasks

async def get_symbol(hallticket: str, sem: str):
    # Reset the results dictionary before starting the new request
    global results
    results = {"Details": {}, "Result": {}}
    
    async with aiohttp.ClientSession() as session:
        tasks = get_result(session, hallticket, sem)
        responses = await asyncio.gather(*tasks)

        for response in responses:
            result = await response.text()
            scrape_results(result)

      
    return results

def scrape_results(result):
    soup = BeautifulSoup(result, "html.parser")
    
    if soup.find("form", {"id": "myForm"}):
        return    

    
    details_table = soup.find_all("table")[0].find_all("tr")
    Htno = details_table[0].find_all("td")[1].get_text()
    Name = details_table[0].find_all("td")[3].get_text()
    Father_Name = details_table[1].find_all("td")[1].get_text()
    College_Code = details_table[1].find_all("td")[3].get_text()

    if Htno != results["Details"].get("Roll_No"):
        results["Details"] = {
            "NAME": Name,
            "Roll_No": Htno,
            "FATHER_NAME": Father_Name,
            "COLLEGE_CODE": College_Code,
        }

    results_table = soup.find_all("table")[1].find_all("tr")
    column_names = [col.text for col in results_table[0].find_all("b")]
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

    
    for row in results_table[1:]:
        cells = row.find_all("td")
        subject_code = cells[indices["subject_code"]].get_text()
        results["Result"][subject_code] = {
            "name": cells[indices["subject_name"]].get_text(),
            "grade": cells[indices["grade"]].get_text(),
            "credits": cells[indices["credits"]].get_text(),
            "internal": cells[optional_indices["internal"]].get_text() if optional_indices["internal"] is not None else "",
            "external": cells[optional_indices["external"]].get_text() if optional_indices["external"] is not None else "",
            "total": cells[optional_indices["total"]].get_text() if optional_indices["total"] is not None else "",
            "rcrv": "Change in Grade" in cells[-1].get_text(),
        }





