import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='sales-profit-loss-analyzer-beginner-friendly-key',
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
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        },
    )

import django
django.setup()

from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.management import execute_from_command_line

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def find_column_name(df, candidate_names):
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

    if series.dtype == object:
        series = (
            series.astype(str)
            .str.replace('₹', '', regex=False)
            .str.replace('Rs.', '', regex=False)
            .str.replace('Rs', '', regex=False)
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
    return pd.to_numeric(series, errors='coerce').fillna(0.0)


def process_and_analyze_dataset(uploaded_file, filename):

    ext = os.path.splitext(filename)[1].lower()

    #Read File
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

    # Identify Required and Optional Columns
    date_col = find_column_name(df, ['month', 'date', 'order_date', 'period', 'sales_date', 'time', 'day'])
    sales_col = find_column_name(df, ['sales', 'revenue', 'turnover', 'amount', 'total_sales'])
    cost_col = find_column_name(df, ['cost', 'expenses', 'expense', 'cogs', 'spending', 'cost_price'])
    profit_col = find_column_name(df, ['profit', 'net_profit', 'gain', 'net profit', 'earnings'])
    product_col = find_column_name(df, ['product', 'product_name', 'product name', 'item', 'item_name', 'item name', 'product_title', 'title', 'sku', 'description'])
    quantity_col = find_column_name(df, ['quantity', 'qty', 'units', 'units_sold', 'units sold', 'volume', 'quantity_sold', 'quantity sold', 'order_quantity', 'count'])

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

    if product_col:
        df['_Product_Clean'] = df[product_col].astype(str).str.strip()
    else:
        df['_Product_Clean'] = 'General Merchandise'

    if quantity_col:
        df['_Quantity_Clean'] = clean_numeric_series(df[quantity_col])
    else:
        df['_Quantity_Clean'] = 1.0

    # Handle Date / Month Grouping (Daily to Monthly if needed)
    group_by_cols = []
    sort_key = None

    if date_col:
        try:
            parsed_dates = pd.to_datetime(df[date_col], format='mixed', errors='coerce')
        except Exception:
            parsed_dates = pd.to_datetime(df[date_col], errors='coerce')
        if parsed_dates.notna().sum() >= len(df) * 0.5:
            df['_SortPeriod'] = parsed_dates.dt.to_period('M')
            df['Month_Formatted'] = parsed_dates.dt.strftime('%b %Y')
            group_by_cols = ['_SortPeriod', 'Month_Formatted']
            sort_key = '_SortPeriod'
        else:
            df['Month_Formatted'] = df[date_col].astype(str).str.strip()
            group_by_cols = ['Month_Formatted']
    else:
        df['Month_Formatted'] = [f"Month {i + 1}" for i in range(len(df))]
        group_by_cols = ['Month_Formatted']

    # Aggregation by Month (Monthly Total Quantity, Sales, Cost, Profit)
    agg_dict = {
        sales_col: 'sum',
        '_Quantity_Clean': 'sum',
    }
    if profit_col:
        agg_dict[profit_col] = 'sum'
    if cost_col:
        agg_dict[cost_col] = 'sum'

    monthly_df = df.groupby(group_by_cols, as_index=False, sort=False)[list(agg_dict.keys())].sum()

    if sort_key and sort_key in monthly_df.columns:
        monthly_df = monthly_df.sort_values(by=sort_key).reset_index(drop=True)

    num_months = len(monthly_df)
    if num_months < 1:
        raise ValueError(
            "The uploaded dataset does not contain any valid data rows."
        )

    # Profit and Loss Calculation Logic
    has_profit_info = True
    if profit_col:
        monthly_df['calc_profit_loss'] = monthly_df[profit_col]
        df['_calc_profit_loss'] = df[profit_col]
    elif cost_col:
        monthly_df['calc_profit_loss'] = monthly_df[sales_col] - monthly_df[cost_col]
        df['_calc_profit_loss'] = df[sales_col] - df[cost_col]
    else:
        has_profit_info = False
        monthly_df['calc_profit_loss'] = 0.0
        df['_calc_profit_loss'] = 0.0

    # Monthly table values
    monthly_df['table_sales'] = monthly_df[sales_col].round(2)
    monthly_df['table_quantity'] = monthly_df['_Quantity_Clean'].round(0).astype(int)
    monthly_df['table_profit'] = monthly_df['calc_profit_loss'].apply(lambda x: round(x, 2) if x > 0 else 0.0)
    monthly_df['table_loss'] = monthly_df['calc_profit_loss'].apply(lambda x: round(abs(x), 2) if x < 0 else 0.0)

    # Calculate Overall Summaries:
    total_sales = float(monthly_df['table_sales'].sum())
    total_quantity = int(monthly_df['table_quantity'].sum())
    total_profit = float(monthly_df['table_profit'].sum()) if has_profit_info else 0.0
    total_loss = float(monthly_df['table_loss'].sum()) if has_profit_info else 0.0
    net_profit_loss = (total_profit - total_loss) if has_profit_info else 0.0
    net_status = "Profit" if net_profit_loss >= 0 else "Loss"

    # Next-Month Prediction
    next_month_num = num_months + 1

    if num_months == 1:
        predicted_sales = max(0.0, round(float(monthly_df['table_sales'].iloc[0]), 2))
        predicted_quantity = max(0, int(monthly_df['table_quantity'].iloc[0]))

        if has_profit_info:
            p_val = float(monthly_df['calc_profit_loss'].iloc[0])
            if p_val >= 0:
                predicted_profit = round(p_val, 2)
                predicted_loss = 0.0
            else:
                predicted_profit = 0.0
                predicted_loss = round(abs(p_val), 2)
        else:
            predicted_profit = None
            predicted_loss = None

        prediction_note = "Estimated for Month 2 based on Month 1 performance baseline"
    else:
        X = np.arange(1, num_months + 1).reshape(-1, 1)
        y_sales = monthly_df['table_sales'].values

        # Predict Next Month Sales
        model_sales = LinearRegression().fit(X, y_sales)
        pred_sales_raw = float(model_sales.predict([[next_month_num]])[0])
        predicted_sales = max(0.0, round(pred_sales_raw, 2))

        # Predict Next Month Quantity
        y_qty = monthly_df['table_quantity'].values
        model_qty = LinearRegression().fit(X, y_qty)
        pred_qty_raw = float(model_qty.predict([[next_month_num]])[0])
        predicted_quantity = max(0, int(round(pred_qty_raw)))

        # Predict Next Month Profit/Loss
        if has_profit_info:
            y_profit_loss = monthly_df['calc_profit_loss'].values
            model_profit = LinearRegression().fit(X, y_profit_loss)
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

        prediction_note = "Estimated via Scikit-learn Linear Regression"

    #Label for Next Month (e.g., 'Month 2 (Predicted)' or 'Month 7 (Predicted)')
    last_month_name = str(monthly_df['Month_Formatted'].iloc[-1])
    if "month" in last_month_name.lower():
        next_month_label = f"Month {next_month_num} (Predicted)"
    else:
        try:
            if sort_key and sort_key in monthly_df.columns:
                next_period = monthly_df[sort_key].iloc[-1] + 1
                next_month_label = f"{next_period.strftime('%b %Y')} (Predicted)"
            else:
                next_month_label = f"Month {next_month_num} (Next-Month Forecast)"
        except Exception:
            next_month_label = f"Month {next_month_num} (Next-Month Forecast)"

    # Prepare Monthly Table Records (Shows Month, Total Quantity, Sales, Profit, Loss)
    monthly_records = []
    for idx, row in monthly_df.iterrows():
        monthly_records.append({
            'month': str(row['Month_Formatted']),
            'quantity': int(row['table_quantity']),
            'sales': float(row['table_sales']),
            'profit': float(row['table_profit']),
            'loss': float(row['table_loss']),
        })

    #Prepare Product Performance Breakdown (Product, Quantity Sold, Sales, Profit, Loss, Share)
    prod_agg = {
        sales_col: 'sum',
        '_Quantity_Clean': 'sum',
        '_calc_profit_loss': 'sum'
    }
    prod_df = df.groupby('_Product_Clean', as_index=False).agg(prod_agg).sort_values(by=sales_col, ascending=False)

    product_records = []
    for _, p_row in prod_df.iterrows():
        p_sales = round(float(p_row[sales_col]), 2)
        p_qty = int(round(float(p_row['_Quantity_Clean'])))
        p_net = float(p_row['_calc_profit_loss']) if has_profit_info else 0.0
        p_profit = round(p_net, 2) if p_net > 0 else 0.0
        p_loss = round(abs(p_net), 2) if p_net < 0 else 0.0
        p_pct = round((p_sales / total_sales * 100), 1) if total_sales > 0 else 0.0

        product_records.append({
            'product': str(p_row['_Product_Clean']),
            'quantity_sold': p_qty,
            'sales': p_sales,
            'profit': p_profit,
            'loss': p_loss,
            'sales_share_pct': p_pct,
        })

    #Product Insights and Stock Recommendation
    if len(product_records) > 0:
        top_p = product_records[0]
        top_name = top_p['product']
        top_sales_val = top_p['sales']
        top_share = top_p['sales_share_pct']

        # Product with highest quantity sold
        top_qty_p = max(product_records, key=lambda x: x['quantity_sold'])
        top_qty_name = top_qty_p['product']
        top_qty_val = top_qty_p['quantity_sold']

        top_selling_text = f"Highest Sales Product: {top_name} with revenue of ₹{top_sales_val:,.2f} ({top_share}% of total sales)."

        if len(product_records) > 1:
            if top_name == top_qty_name:
                recommendation_text = f"Recommendation for Month {next_month_num}: Increase stock and marketing for {top_name}. It has both the highest sales revenue and highest unit volume ({top_qty_val} units sold)."
            else:
                recommendation_text = f"Recommendation for Month {next_month_num}: Increase stock for {top_name} to drive maximum revenue (₹{top_sales_val:,.2f}), and maintain high inventory for {top_qty_name} due to strong unit demand ({top_qty_val} units sold)."
        else:
            recommendation_text = f"Recommendation for Month {next_month_num}: Increase stock for {top_name} to meet expected customer demand."
    else:
        top_selling_text = None
        recommendation_text = None

    return {
        'success': True,
        'summary': {
            'total_sales': round(total_sales, 2),
            'total_quantity': total_quantity,
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'net_profit_loss': round(net_profit_loss, 2),
            'net_status': net_status,
            'has_profit_info': has_profit_info,
        },
        'prediction': {
            'next_month_label': next_month_label,
            'predicted_sales': predicted_sales,
            'predicted_quantity': predicted_quantity,
            'predicted_profit': predicted_profit,
            'predicted_loss': predicted_loss,
            'has_profit_info': has_profit_info,
            'note': prediction_note,
            'top_selling_text': top_selling_text,
            'recommendation_text': recommendation_text,
        },
        'monthly_data': monthly_records,
        'product_data': product_records,
    }




def index_view(request):

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
    print(" Backend: Python & Django (SQLite Database)")
    print(" Machine Learning: Scikit-learn (Linear Regression)")
    print(" Currency: Indian Rupee (INR - ₹)")
    print(" Web Dashboard: http://127.0.0.1:8000/")
    print(" Press CTRL+C to stop the server.")
    print("=" * 76)

    execute_from_command_line(sys.argv)
