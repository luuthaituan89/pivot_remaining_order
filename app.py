from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SESSION_PERMANENT'] = False

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def generate_pivot_table(df):
    count_table = df.groupby(['number_of_days', 'domain']).size().reset_index(name='count')
    pivot_table = count_table.pivot_table(index='number_of_days', columns='domain', values='count', fill_value=0)
    pivot_table.loc['Grand Total'] = pivot_table.sum()
    pivot_table = pivot_table.reindex(sorted(pivot_table.columns, key=lambda x: (str(x), x)), axis=1)
    pivot_table['Grand Total'] = pivot_table.sum(axis=1)
    return pivot_table


def write_excel(df, pivot_table, output_path):
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='RawData', index=False)
        pivot_table.to_excel(writer, sheet_name='DashBoard')


def _get_file_list():
    files = []
    for fname in os.listdir(UPLOAD_FOLDER):
        if fname.endswith('.csv'):
            input_name = fname
            output_name = os.path.splitext(fname)[0] + '.xlsx'
            has_output = os.path.exists(os.path.join(OUTPUT_FOLDER, output_name))
            files.append({
                'input': input_name,
                'output': output_name if has_output else None
            })
    return sorted(files, key=lambda x: x['input'])


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            input_path = os.path.join(UPLOAD_FOLDER, filename)
            output_name = os.path.splitext(filename)[0] + '.xlsx'
            output_path = os.path.join(OUTPUT_FOLDER, output_name)

            file.save(input_path)

            try:
                df = pd.read_csv(input_path)

                if 'number_of_days' in df.columns:
                    filtered_rows = df[df['number_of_days'].isin([0, 1])].fillna('')
                    session['filtered_rows'] = filtered_rows.to_dict(orient='records')
                    session['column_order'] = list(filtered_rows.columns)
                else:
                    flash("⚠️ Missing column 'number_of_days' in CSV file")
                    session['filtered_rows'] = []
                    session['column_order'] = []

                pivot_table = generate_pivot_table(df)
                write_excel(df, pivot_table, output_path)

                flash("✅ File has been processed successfully.")
                session['latest_output'] = output_name
            except Exception as e:
                flash(f"❌ Error: {str(e)}")
                session['filtered_rows'] = []
                session['column_order'] = []

            return redirect(url_for('index'))

    filtered_rows = session.get('filtered_rows', [])
    column_order = session.get('column_order', [])
    latest_output = session.get('latest_output')

    if latest_output and not os.path.exists(os.path.join(OUTPUT_FOLDER, latest_output)):
        filtered_rows = []
        column_order = []
        session.pop('filtered_rows', None)
        session.pop('column_order', None)
        session.pop('latest_output', None)

    files = _get_file_list()
    return render_template("index.html", files=files, filtered_rows=filtered_rows, column_order=column_order)


@app.route("/download/<filename>")
def download_file(filename):
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(output_path):
        return send_file(
            output_path,
            as_attachment=True,
            download_name='Order_Remaining_Payment_Review_Checklist.xlsx'
        )
    return "File not found", 404


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
