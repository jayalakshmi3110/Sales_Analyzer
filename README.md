# Sales Profit and Loss Analysis with Next-Month Prediction

A simple, beginner-friendly web application built with **Python**, **Django**, **Pandas**, and **Scikit-learn (Linear Regression)**. It allows users to upload a monthly or daily sales dataset (in CSV or Excel format) to instantly compute financial metrics (Total Sales, Total Profit, Total Loss, Net Profit/Loss) and forecast next-month figures with  easy-to-use webpage without requiring any login credentials.

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
- **Smart Column Detection:** Flexible column recognition (`Date`, `Month`, `Sales`, `Revenue`, `Cost`, `Expenses`, `Profit`).
- **Beginner-Friendly Architecture:** Clean, well-commented code designed for academic project submissions and viva explanations.

## Technologies Used

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Django Web Framework |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn (`LinearRegression`) |
| **Supported Formats** | CSV (`.csv`) and Excel (`.xlsx`, `.xls`) |


