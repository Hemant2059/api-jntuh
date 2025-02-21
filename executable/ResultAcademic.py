import executable.ResultSem as sem_result
from concurrent.futures import ThreadPoolExecutor, as_completed

class Results:
    def __init__(self):
        self.semesters = ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2", "4-1", "4-2"]

    def get_cached_result(self, roll_number):
        all_results = {
            "Details": {},
            "results": []
        }

        # Temporary dictionary to store semester results
        semester_results = {}

        # Use ThreadPoolExecutor for parallel fetching
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit tasks with a new instance of sem_result.Results() for each
            future_to_sem = {
                executor.submit(sem_result.Results().get_cached_result, roll_number, sem): sem
                for sem in self.semesters
            }

            # Process completed futures
            for future in as_completed(future_to_sem):
                sem = future_to_sem[future]
                try:
                    sem_data = future.result()
                    if sem_data and sem_data.get("Result"):
                        # Store semester result
                        semester_results[sem] = sem_data["Result"]

                        # Set student details once
                        if not all_results["Details"] and sem_data.get("Details"):
                            all_results["Details"] = sem_data["Details"]
                except Exception as e:
                    print(f"Error fetching results for {sem}: {e}")

        # Append results in the correct semester order
        for sem in self.semesters:
            if sem in semester_results:
                all_results["results"].append({sem: semester_results[sem]})

        # Handle invalid roll number
        if not all_results["Details"]:
            all_results["Details"] = {"Roll_No": "Invalid Hallticket Number"}

        return all_results
