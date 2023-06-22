from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi import Request
import requests
import json
from fastapi.templating import Jinja2Templates
from pdf import pdf_to_text_spans
from fastapi.staticfiles import StaticFiles
import boto3
import tempfile

# Create an S3 client
s3 = boto3.client('s3')
app = FastAPI()
templates = Jinja2Templates(directory="templates")


def to_json_filter(value):
    return json.dumps(value)

# Add the filter to Jinja2 environment
templates.env.filters["to_json"] = to_json_filter


app.mount("/static", StaticFiles(directory="static"), name="static")
inference_server_url = "http://inference-server:8000/predict"  # Inference server URL

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize")
async def summarize(request: Request, pdf_file: UploadFile = File(...)):
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
        temp_pdf.write(pdf_file.file.read())
        src = temp_pdf.name
    
    text = pdf_to_text_spans(src)

    data = {"text": text}
    headers = {"Content-Type": "application/json"}
    response = requests.post(inference_server_url, data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        # Process the response from the inference server
        inference_results = response.json()
        
        summary0 = inference_results[0]
        summary1 = inference_results[1]

        return templates.TemplateResponse(
            "feedback.html",
            {"request": request, "summary0": summary0, "summary1": summary1,  "text": text}
        )
    else:
        return {"error": "Failed to retrieve summary from the inference server"}
    
@app.post("/adminsummarize")
async def summarize(request: Request, pdf_file: UploadFile = File(...)):
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
        temp_pdf.write(pdf_file.file.read())
        src = temp_pdf.name
    
    text = pdf_to_text_spans(src)

    data = {"text": text}
    headers = {"Content-Type": "application/json"}
    response = requests.post(inference_server_url, data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        # Process the response from the inference server
        inference_results = response.json()
        
        summary0 = inference_results[0]
        summary1 = inference_results[1]

        return templates.TemplateResponse(
            "reward.html",
            {"request": request, "summary0": summary0, "summary1": summary1,  "text": text}
        )
    else:
        return {"error": "Failed to retrieve summary from the inference server"}    
    
@app.post("/save")
async def save_data(request_data: dict):
    # Process the data and save it to AWS S3 bucket
    # Assuming you have the following dummy URL and bucket name
    bucket_name = "your-bucket-name"
    object_key = "data.json"

    # Convert the request data to JSON string
    json_data = json.dumps(request_data)

    try:
        # Upload the data to S3 bucket
        s3.put_object(Body=json_data, Bucket=bucket_name, Key=object_key)
        return templates.TemplateResponse(
            "index.html",
            {"message": "Data saved successfully"}
        )
    except Exception as e:
        return {"error": f"Failed to save data: {str(e)}"}


if __name__ == "__main__":
            
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)