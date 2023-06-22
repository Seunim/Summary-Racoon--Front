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
from fastapi import Form

# Create an S3 client
s3_raccoon= boto3.client('s3', region_name = 'ap-northeast-2')
app = FastAPI()
templates = Jinja2Templates(directory="templates")


def to_json_filter(value):
    return json.dumps(value)

# Add the filter to Jinja2 environment
templates.env.filters["to_json"] = to_json_filter


app.mount("/static", StaticFiles(directory="static"), name="static")
inference_server_url = "https://asdasdinfer.run.goorm.site/inference"  # Inference server URL

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize")
async def summarize(request: Request, pdf_file: UploadFile = File(...)):
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
        temp_pdf.write(pdf_file.file.read())
        src = temp_pdf.name
    
    text = pdf_to_text_spans(src)
    realtext= []
    for i in range(len(text)):
        realtext.append(text[i]['text'])
    section=[]
    for i in range(len(text)):
        section.append(text[i]["section"])
    data = {"text": text}

    response = requests.get(inference_server_url, data=json.dumps(data))

    if response.status_code == 200:
        # Process the response from the inference server
        response_dict = response.json()
        print(response_dict)

        summary0 = response_dict["inference_results0"]
        summary0 = [item for sublist in summary0 for item in sublist]
        summary1 = response_dict["inference_results1"]
        summary1 = [item for sublist in summary1 for item in sublist]

        return templates.TemplateResponse(
    "feedback.html",
    {
        "request": request,
        "summary0": summary0,
        "summary1": summary1,
        "text": realtext,
        "section": section,
        "section_length": len(section)  # Add this line
    }

        )
    else:
        return {"error": "Failed to retrieve summary from the inference server"}

@app.post("/save")
async def save_data(
    summary_feedback: str = Form(...),
    text: str = Form(...),
    summary0: str = Form(...),
    summary1: str = Form(...)
):
    summary=[]
    text = text
    if summary_feedback == summary1:
        summary.append(summary1)
        summary.append(summary0)
    elif summary_feedback == summary0:
        summary.append(summary0)
        summary.append(summary1)

    data = {"summary": summary, "text": text}

    # Convert the data to JSON
    json_data = json.dumps(data)

    # Specify the existing file name in S3
    bucket_name = "paper.raccoon-reward.texts"
    file_name = "summarydata.txt"

    # Get the existing content of the file
    response = s3_raccoon.get_object(Bucket=bucket_name, Key=file_name)
    existing_data = response["Body"].read().decode()

    # Append the new JSON data to the existing content
    updated_data = existing_data + "\n" + json_data

    # Save the updated data back to the file in S3
    s3_raccoon.put_object(Body=updated_data, Bucket=bucket_name, Key=file_name)

    return {"message": "Text and summary saved successfully."}
    



if __name__ == "__main__":
            
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)