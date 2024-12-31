from typing import Union
import asyncio 
from fastapi import FastAPI

app = FastAPI()


import executable.Results as results
import executable.ResultSem as sem_result
from executable.SemResult import get_symbol


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/academic")
def read_item(ht: Union[str, None] = None):
    result = results.Results().get_result(ht)
    return result if result else {"result": "No results found"}

@app.get("/sem")
def read_item(htno: Union[str, None] = None, sem: Union[str, None] = None):
    result = sem_result.Results().get_result(htno, sem)
    return result if result else {"result": "No results found"}


@app.get("/semester")
def read_item(htno: Union[str, None] = None, sem: Union[str, None] = None):
    result = asyncio.run(get_symbol(htno, sem))
    return result if result else {"result": "No results found"}

