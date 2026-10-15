# DIA 2.0: Easy Test Guide

This guide helps you try the backend using the tiny sample images already in this repository. You do not need to know what an API or database is to follow it.

You will open **two PowerShell windows**:

- Window 1 runs the web service that accepts your dataset.
- Window 2 runs the background worker that analyzes it.

Keep both windows open while testing.

## Before you start

Open PowerShell and copy this command. It takes you to the project folder:

```powershell
cd "C:\Users\SRIJAN BAJPAI\Downloads\Dataset Integrity Analyzer"
```

If your project is saved somewhere else, replace the path with your own folder path.

Check your Python version:

```powershell
python --version
```

The project expects Python 3.12. The commands below use the project's `.venv` environment, which is already set up in this workspace. If you do not have a `.venv` folder, run these once from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-v2.txt
```

## Step 1: Prepare the database

In PowerShell Window 1, make sure you are in the project folder, then run:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

This creates or updates the local database. You should see a message mentioning SQLite. If it says there are no new migrations to run, that is okay too.

## Step 2: Start the web service

In Window 1, run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn dia.api.main:app --reload
```

Leave this window open. When you see a message saying the application has started, the service is ready.

You can open this address in your browser to see the API's built-in test page:

<http://127.0.0.1:8000/docs>

## Step 3: Start the analyzer

Open a **second** PowerShell window. Go to the project folder again:

```powershell
cd "C:\Users\SRIJAN BAJPAI\Downloads\Dataset Integrity Analyzer"
```

Start the background worker:

```powershell
.\.venv\Scripts\python.exe -m dia.worker
```

Leave this window open too. The worker waits quietly until there is an analysis to run.

## Step 4: Pack the sample pictures into a ZIP file

Open a **third** PowerShell window. The first two windows are busy running the service and worker. Go to the project folder, then run:

```powershell
Compress-Archive -Path .\test_data\class_A, .\test_data\class_B -DestinationPath .\dia-smoke.zip -Force
```

This puts the sample pictures into `dia-smoke.zip`. The ZIP contains two groups of pictures, which DIA needs for a classification dataset.

## Step 5: Upload the ZIP

In the same PowerShell window, run:

```powershell
$uploadText = curl.exe -sS -X POST http://127.0.0.1:8000/v1/datasets -F "file=@dia-smoke.zip"
$dataset = $uploadText | ConvertFrom-Json
$dataset
```

You should see information including an `id`, `sample_count`, and `class_count`. The `id` is the dataset's address inside DIA. Keep that PowerShell window open; the next steps use the `$dataset` value it contains.

## Step 6: Ask DIA to analyze the pictures

Run:

```powershell
$requestBody = @{ sampling_rate = 1.0; sampling_seed = 42 } | ConvertTo-Json
$run = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/datasets/$($dataset.id)/runs" -Method Post -ContentType "application/json" -Body $requestBody
$run
```

You should see a `run_id`. This is the address of this particular analysis. Keep the window open so PowerShell remembers `$run`.

## Step 7: Wait for the analysis to finish

Copy and run this block. It checks progress every two seconds:

```powershell
do {
    Start-Sleep -Seconds 2
    $status = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/runs/$($run.run_id)"
    "$($status.status) - $($status.progress_percent)% - $($status.status_message)"
} while ($status.status -in @("queued", "running"))

$status
```

Wait until the status says `completed`. On the very first run, DIA may need to download a pre-trained picture-analysis file. That can make the first analysis slower; later runs may be faster.

If it says `failed`, look at `error_message` in the output and at Window 2, where the worker prints detailed errors.

## Step 8: Look at the results

Get the full report:

```powershell
$report = Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/runs/$($run.run_id)/report"
```

Show the class counts:

```powershell
$report.results.distribution | ConvertTo-Json -Depth 8
```

Show the image-quality results:

```powershell
$report.results.quality | ConvertTo-Json -Depth 8
```

Show duplicate-image results:

```powershell
$report.results.duplicates | ConvertTo-Json -Depth 8
```

Show the readiness score and what information it could measure:

```powershell
$report.results.readiness | ConvertTo-Json -Depth 8
```

The included sample pictures do not come with information such as people's ages, genders, or locations. Therefore, some fairness measurements may say they are unavailable. That is expected; DIA does not guess missing group information and present the guess as fact.

## Step 9: Save the per-picture results as a spreadsheet file

Run:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/v1/runs/$($run.run_id)/samples.csv" -OutFile .\dia-samples.csv
```

This saves `dia-samples.csv` in the project folder. Open it with Excel or another spreadsheet app to see measurements for individual pictures.

## Run the automated checks

These checks test the code itself, including unsafe ZIP files, analysis results, API access, and deletion behavior. Run this from the project folder:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

You should see `21 passed` (the exact number may change as tests are added).

## If something goes wrong

- **“Connection refused” or “Could not connect”:** Make sure Window 1 is still running the API command.
- **The run stays queued:** Make sure Window 2 is still running `python -m dia.worker`.
- **PowerShell says a file or folder is missing:** Check that you are in the repository folder by running `Get-Location`.
- **The first run cannot load image features:** Check your internet connection; the pre-trained picture-analysis file may need to download once. The worker window shows the detailed error.
- **It says unauthorized:** Local development normally has no password. If you set `DIA_SHARED_PASSWORD`, include it as an `X-DIA-Password` header in your requests.
- **You see “unavailable” in the report:** This can be correct. DIA marks checks unavailable when it lacks the data or validated model needed to calculate them.

## Stop the services

Click each service window and press **Ctrl+C**. The uploaded dataset stays in local storage until you delete it through the API; stopping the service does not delete it.

For more advanced options, supported data layouts, and all endpoints, see [API_GUIDE.md](API_GUIDE.md).
