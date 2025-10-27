# within a route or script using SessionLocal
from db import SessionLocal
from models import Transaction, Category

sess = SessionLocal()
tx = Transaction(user_id=1, account_id=None, posted_date='2025-10-01',
                 amount=-45.32, description="AMZN MKTP US*ABC123",
                 merchant="Amazon", raw_text="AMZN MKTP...")

# classification
cat_name, conf = rule_classify(tx.description)
if not cat_name:
    cat_name, conf = ai_classify_openai(tx.description, your_client, categories_list)
cat = sess.query(Category).filter_by(name=cat_name).first()
tx.category_id = cat.id if cat else None
tx.category_source = 'rule' if conf and conf > 0.9 else 'ai'
tx.ai_confidence = float(conf) if conf else None

sess.add(tx)
sess.commit()
