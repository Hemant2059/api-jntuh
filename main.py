from typing import Union
import asyncio 
from fastapi import FastAPI

app = FastAPI()


import executable.Results as results
from executable.SemResult import get_symbol


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/results/academic")
def read_item(ht: Union[str, None] = None):
    result = results.Results().get_result(ht)
    return result if result else {"result": "No results found"}


@app.get("/results/semester")
def read_item(htno: Union[str, None] = None, sem: Union[str, None] = None):
    result = asyncio.run(get_symbol(htno, sem))
    return result if result else {"result": "No results found"}

