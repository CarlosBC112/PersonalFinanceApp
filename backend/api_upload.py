from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymysql
import csv
import io
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MySQL connection settings
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "fintrack")

# Category color mapping
CATEGORY_COLORS = {
    'Housing': {'color': '#3b82f6', 'accentClass': 'bg-blue-600'},
    'Home': {'color': '#3b82f6', 'accentClass': 'bg-blue-600'},
    'Transportation': {'color': '#f97316', 'accentClass': 'bg-orange-500'},
    'Food': {'color': '#10b981', 'accentClass': 'bg-green-500'},
    'Food & Dining': {'color': '#10b981', 'accentClass': 'bg-green-500'},
    'Food & Drink': {'color': '#ef4444', 'accentClass': 'bg-red-500'},
    'Groceries': {'color': '#10b981', 'accentClass': 'bg-emerald-500'},
    'Restaurants': {'color': '#84cc16', 'accentClass': 'bg-lime-500'},
    'Utilities': {'color': '#eab308', 'accentClass': 'bg-yellow-500'},
    'Bills & Utilities': {'color': '#eab308', 'accentClass': 'bg-yellow-500'},
    'Insurance': {'color': '#a855f7', 'accentClass': 'bg-purple-500'},
    'Medical & Healthcare': {'color': '#ef4444', 'accentClass': 'bg-red-500'},
    'Healthcare': {'color': '#ef4444', 'accentClass': 'bg-red-500'},
    'Health & Wellness': {'color': '#ef4444', 'accentClass': 'bg-red-500'},
    'Personal': {'color': '#ec4899', 'accentClass': 'bg-pink-500'},
    'Personal Care': {'color': '#ec4899', 'accentClass': 'bg-pink-500'},
    'Recreation and Entertainment': {'color': '#6366f1', 'accentClass': 'bg-indigo-500'},
    'Entertainment': {'color': '#6366f1', 'accentClass': 'bg-indigo-500'},
    'Shopping': {'color': '#8b5cf6', 'accentClass': 'bg-violet-500'},
    'General Merchandise': {'color': '#8b5cf6', 'accentClass': 'bg-violet-500'},
    'Education': {'color': '#f97316', 'accentClass': 'bg-orange-500'},
    'Travel': {'color': '#0ea5e9', 'accentClass': 'bg-sky-600'},
    'Bills': {'color': '#facc15', 'accentClass': 'bg-yellow-400'},
    'Gas': {'color': '#f59e0b', 'accentClass': 'bg-amber-500'},
    'Gas & Fuel': {'color': '#f59e0b', 'accentClass': 'bg-amber-500'},
    'Professional Services': {'color': '#475569', 'accentClass': 'bg-slate-500'},
    'Gifts & Donations': {'color': '#f43f5e', 'accentClass': 'bg-rose-600'},
    'Gifts': {'color': '#f43f5e', 'accentClass': 'bg-rose-600'},
    'Miscellaneous': {'color': '#6b7280', 'accentClass': 'bg-gray-500'},
}

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process a CSV file of transactions"""
    try:
        # Read file content
        contents = await file.read()
        decoded_content = contents.decode('utf-8')
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(decoded_content))
        
        # Connect to database
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        inserted_count = 0
        skipped_count = 0
        with conn.cursor() as cursor:
            for row in reader:
                # Extract transaction data
                transaction_date = row.get('transaction_date') or row.get('Transaction Date') or row.get('date') or row.get('Date')
                post_date = row.get('post_date') or row.get('Post Date') or row.get('date') or row.get('Date')
                description = row.get('description') or row.get('Description')
                category = row.get('category') or row.get('Category')
                trans_type = row.get('type') or row.get('Type') or 'expense'
                amount = row.get('amount') or row.get('Amount') or '0'
                memo = row.get('memo') or row.get('Memo') or ''
                
                # Check for duplicate based on transaction_date, description, and amount
                cursor.execute("""
                    SELECT COUNT(*) as count FROM transactions_staging 
                    WHERE transaction_date = %s 
                    AND description = %s 
                    AND amount = %s
                """, (transaction_date, description, amount))
                
                result = cursor.fetchone()
                if result['count'] > 0:
                    # Skip this transaction as it already exists
                    skipped_count += 1
                    continue
                
                # Insert transaction into staging table with correct column names
                cursor.execute("""
                    INSERT INTO transactions_staging 
                    (transaction_date, post_date, description, category, type, amount, memo) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (transaction_date, post_date, description, category, trans_type, amount, memo))
                inserted_count += 1
            conn.commit()
        conn.close()
        
        # Build message based on results
        message = f"CSV uploaded successfully. {inserted_count} transactions imported."
        if skipped_count > 0:
            message += f" {skipped_count} duplicate(s) skipped."
        
        return {
            "success": True, 
            "message": message
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Upload error: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transactions")
def get_transactions():
    """Get all transactions from the database"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    staging_id as id,
                    description as name,
                    description,
                    category as merchant,
                    category,
                    CAST(amount AS DECIMAL(12,2)) as amount,
                    transaction_date as date,
                    type
                FROM transactions_staging
                ORDER BY STR_TO_DATE(transaction_date, '%m/%d/%Y') DESC, staging_id DESC
            """)
            transactions = cursor.fetchall()
        conn.close()
        return transactions
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Get transactions error: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/daily")
def get_daily_analytics():
    """Get daily spending analytics"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    transaction_date as date,
                    ABS(SUM(CAST(amount AS DECIMAL(12,2)))) as total,
                    COUNT(*) as transactions
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
                AND CAST(amount AS DECIMAL(12,2)) < 0
                GROUP BY transaction_date
                ORDER BY transaction_date DESC
                LIMIT 30
            """)
            daily_data = cursor.fetchall()
        conn.close()
        return daily_data
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Get daily analytics error: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/monthly")
def get_monthly_analytics():
    """Get monthly analytics including summary, trends, and category breakdown"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            # Get total spending
            cursor.execute("""
                SELECT 
                    ABS(SUM(CAST(amount AS DECIMAL(12,2)))) as totalSpending,
                    ABS(AVG(CAST(amount AS DECIMAL(12,2)))) as dailyAverage,
                    COUNT(*) as transactionCount
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
                AND CAST(amount AS DECIMAL(12,2)) < 0
            """)
            summary = cursor.fetchone()
            
            # Get category breakdown
            cursor.execute("""
                SELECT 
                    COALESCE(category, 'Uncategorized') as category,
                    ABS(SUM(CAST(amount AS DECIMAL(12,2)))) as amount,
                    COUNT(*) as count
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
                AND CAST(amount AS DECIMAL(12,2)) < 0
                GROUP BY category
                ORDER BY amount DESC
            """)
            categories = cursor.fetchall()
            
            # Calculate percentages
            total = float(summary['totalSpending'] or 1)
            category_breakdown = []
            for cat in categories:
                cat_name = cat['category']
                color_info = CATEGORY_COLORS.get(cat_name, {'color': '#6b7280', 'accentClass': 'bg-gray-500'})
                category_breakdown.append({
                    'category': cat_name,
                    'amount': float(cat['amount']),
                    'percent': (float(cat['amount']) / total) * 100,
                    'color': color_info['color'],
                    'accentClass': color_info['accentClass']
                })
            
            # Get income vs expenses by month
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(STR_TO_DATE(transaction_date, '%m/%d/%Y'), '%b') as month,
                    DATE_FORMAT(STR_TO_DATE(transaction_date, '%m/%d/%Y'), '%Y-%m') as month_key,
                    SUM(CASE WHEN CAST(amount AS DECIMAL(12,2)) > 0 THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END) as income,
                    ABS(SUM(CASE WHEN CAST(amount AS DECIMAL(12,2)) < 0 THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as expenses
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
                GROUP BY month_key, month
                ORDER BY month_key ASC
                LIMIT 12
            """)
            income_vs_expenses_data = cursor.fetchall()
            
            income_vs_expenses = []
            for row in income_vs_expenses_data:
                income_vs_expenses.append({
                    'month': row['month'],
                    'income': float(row['income']),
                    'expenses': float(row['expenses'])
                })
            
            # Get monthly trend data with category breakdown
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(STR_TO_DATE(transaction_date, '%m/%d/%Y'), '%b') as month,
                    DATE_FORMAT(STR_TO_DATE(transaction_date, '%m/%d/%Y'), '%Y-%m') as month_key,
                    ABS(SUM(CAST(amount AS DECIMAL(12,2)))) as total,
                    ABS(SUM(CASE WHEN category = 'Housing' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as housing,
                    ABS(SUM(CASE WHEN category = 'Food & Dining' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as food,
                    ABS(SUM(CASE WHEN category = 'Transportation' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as transportation,
                    ABS(SUM(CASE WHEN category = 'Utilities' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as utilities,
                    ABS(SUM(CASE WHEN category = 'Insurance' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as insurance,
                    ABS(SUM(CASE WHEN category = 'Medical & Healthcare' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as medical,
                    ABS(SUM(CASE WHEN category = 'Personal Care' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as personal,
                    ABS(SUM(CASE WHEN category = 'Recreation & Entertainment' THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as recreation,
                    ABS(SUM(CASE WHEN category NOT IN ('Housing', 'Food & Dining', 'Transportation', 'Utilities', 'Insurance', 'Medical & Healthcare', 'Personal Care', 'Recreation & Entertainment') THEN CAST(amount AS DECIMAL(12,2)) ELSE 0 END)) as miscellaneous
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
                AND CAST(amount AS DECIMAL(12,2)) < 0
                GROUP BY month_key, month
                ORDER BY month_key ASC
                LIMIT 12
            """)
            trend_data = cursor.fetchall()
            
            trend = []
            for row in trend_data:
                trend.append({
                    'month': row['month'],
                    'total': float(row['total']),
                    'housing': float(row['housing'] or 0),
                    'food': float(row['food'] or 0),
                    'transportation': float(row['transportation'] or 0),
                    'utilities': float(row['utilities'] or 0),
                    'insurance': float(row['insurance'] or 0),
                    'medical': float(row['medical'] or 0),
                    'personal': float(row['personal'] or 0),
                    'recreation': float(row['recreation'] or 0),
                    'miscellaneous': float(row['miscellaneous'] or 0)
                })
            
        conn.close()
        
        return {
            "summary": {
                "totalSpending": float(summary['totalSpending'] or 0),
                "dailyAverage": float(summary['dailyAverage'] or 0),
                "lastMonthTotal": 0,
                "differenceAmount": 0,
                "differencePercent": 0,
                "dailyAverageChange": 0,
                "topCategory": {
                    "name": category_breakdown[0]['category'] if category_breakdown else "None",
                    "amount": category_breakdown[0]['amount'] if category_breakdown else 0,
                    "percent": category_breakdown[0]['percent'] if category_breakdown else 0
                }
            },
            "categoryBreakdown": category_breakdown,
            "trend": trend,
            "incomeVsExpenses": income_vs_expenses
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Get monthly analytics error: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))
