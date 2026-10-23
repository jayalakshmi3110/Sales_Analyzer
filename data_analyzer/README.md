# Sales Profit and Loss Analysis with Next-Month Prediction

A simple, beginner-friendly web application built with **Python**, **Django**, **Pandas**, and **Scikit-learn (Linear Regression)**. It allows users to upload a monthly or daily sales dataset (in CSV or Excel format) to instantly compute financial metrics (Total Sales, Total Profit, Total Loss, Net Profit/Loss) and forecast next-month figures with an interactive **Chart.js** visualization—all on a single, easy-to-use webpage without requiring any login credentials.

---

## Features

- **Direct Access (No Authentication):** Opens directly to the dashboard. No login, registration, or password setup needed.
- **Dual File Support:** Accepts both **CSV** (`.csv`) and **Excel** (`.xlsx`, `.xls`) files.
- **Automatic Data Aggregation:** If daily transaction data is uploaded, it automatically groups rows by month.
- **Results Summary (4 Metric Boxes):**
  1. **Total Sales**
  2. **Total Profit**
  3. **Total Loss**
  4. **Net Profit / Loss** (dynamically colored green for profit, red for loss)
- **Monthly Analysis Table:** Displays Month, Sales, Profit, and Loss with full summary totals.
- **Machine Learning Next-Month Prediction:** Uses Scikit-learn's `LinearRegression` algorithm to forecast:
  - Predicted Sales
  - Predicted Profit
  - Predicted Loss
  - Clearly labeled as mathematical estimates.
- **Actual vs. Predicted Sales Chart:** Interactive line chart powered by **Chart.js** comparing actual historical monthly performance with next-month forecasts.
- **Smart Column Detection:** Flexible column recognition (`Date`, `Month`, `Sales`, `Revenue`, `Cost`, `Expenses`, `Profit`).
- **Beginner-Friendly Architecture:** Clean, well-commented code designed for academic project submissions and viva explanations.

---

## Technologies Used

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Django Web Framework |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn (`LinearRegression`) |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Visualization** | Chart.js |
| **Supported Formats** | CSV (`.csv`) and Excel (`.xlsx`, `.xls`) |

---

##  Project Folder Structure

```text
sales_prediction/
│
├── app.py                         # Single-file Django backend, ML logic & API endpoints
├── index.html                     # Frontend user interface (Bootstrap 5 & Chart.js)
├── style.css                      # Custom light-blue styling & responsive layout
├── sample_sales_data.csv          # Sample 6-month monthly dataset
├── sample_daily_transactions.xlsx # Sample daily Excel dataset
└── README.md                      # Documentation & local setup instructions


##  Calculation & Machine Learning Logic

### 1. Financial Calculations
- **Total Sales:** Sum of all sales values across all months.
- **Monthly Profit / Loss:**
  - If a dedicated `Profit` column exists in the dataset, it is used directly.
  - Otherwise, if `Cost` is available: $\text{Profit/Loss} = \text{Sales} - \text{Cost}$.
  - If both cost and profit information are missing, the app clearly displays an alert stating profit and loss cannot be calculated, while still providing sales analysis and sales prediction.
- **Total Profit:** Sum of all positive monthly profit values ($\text{Profit} > 0$).
- **Total Loss:** Absolute sum of all negative monthly profit values ($\text{Profit} < 0$).
- **Net Profit / Loss:** $\text{Total Profit} - \text{Total Loss}$.

### 2. Next-Month Forecasting (Linear Regression)
- **Algorithm:** Ordinary Least Squares Linear Regression (`sklearn.linear_model.LinearRegression`).
- **Feature ($X$):** Sequential time index of months ($1, 2, 3, \dots, N$).
- **Target ($y$):** Historical monthly values for Sales and Profit/Loss.
- **Next Month ($N + 1$):**
  $$\hat{y}_{N+1} = \beta_0 + \beta_1 \cdot (N + 1)$$
- All predicted values are clearly marked as **Estimated Values**.

---

## Quick Start Guide (Running Locally)

### Prerequisites
Make sure **Python 3.8+** and `pip` are installed on your computer.

### Step 1: Open Terminal / Command Prompt
Navigate to the project folder:
```bash
cd sales_prediction
```

### Step 2: Install Required Dependencies
Run the following command in your terminal:
```bash
pip install django pandas numpy scikit-learn openpyxl
```

*(Optional: If you wish to connect to a MySQL database, also install `pymysql`:)*
```bash
pip install pymysql
```

### Step 3: Start the Application
Run the application using Python:
```bash
python app.py
```

### Step 4: Open in Your Browser
Open any web browser (Chrome, Edge, Firefox, Safari) and go to:
http://127.0.0.1:8000/


## Database Configuration 

- **Default (Plug-and-Play):** By default, Django automatically uses **SQLite** (`sales_db.sqlite3`). This allows the project to run immediately without installing or configuring any database server.
- **Using MySQL (for College/Viva Requirement):**
  1. Start your local MySQL server (via XAMPP, WAMP, or MySQL Service).
  2. Create a database:
     ```sql
     CREATE DATABASE sales_db;
     ```
  3. Start the server with `USE_MYSQL=True`:
     - **Windows PowerShell:**
       ```powershell
       $env:USE_MYSQL="True"; python app.py
       ```
     - **Linux / macOS / Bash:**
       ```bash
       USE_MYSQL=True python app.py
       ```

---

## Testing with Sample Datasets

Two ready-to-use sample datasets are included:

1. **`sample_sales_data.csv`**: A 6-month historical dataset containing `Month`, `Sales`, and `Cost`.
2. **`sample_daily_transactions.xlsx`**: An Excel file with individual daily transactions across 4 months. Upload this file to see automatic monthly grouping in action.


