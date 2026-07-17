# 🔐 PermAware: Context-Aware Android Permission Justification

PermAware is a context-aware system designed to analyze Android application permissions and determine whether they are **Justified** or **Unjustified** based on the application's category. For example, a Social Media application requesting Camera permission is labeled as **"Justified"**, whereas a Gaming app requesting the same permission may be flagged as **"Unjustified"**.

Unlike traditional approaches that rely on fixed static rules or simple malware detection, PermAware leverages a fine-tuned **BERT (Bidirectional Encoder Representations from Transformers)** model to understand the deep semantic relationship between permission requests and app categories.

---

## 📊 Performance & Key Results
* **Accuracy:** 92.5% on a held-out validation set.
* **F1-Score:** 0.88, demonstrating robust performance on imbalanced datasets.
* **Explainability:** Token-level attention heatmaps are used to visualize the contextual relationships between specific permissions and app categories.

## 🛠️ System Walkthrough

The PermAware framework operates through a structured four-stage modular pipeline, accessible via a **Streamlit** interface.

### 1. Input Generation
The system supports an automated mode where users enter an **Application ID** (e.g., `com.facebook.katana`) to scrape permissions from the Google Play Store, or a manual mode for custom evaluation.

![Input Panel](./images/input_panel.png)

### 2. Scraping & Normalization
Permissions are extracted using **BeautifulSoup** and passed through a normalization module to map noisy or varied text (e.g., "access microphone") to canonical labels like `RECORD_AUDIO`.

![Scraped Permissions](./images/scraped_permissions.png)

### 3. BERT Classification
The normalized inputs are processed by the fine-tuned **BERT model**, which performs binary inference to determine justification. Results are presented in a tabular format with **predicted labels** and **confidence scores**.

![Classification Results](./images/classification_results.png)

## 📂 Dataset Details
* **Source:** Custom rule-based synthetic dataset developed for context-aware classification.
* **Size:** 980 total permission–category pairs.
  * **308 Justified** samples.
  * **672 Unjustified** samples.
* **Scope:** Covers 10 well-known application categories and 14 canonical permission types.

## 🚀 How to Run (Google Colab)
This project is optimized for **Google Colab** using an **NVIDIA T4 GPU**.

### 1. Run Cells Sequentially
Execute all cells from top to bottom:
* **Install dependencies:** `transformers`, `streamlit`, `pyngrok`.
* **Upload the Dataset:** Uplaod the `final_synthetic_dataset.csv'` Dataset in colab when prompted to.
* **Load Model:** Initialize the fine-tuned BERT model.
* **Launch:** Deploy the Streamlit interface.

### 2. Ngrok Authentication
To access the web interface, enter your **Ngrok Auth Token** in the 3rd cell by replacing the placeholder text `"Add your ngrok authentication token here"`.

### 3. Research vs. Implementation
* **Implementation Cells:** Required to launch and run the application.
* **Research Cells (below pyngrok code):**
  * Contains code for the **ablation study** and performance benchmarking.
  * These are optional and can be skipped for normal prototype usage.

## 🤝 Contributors
* **Shreyas Prabhu** – St. John College of Engineering and Management
* **Sharvareesh Upadhyay** – St. John College of Engineering and Management
* **Jayesh Sutar** – St. John College of Engineering and Management
* **Pooja Gharat** (Advisor) – St. John College of Engineering and Management

## 📄 License
This project is licensed under the **MIT License**.

---
## ⚡ FastAPI Inference Service

The project has been converted into a production-ready FastAPI inference service located in the [app/](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app) directory.

### Project Structure
*   **[app/config.py](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app/config.py):** Portable path resolutions using `pathlib`.
*   **[app/schemas.py](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app/schemas.py):** Pydantic request (`PredictRequest`) and response (`PredictResponse`) schemas.
*   **[app/train.py](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app/train.py):** Reusable module containing the notebook's exact BERT training pipeline.
*   **[app/preprocessing.py](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app/preprocessing.py):** Data extraction (Google Play Store scraping) and canonical permission normalization.
*   **[app/inference.py](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app/inference.py):** Tokenizer/Model loader and binary prediction pipeline. If model weights (`my_model_bce`) are missing at startup, it automatically triggers the training module to build the model first.
*   **[app/utils.py](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app/utils.py):** Reproducibility and logging utility functions.
*   **[app/main.py](file:///d:/Personal%20Project/Major%20proj%20zip/Major%20proj%20zip/app/main.py):** FastAPI application with lifecycle lifespan setup and `/predict` endpoint.

### 🏃 Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python -m uvicorn app.main:app --port 8000
   ```
3. Perform a test prediction:
   ```powershell
   # PowerShell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/predict" -Method Post -ContentType "application/json" -Body '{"permission": "Location", "category": "Social Media"}'
   ```

### ☁️ Deploying to Render
Since model files are ignored by git, they must be generated during deployment. To avoid startup timeouts on Render, train the model during the build stage.

*   **Service Type:** Web Service
*   **Build Command:** `pip install -r requirements.txt && python -m app.train`
*   **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---
⭐ *If you found this project useful, consider giving it a star!*
