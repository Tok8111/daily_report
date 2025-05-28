import sqlite3
import calendar
import os
from flask import Flask, render_template, request, redirect, url_for, session, g, flash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'your_database.db'  # SQLiteのDBファイル

# ---------------------------
# DB接続管理
# ---------------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        # Flask 実行ファイルと同じ場所にある DB ファイルの絶対パスを取得
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'your_database.db')  # ← ここは正しい DB ファイル名
        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ---------------------------
# カレンダー形式データ作成
# ---------------------------
def generate_calendar(year, month):
    # その月の日数・曜日情報を取得してカレンダー形式データを作成
    cal = calendar.Calendar(firstweekday=6)  # 日曜始まりに調整（必要に応じて）
    month_days = cal.monthdayscalendar(year, month)  # [[日〜土]の日にち(0=空白)]

    return month_days

# ---------------------------
# 利用者一覧データ作成
# ---------------------------
@app.route('/user_list')
def user_list():
    if 'username' not in session or session['role'] != 'staff':
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users WHERE role = 'user'")
    users = cursor.fetchall()
    conn.close()

    return render_template('user_list.html', users=users)

# ---------------------------
# G1.トップページ（ログイン画面）
# ---------------------------
@app.route('/')
def index():
    return render_template('login.html')

# ---------------------------
# ログイン処理
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user['user_id'] # ユーザIDをセッションに保存
            session['username'] = user['username']  # ユーザネームをセッションに保存
            session['role'] = user['role']  # ユーザロールをセッションに保存
            session['name'] = user['name']  # ユーザ氏名をセッションに保存
            return redirect(url_for('main'))
        else:
            return redirect(url_for('login_failure'))
    
    # GETリクエスト時のフォーム表示
    return render_template('login.html')

# ---------------------------
# G2.ログイン失敗処理（ログイン失敗画面へ遷移）
# ---------------------------
@app.route('/login_failure')
def login_failure():
    return render_template('login_failure.html')

# ---------------------------
# G3.メイン画面
# ---------------------------
@app.route('/main', methods=['GET', 'POST'])
def main():
    if 'username' not in session or 'role' not in session:
        return redirect(url_for('index'))

    role = session['role']
    username = session['username']

    calendar_data = None
    year = None
    month = None
    prev_year = prev_month = next_year = next_month = None
    users = []  # 追加：staff用の利用者一覧

    if role == 'user':
        # クエリパラメータから年月取得。無ければ今月
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        today = datetime.today()
        if not year:
            year = today.year
        if not month:
            month = today.month

        calendar_data = generate_calendar(year, month)

        first_day = datetime(year, month, 1)
        prev_month_date = first_day - timedelta(days=1)
        next_month_date = first_day + timedelta(days=31)
        next_month_date = datetime(next_month_date.year, next_month_date.month, 1)

        prev_year, prev_month = prev_month_date.year, prev_month_date.month
        next_year, next_month = next_month_date.year, next_month_date.month

    elif role == 'staff':
        # 利用者一覧を取得
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name FROM users WHERE role = 'user'")
        rows = cursor.fetchall()
        users = [{'id': row['user_id'], 'name': row['name']} for row in rows]
        conn.close()

    return render_template('main.html',
                           username=username,
                           name=session.get('name'),
                           role=role,
                           calendar=calendar_data,
                           year=year,
                           month=month,
                           prev_year=prev_year,
                           prev_month=prev_month,
                           next_year=next_year,
                           next_month=next_month,
                           users=users)  # 追加

# -----------------------
# G4. 日報入力画面のルート
# -----------------------
@app.route('/daily_report_input', methods=['GET', 'POST'])
def daily_report_input():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()

        user_id = session['user_id']
        report_date = request.form['report_date']
        condition = request.form.get('condition')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        # 先に各リスト形式の値を取得
        task_name = request.form.getlist('work_detail[]')
        task_duration = request.form.getlist('work_time[]')
        task_note = request.form.getlist('user_comment[]')

        # コメント文字数バリデーション（各コメントが300文字以内か確認）
        for note in task_note:
            if len(note) > 300:
                flash('利用者コメントは300文字以内で入力してください。')
                return redirect(url_for('daily_report_input', date=report_date))

        # 代表値を使って reports テーブル用の項目を生成
        work_time = task_duration[0].strip() if task_duration and task_duration[0].strip() != "" else "0"
        work_detail = task_name[0].strip() if task_name and task_name[0].strip() != "" else "(未記入)"

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # reportsテーブルに既存データがあるか確認
        cursor.execute('SELECT report_id FROM reports WHERE user_id = ? AND report_date = ?', (user_id, report_date))
        existing_report = cursor.fetchone()

        if existing_report:
            report_id = existing_report['report_id']
            cursor.execute('''
                UPDATE reports
                SET condition = ?, start_time = ?, end_time = ?, work_time = ?, work_detail = ?, updated_at = ?
                WHERE report_id = ?
            ''', (condition, start_time, end_time, work_time, work_detail, created_at, report_id))
            # 関連タスクは一旦削除
            cursor.execute('DELETE FROM report_tasks WHERE report_id = ?', (report_id,))
        else:
            cursor.execute('''
                INSERT INTO reports (user_id, report_date, condition, start_time, end_time, work_time, work_detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, report_date, condition, start_time, end_time, work_time, work_detail, created_at))
            report_id = cursor.lastrowid

        # 各タスクを report_tasks に登録
        for index, (name, duration, note) in enumerate(zip(task_name, task_duration, task_note), start=1):
            if name.strip() == "":
                continue
            cursor.execute('''
                INSERT INTO report_tasks (report_id, task_name, task_duration, task_note, task_order)
                VALUES (?, ?, ?, ?, ?)
            ''', (report_id, name, duration, note, index))

        db.commit()
        flash('日報を保存しました。')
        return redirect(url_for('daily_report_input', date=report_date))

    else:
        # GETメソッド時：フォーム初期表示処理
        report_date = request.args.get('date')  # カレンダーから渡される日付
        if not report_date:
            flash('日付が指定されていません。')
            return redirect(url_for('main'))

        user_id = session.get('user_id')
        db = get_db()
        cursor = db.cursor()

        # 既存の日報情報の取得（あれば）
        cursor.execute('SELECT * FROM reports WHERE user_id = ? AND report_date = ?', (user_id, report_date))
        report = cursor.fetchone()

        tasks = []
        if report:
            cursor.execute('SELECT * FROM report_tasks WHERE report_id = ? ORDER BY task_order', (report['report_id'],))
            tasks = cursor.fetchall()

        task_count = len(tasks) if tasks else 1

        # 職員コメントの設定
        staff_comment = ''
        if report:
            staff_comment = report['staff_comment'] if report['staff_comment'] is not None else ''
        
        # ユーザー名をセッションから取得してテンプレートに渡す
        user_name = session.get('name', '利用者')  # セッションに名前があることを想定
        return render_template('daily_report_input.html',
            report_date=report_date,
            report=report,
            tasks=tasks,
            task_count=task_count,
            name=user_name,
            staff_comment=staff_comment
        )

# -----------------------
# G5. 日報一覧画面のルート
# -----------------------
@app.route('/report_list', methods=['GET', 'POST'])
def report_list():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = request.args.get('user_id')
    if user_id is not None:
        user_id = int(user_id)

    role = session.get('role')
    username = session['username']

    # 年月の指定（なければ現在）
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    today = datetime.today()

    if not year or not month:
        year = today.year
        month = today.month

    # 月の開始と終了を取得
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])
    first_day_str = first_day.strftime('%Y-%m-%d')
    last_day_str = last_day.strftime('%Y-%m-%d')

    prev_month = first_day - timedelta(days=1)
    next_month = last_day + timedelta(days=1)

    conn = get_db()
    cursor = conn.cursor()

    if role == 'staff' and user_id:
        # 利用者の「名前」を取得
        user_result = cursor.execute("SELECT name FROM users WHERE user_id = ?", (user_id,)).fetchone()
        display_name = user_result['name'] if user_result else '不明'

        # 日報と作業内容を取得
        cursor.execute('''
            SELECT r.*, u.username,
                   group_concat(t.task_duration, '\n') as task_duration,
                   group_concat(t.task_name, '\n') as task_name,
                   group_concat(t.task_note, '\n') as task_note
            FROM reports r
            JOIN users u ON r.user_id = u.user_id
            LEFT JOIN report_tasks t ON r.report_id = t.report_id
            WHERE r.user_id = ? AND r.report_date BETWEEN ? AND ?
            GROUP BY r.report_id
            ORDER BY r.report_date ASC
        ''', (user_id, first_day_str, last_day_str))
        reports = cursor.fetchall()

    else:
        # 利用者本人が閲覧する場合（例：role='user'）
        cursor.execute('''
            SELECT r.*, u.username, u.name,
                   group_concat(t.task_duration, '\n') as task_duration,
                   group_concat(t.task_name, '\n') as task_name,
                   group_concat(t.task_note, '\n') as task_note
            FROM reports r
            JOIN users u ON r.user_id = u.user_id
            LEFT JOIN report_tasks t ON r.report_id = t.report_id
            WHERE u.username = ? AND r.report_date BETWEEN ? AND ?
            GROUP BY r.report_id
            ORDER BY r.report_date ASC
        ''', (username, first_day_str, last_day_str))
        reports = cursor.fetchall()

        # ログイン中の利用者の「名前」を取得
        user_result = cursor.execute("SELECT name FROM users WHERE username = ?", (username,)).fetchone()
        display_name = user_result['name'] if user_result else '不明'

    conn.close()

    return render_template('report_list.html',
                           reports=reports,
                           name=display_name,  # ← 利用者の「名前」
                           user_id=user_id,
                           display_month=f"{year}年{month:02d}月",
                           year=year,
                           month=month,
                           prev_year=prev_month.year,
                           prev_month=prev_month.month,
                           next_year=next_month.year,
                           next_month=next_month.month)


# -----------------------
# 職員コメントアップデート処理
# -----------------------
@app.route('/update_staff_comments', methods=['POST'])
def update_staff_comments():
    if 'username' not in session:
        return redirect(url_for('login'))

    report_ids_str = request.form.get('report_ids')
    if not report_ids_str:
        flash('更新対象のレポートIDがありません。')
        # user_idやyear, monthを取得して渡す（なければNoneでOK）
        user_id = request.form.get('user_id')
        year = request.form.get('year')
        month = request.form.get('month')
        return redirect(url_for('report_list', user_id=user_id, year=year, month=month))

    report_ids = report_ids_str.split(',')

    conn = get_db()
    cursor = conn.cursor()

    try:
        for report_id in report_ids:
            staff_comment = request.form.get(f'staff_comment_{report_id}', '')
            cursor.execute('''
                UPDATE reports
                SET staff_comment = ?
                WHERE report_id = ?
            ''', (staff_comment, report_id))
        conn.commit()
        flash('職員コメントを更新しました。')
    except Exception as e:
        conn.rollback()
        flash(f'コメントの更新に失敗しました。エラー: {e}')
    finally:
        conn.close()

    # 更新後は元の利用者IDと年月を渡してリダイレクト
    user_id = request.form.get('user_id')
    year = request.form.get('year')
    month = request.form.get('month')
    return redirect(url_for('report_list', user_id=user_id, year=year, month=month))

# ---------------------------
# G6.ログアウト処理（ログアウト画面へ遷移）
# ---------------------------
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return render_template('logout.html')

# ---------------------------
# アプリ起動
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)