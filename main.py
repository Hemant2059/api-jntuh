from typing import Union
from fastapi import FastAPI

app = FastAPI()

import executable.ResultSem as sem_result
import executable.ResultAcademic as academic_result


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/academic")
def read_item(htno: Union[str, None] = None):
    result = academic_result.Results().get_cached_result(htno)
    return result if result else {"result": "No results found"}

@app.get("/sem")
def read_item(htno: Union[str, None] = None, sem: Union[str, None] = None):
    result = sem_result.Results().get_cached_result(htno, sem)
    return result if result else {"result": "No results found"}
