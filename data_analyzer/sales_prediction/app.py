import os
import sys
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


from django.conf import settings


USE_MYSQL = os.environ.get("USE_MYSQL", "False").lower() in ("true", "1")

if USE_MYSQL:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
        db_config = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': os.environ.get('MYSQL_DATABASE', 'sales_db'),
                'USER': os.environ.get('MYSQL_USER', 'root'),
                'PASSWORD': os.environ.get('MYSQL_PASSWORD', ''),
                'HOST': os.environ.get('MYSQL_HOST', '127.0.0.1'),
                'PORT': os.environ.get('MYSQL_PORT', '3306'),
            }
        }
    except Exception:
        # Graceful fallback to SQLite if PyMySQL or MySQL server is unavailable
        db_config = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'sales_db.sqlite3',
            }
        }
else:
    db_config = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'sales_db.sqlite3',
        }
    }

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='sales-profit-loss-analyzer-secret-key-for-college-demo',
        ROOT_URLCONF=__name__,
        ALLOWED_HOSTS=['*'],
        INSTALLED_APPS=[
            'django.contrib.staticfiles',
        ],
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [BASE_DIR],
            'APP_DIRS': False,
        }],
        STATIC_URL='/static/',
        STATICFILES_DIRS=[BASE_DIR],
        DATABASES=db_config,
    )

import django
django.setup()

from django.urls import path
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.management import execute_from_command_line


import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression



def find_column_name(df, candidate_names):
    """
    Case-insensitive search for a column name in the DataFrame.
    Matches exact clean names first, then checks substring containment.
    """
    col_mapping = {col.strip().lower(): col for col in df.columns}
    
    # 1. Exact match
    for cand in candidate_names:
        c_low = cand.lower()
        if c_low in col_mapping:
            return col_mapping[c_low]

    # 2. Substring match
    for cand in candidate_names:
        c_low = cand.lower()
        for k in col_mapping:
            if c_low in k:
                return col_mapping[k]

    return None


def clean_numeric_series(series):
    """
    Cleans numeric columns by stripping currency symbols ($), commas, and spaces,
    then converts invalid entries to 0.0.
    """
    if series.dtype == object:
        series = (
            series.astype(str)
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
    return pd.to_numeric(series, errors='coerce').fillna(0.0)


def process_and_analyze_dataset(uploaded_file, filename):
    """
    Parses CSV/Excel file, groups daily records by month if necessary,
    computes sales, profit, loss, and forecasts next month via Linear Regression.
    """
    ext = os.path.splitext(filename)[1].lower()

    # Step A: Read File
    try:
        if ext == '.csv':
            df = pd.read_csv(uploaded_file)
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(uploaded_file)
        else:
            raise ValueError("Unsupported file format. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file.")
    except Exception as e:
        raise ValueError(f"Failed to read file: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded dataset is empty. Please upload a file containing data rows.")

    # Step B: Identify Required and Optional Columns
    date_col = find_column_name(df, ['month', 'date', 'order_date', 'period', 'sales_date', 'time', 'day'])
    sales_col = find_column_name(df, ['sales', 'revenue', 'turnover', 'amount', 'total_sales'])
    cost_col = find_column_name(df, ['cost', 'expenses', 'expense', 'cogs', 'spending', 'cost_price'])
    profit_col = find_column_name(df, ['profit', 'net_profit', 'gain', 'net profit', 'earnings'])

    if not sales_col:
        raise ValueError(
            "Could not identify a Sales or Revenue column. Please ensure your file has a column named 'Sales' or 'Revenue'."
        )

    # Clean numeric columns
    df[sales_col] = clean_numeric_series(df[sales_col])
    if cost_col:
        df[cost_col] = clean_numeric_series(df[cost_col])
    if profit_col:
        df[profit_col] = clean_numeric_series(df[profit_col])


    group_by_cols = []
    sort_key = None

    if date_col:
        # Check if column contains parseable dates
        try:
            parsed_dates = pd.to_datetime(df[date_col], format='mixed', errors='coerce')
        except Exception:
            parsed_dates = pd.to_datetime(df[date_col], errors='coerce')
        if parsed_dates.notna().sum() >= len(df) * 0.5:
            # Datetime values detected: Group by Year-Month period
            df['_SortPeriod'] = parsed_dates.dt.to_period('M')
            df['Month_Formatted'] = parsed_dates.dt.strftime('%b %Y')
            group_by_cols = ['_SortPeriod', 'Month_Formatted']
            sort_key = '_SortPeriod'
        else:
            # Categorical month strings (e.g., 'Month 1', 'Jan', 'February')
            df['Month_Formatted'] = df[date_col].astype(str).str.strip()
            group_by_cols = ['Month_Formatted']
    else:
        # If no date/month column provided, synthesize sequential Month labels
        df['Month_Formatted'] = [f"Month {i + 1}" for i in range(len(df))]
        group_by_cols = ['Month_Formatted']

    agg_dict = {sales_col: 'sum'}
    if profit_col:
        agg_dict[profit_col] = 'sum'
    if cost_col:
        agg_dict[cost_col] = 'sum'

    monthly_df = df.groupby(group_by_cols, as_index=False, sort=False)[list(agg_dict.keys())].sum()

    if sort_key and sort_key in monthly_df.columns:
        monthly_df = monthly_df.sort_values(by=sort_key).reset_index(drop=True)

    num_months = len(monthly_df)
    if num_months < 2:
        raise ValueError(
            f"At least 2 historical months are required to perform Linear Regression forecasting. Found only {num_months} month(s)."
        )

    # Step E: Profit and Loss Calculation Logic
    has_profit_info = True
    if profit_col:
        # Rule: If profit column already exists, use it directly
        monthly_df['calc_profit_loss'] = monthly_df[profit_col]
    elif cost_col:
        # Rule: Profit/Loss = Sales - Cost
        monthly_df['calc_profit_loss'] = monthly_df[sales_col] - monthly_df[cost_col]
    else:

        has_profit_info = False
        monthly_df['calc_profit_loss'] = 0.0


    monthly_df['table_sales'] = monthly_df[sales_col].round(2)
    monthly_df['table_profit'] = monthly_df['calc_profit_loss'].apply(lambda x: round(x, 2) if x > 0 else 0.0)
    monthly_df['table_loss'] = monthly_df['calc_profit_loss'].apply(lambda x: round(abs(x), 2) if x < 0 else 0.0)

    # Calculate Overall Summaries:
    # 1. Total Sales = Sum of all sales values
    total_sales = float(monthly_df['table_sales'].sum())

    # 2. Total Profit = Sum of positive profit values
    total_profit = float(monthly_df['table_profit'].sum()) if has_profit_info else 0.0

    # 3. Total Loss = Absolute sum of negative profit values
    total_loss = float(monthly_df['table_loss'].sum()) if has_profit_info else 0.0

    # 4. Net Profit/Loss = Total Profit - Total Loss
    net_profit_loss = (total_profit - total_loss) if has_profit_info else 0.0
    net_status = "Profit" if net_profit_loss >= 0 else "Loss"

    # Step F: Next-Month Prediction using Scikit-learn Linear Regression
    X = np.arange(1, num_months + 1).reshape(-1, 1)
    y_sales = monthly_df['table_sales'].values

    # Train Linear Regression for Sales
    model_sales = LinearRegression()
    model_sales.fit(X, y_sales)

    # Predict Next Month (Month N + 1)
    next_month_num = num_months + 1
    pred_sales_raw = float(model_sales.predict([[next_month_num]])[0])
    predicted_sales = max(0.0, round(pred_sales_raw, 2))

    # Predict Next Month Profit/Loss
    if has_profit_info:
        y_profit_loss = monthly_df['calc_profit_loss'].values
        model_profit = LinearRegression()
        model_profit.fit(X, y_profit_loss)

        pred_profit_raw = float(model_profit.predict([[next_month_num]])[0])
        pred_profit_rounded = round(pred_profit_raw, 2)

        if pred_profit_rounded >= 0:
            predicted_profit = pred_profit_rounded
            predicted_loss = 0.0
        else:
            predicted_profit = 0.0
            predicted_loss = abs(pred_profit_rounded)
    else:
        predicted_profit = None
        predicted_loss = None

 
    last_month_name = str(monthly_df['Month_Formatted'].iloc[-1])
    if "month" in last_month_name.lower():
        next_month_label = f"Month {next_month_num} (Predicted)"
    else:
        next_month_label = f"Month {next_month_num} (Next-Month Forecast)"


    monthly_records = []
    for idx, row in monthly_df.iterrows():
        monthly_records.append({
            'month': str(row['Month_Formatted']),
            'sales': float(row['table_sales']),
            'profit': float(row['table_profit']),
            'loss': float(row['table_loss']),
        })


    labels = [r['month'] for r in monthly_records] + [next_month_label]
    actual_series = [r['sales'] for r in monthly_records] + [None]


    predicted_series = [None] * (num_months - 1) + [actual_series[num_months - 1], predicted_sales]

    return {
        'success': True,
        'summary': {
            'total_sales': round(total_sales, 2),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'net_profit_loss': round(net_profit_loss, 2),
            'net_status': net_status,
            'has_profit_info': has_profit_info,
        },
        'prediction': {
            'next_month_label': next_month_label,
            'predicted_sales': predicted_sales,
            'predicted_profit': predicted_profit,
            'predicted_loss': predicted_loss,
            'has_profit_info': has_profit_info,
            'note': 'Estimated via Scikit-learn Linear Regression',
        },
        'monthly_data': monthly_records,
        'chart_data': {
            'labels': labels,
            'actual_sales': actual_series,
            'predicted_sales': predicted_series,
        }
    }


def index_view(request):
    """
    Renders the single-page application dashboard.
    No login credentials or authentication required.
    """
    return render(request, 'index.html')


@csrf_exempt
def analyze_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method. Please use POST.'}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded. Please select a CSV or Excel file.'}, status=400)

    uploaded_file = request.FILES['file']
    filename = uploaded_file.name

    try:
        results = process_and_analyze_dataset(uploaded_file, filename)
        return JsonResponse(results)
    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'}, status=500)




urlpatterns = [
    path('', index_view, name='home'),
    path('analyze/', analyze_view, name='analyze'),
]



if __name__ == '__main__':

    if len(sys.argv) == 1:
        sys.argv.extend(['runserver', '127.0.0.1:8000', '--noreload'])

    print("=" * 76)
    print(" Sales Profit & Loss Analysis with Next-Month Prediction")
    print("=" * 76)
    print(" Backend: Python & Django")
    print(" Machine Learning: Scikit-learn (Linear Regression)")
    print(" Data Processing: Pandas & NumPy")
    print(" Web Dashboard: http://127.0.0.1:8000/")
    print(" Press CTRL+C to stop the server.")
    print("=" * 76)

    execute_from_command_line(sys.argv)
