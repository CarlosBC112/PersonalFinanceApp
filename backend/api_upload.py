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
        with conn.cursor() as cursor:
            for row in reader:
                transaction_date = row.get('transaction_date') or row.get('Transaction Date') or row.get('date') or row.get('Date')
                description = row.get('description') or row.get('Description')
                amount = row.get('amount') or row.get('Amount') or '0'
                # Check for duplicate
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM transactions_staging
                    WHERE transaction_date = %s AND description = %s AND amount = %s
                """, (transaction_date, description, amount))
                result = cursor.fetchone()
                if result['cnt'] == 0:
                    cursor.execute("""
                        INSERT INTO transactions_staging 
                        (transaction_date, post_date, description, category, type, amount, memo) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        transaction_date,
                        row.get('post_date') or row.get('Post Date') or row.get('date') or row.get('Date'),
                        description,
                        row.get('category') or row.get('Category'),
                        row.get('type') or row.get('Type') or 'expense',
                        amount,
                        row.get('memo') or row.get('Memo') or ''
                    ))
                    inserted_count += 1
            conn.commit()
        conn.close()
        return {
            "success": True, 
            "message": f"CSV uploaded successfully. {inserted_count} new transactions imported."
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
                ORDER BY staging_id DESC
                LIMIT 100
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
                    SUM(CAST(amount AS DECIMAL(12,2))) as total,
                    COUNT(*) as transactions
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
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
                    SUM(CAST(amount AS DECIMAL(12,2))) as totalSpending,
                    AVG(CAST(amount AS DECIMAL(12,2))) as dailyAverage,
                    COUNT(*) as transactionCount
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
            """)
            summary = cursor.fetchone()
            
            # Get category breakdown
            cursor.execute("""
                SELECT 
                    COALESCE(category, 'Uncategorized') as category,
                    SUM(CAST(amount AS DECIMAL(12,2))) as amount,
                    COUNT(*) as count
                FROM transactions_staging
                WHERE transaction_date IS NOT NULL AND transaction_date != ''
                GROUP BY category
                ORDER BY amount DESC
            """)
            categories = cursor.fetchall()
            
            # Calculate percentages
            total = float(summary['totalSpending'] or 1)
            category_breakdown = []
            for cat in categories:
                category_breakdown.append({
                    'category': cat['category'],
                    'amount': float(cat['amount']),
                    'percent': (float(cat['amount']) / total) * 100
                })
            
            # Simple trend data (just return empty for now)
            trend = []
            
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
            "incomeVsExpenses": []
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Get monthly analytics error: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))
