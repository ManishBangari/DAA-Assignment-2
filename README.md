# Faculty Allocation System (BTP/MTP)

A **Streamlit-based allocation tool** that assigns students to faculty members based on their CGPA and ranked preferences.

---

## 🚀 Features

- Uploads CSV containing student data (`Roll, Name, Email, CGPA, Faculty columns...`)
- Automatically detects faculty columns (case-insensitive)
- Sorts students by CGPA (descending, stable sort for ties)
- Allocates students in **cycles** of size equal to number of faculties:
  - Each faculty gets at most one student per cycle
  - Students are allocated to their **highest available preference**
- Generates two output CSVs:
  - `output_btp_mtp_allocation.csv` — Final student–faculty mapping  
  - `fac_preference_count.csv` — Number of students choosing each faculty per preference rank
- Works locally or with **Docker**
- Robust error handling and logging

---

## 📁 Project Structure

```
.
├── app.py                   # Main Streamlit application
├── requirements.txt         # Python dependencies
├── Dockerfile               # For building Docker image
├── docker-compose.yml       # For running the app in Docker
├── .gitignore               # Git ignore rules
└── README.md                # Project instructions (this file)
```

---

## 🧠 Input CSV Format

| Roll | Name | Email | CGPA | Faculty_1 | Faculty_2 | Faculty_3 | ... |
|------|------|--------|------|------------|------------|------------|-----|
| 1601CB01 | Alok | random1@gmail.com | 8.21 | 2 | 3 | 1 | ... |

- The faculty columns contain **integer preferences (1 = highest preference)**.
- All columns after `CGPA` are considered faculty columns automatically.
- Column names are **case-insensitive**.

---

## ⚙️ Run Locally (Without Docker)

### 1️⃣ Setup environment
```bash
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Run Streamlit app
```bash
streamlit run app.py
```

### 3️⃣ Open in browser
Go to: **http://localhost:8501**

### 4️⃣ Upload your CSV
- Upload the input file.
- Click **Run allocation**.
- Download the two result CSVs.

---

## 🐳 Run with Docker

### 1️⃣ Build and run
```bash
docker-compose up --build
```

### 2️⃣ Access the app
Open your browser at: **http://localhost:8501**

### 3️⃣ Use the UI
Upload your CSV → Click *Run allocation* → Download results.

---

## 📤 Output Files

1. **`output_btp_mtp_allocation.csv`**
   - Columns: `Roll, Name, Email, CGPA, Allocated`
   - Each student is assigned to one faculty.

2. **`fac_preference_count.csv`**
   - Shows how many students marked each faculty as their 1st, 2nd, 3rd, etc. preference.

---

## 🪶 Notes

- Sorting by CGPA is **descending and stable** (tie-breaking preserves original file order).
- Each faculty can have multiple students overall (across cycles) but only one per cycle.
- Works even if column cases differ (e.g. `cgpa`, `CGPA`, `CgPa`).
- If no faculty is available for a student in a cycle, the code assigns the first available faculty (ensures everyone gets a faculty).


---
