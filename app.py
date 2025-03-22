from flask import Flask, request, render_template, redirect, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from xhtml2pdf import pisa  # PDF生成用ライブラリ
from io import BytesIO  # メモリ内でPDFを生成するために使用

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kakeibo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# データベースのモデル（収支の記録）
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.today)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # "income" or "expense"

# 📝 収支登録ページ（フォーム表示 & データ追加）
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        date = datetime.strptime(request.form['date'], "%Y-%m-%d")
        category = request.form['category']
        amount = int(request.form['amount'])
        type = request.form['type']

        new_transaction = Transaction(date=date, category=category, amount=amount, type=type)
        db.session.add(new_transaction)
        db.session.commit()
        return redirect('/list')

    return render_template('add.html')

# 📜 収支一覧ページ（データ表示）
@app.route('/list')
def list_transactions():
    sort = request.args.get('sort', 'date')  # ソート（デフォルト：日付）
    order = request.args.get('order', 'desc')  # 昇順 or 降順
    filter_type = request.args.get('type', 'all')  # 絞り込み（all, income, expense）

    # ソート条件
    column = Transaction.date if sort == 'date' else Transaction.amount

    # 並び順
    transactions = Transaction.query.order_by(column.asc() if order == 'asc' else column.desc())

    # 収入 or 支出の絞り込み
    if filter_type == 'income':
        transactions = transactions.filter_by(type='income')
    elif filter_type == 'expense':
        transactions = transactions.filter_by(type='expense')

    transactions = transactions.all()

    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')

    return render_template(
        'list.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense,
        sort=sort,
        order=order,
        filter_type=filter_type
    )

# 📄 家計簿をPDFとして保存
@app.route('/export/pdf')
def export_pdf():
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')

    # HTMLテンプレートをPDFに変換
    rendered_html = render_template(
        'export_pdf.html',
        transactions=transactions,
        total_income=total_income,
        total_expense=total_expense
    )
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(rendered_html.encode('utf-8'), pdf)  # UTF-8でエンコード

    if pisa_status.err:
        return "PDF生成中にエラーが発生しました", 500

    pdf.seek(0)
    return Response(pdf, mimetype='application/pdf', headers={
        "Content-Disposition": "attachment;filename=kakeibo.pdf"
    })

# ✏️ 収支の編集ページ
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    transaction = db.session.get(Transaction, id)
    if not transaction:
        return redirect('/list')

    if request.method == 'POST':
        transaction.date = datetime.strptime(request.form['date'], "%Y-%m-%d")
        transaction.category = request.form['category']
        transaction.amount = int(request.form['amount'])
        transaction.type = request.form['type']

        db.session.commit()
        return redirect('/list')

    return render_template('edit.html', transaction=transaction)

# 🗑 収支の削除
@app.route('/delete/<int:id>')
def delete(id):
    transaction = db.session.get(Transaction, id)
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
    return redirect('/list')

# データベース初期化
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
