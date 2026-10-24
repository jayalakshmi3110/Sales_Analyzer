# Sales Profit and Loss Analysis with Next-Month Prediction

A simple, beginner-friendly web application built with **Python**, **Django**, **Pandas**, and **Scikit-learn (Linear Regression)**. It allows users to upload a monthly or daily sales dataset (in CSV or Excel format) to instantly compute financial metrics (Total Sales, Total Profit, Total Loss, Net Profit/Loss) and forecast next-month figures with an interactive **Chart.js** visualization—all on a single, easy-to-use webpage without requiring any login credentials.

##  Features

- **Direct Access (No Authentication):** Opens directly to the dashboard. No login, registration, or password setup needed.
- **Dual File Support:** Accepts both **CSV** (`.csv`) and **Excel** (`.xlsx`, `.xls`) files.
- **Automatic Data Aggregation:** If daily transaction data is uploaded, it automatically groups rows by month.
- **Single-Month & Multi-Month Support:** Works smoothly whether the user uploads **1 month of data** (predicts **Month 2** with stock recommendations) or **multi-month data** (predicts Month $N+1$ using Linear Regression).
- **Product Sales & Stock Increase Recommendation:** Automatically identifies which product had the highest sales revenue and recommends which product to increase inventory for in the upcoming month.
- **Results Summary (5 Metric Boxes):**
  1. Total Sales (₹)
  2. Total Units Sold (Units)
  3. Total Profit (₹)
  4. Total Loss (₹)
  5. Net Profit / Loss (₹)
- **Monthly Analysis Table:** Displays Month, Total Quantity, Sales (₹), Profit (₹), and Loss (₹) with totals footer.
- **Product Performance Breakdown Table:** Displays Product Name, Total Units Sold, Total Sales (₹), Total Profit (₹), Total Loss (₹), and Revenue Share (%).
- **Machine Learning Next-Month Prediction:** Uses Scikit-learn's `LinearRegression` algorithm to forecast:
  - Predicted Sales (₹)
  - Predicted Quantity (Units)
  - Predicted Profit (₹)
  - Predicted Loss (₹)
- **Smart Column Detection:** Flexible column recognition (`Date`, `Month`, `Sales`, `Revenue`, `Cost`, `Expenses`, `Profit`).

## Technologies Used

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Django Web Framework |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn (`LinearRegression`) |
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Database** | SQLite (Standard Library, No server setup required) |
| **Supported Formats** | CSV (`.csv`) and Excel (`.xlsx`, `.xls`) |

