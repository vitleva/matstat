from flask import Flask, render_template, request
from scipy.stats import t, norm
import math

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    user_input = {}

    if request.method == 'POST':
        try:
            alpha = float(request.form['alpha'])
            mode = request.form.get('mode')  # known or unknown
            sigma = float(request.form.get('sigma', 0)) if mode == 'known' else None

            def parse_input(prefix):
                values = []
                counts = []
                i = 0
                while True:
                    val = request.form.get(f'{prefix}_value_{i}')
                    cnt = request.form.get(f'{prefix}_count_{i}')
                    if val is None or cnt is None:
                        break
                    if val.strip() == '':
                        i += 1
                        continue
                    values.append(float(val))
                    counts.append(int(cnt))
                    i += 1
                return values, counts

            values_A, counts_A = parse_input('a')
            values_B, counts_B = parse_input('b')

            data_A = [v for v, c in zip(values_A, counts_A) for _ in range(c)]
            data_B = [v for v, c in zip(values_B, counts_B) for _ in range(c)]

            if len(data_A) < 2 or len(data_B) < 2:
                raise ValueError("Обе выборки должны содержать как минимум 2 значения.")

            n1 = len(data_A)
            n2 = len(data_B)
            mean1 = sum(data_A) / n1
            mean2 = sum(data_B) / n2

            if mode == 'unknown':
                # дисперсия неизвестна
                s1_sq = sum((x - mean1) ** 2 for x in data_A) / (n1 - 1)
                s2_sq = sum((x - mean2) ** 2 for x in data_B) / (n2 - 1)
                s_pooled = ((n1 - 1) * s1_sq + (n2 - 1) * s2_sq) / (n1 + n2 - 2)
                t_calc = (mean1 - mean2) / math.sqrt(s_pooled * (1/n1 + 1/n2))
                df = n1 + n2 - 2
                t_crit = t.ppf(1 - alpha / 2, df)
                result = {
                    'mode': 'unknown',
                    'mean1': round(mean1, 4),
                    'mean2': round(mean2, 4),
                    's1_sq': round(s1_sq, 4),
                    's2_sq': round(s2_sq, 4),
                    's_pooled': round(s_pooled, 4),
                    't_calc': round(t_calc, 4),
                    't_crit': round(t_crit, 4),
                    'df': df,
                    'hypothesis': "отклоняется" if abs(t_calc) > t_crit else "не отклоняется"
                }
            else:
                # дисперсия известна, σ задана пользователем
                if sigma <= 0:
                    raise ValueError("σ должно быть положительным числом.")
                t_calc = (mean1 - mean2) / (sigma * math.sqrt(1/n1 + 1/n2))
                t_crit = norm.ppf(1 - alpha / 2)  # !!! нормальное распределение
                result = {
                    'mode': 'known',
                    'mean1': round(mean1, 4),
                    'mean2': round(mean2, 4),
                    'sigma': sigma,
                    't_calc': round(t_calc, 4),
                    't_crit': round(t_crit, 4),
                    'hypothesis': "отклоняется" if abs(t_calc) > t_crit else "не отклоняется"
                }

            user_input = {
                'values_A': values_A,
                'counts_A': counts_A,
                'values_B': values_B,
                'counts_B': counts_B,
                'alpha': alpha,
                'mode': mode,
                'sigma': sigma
            }

        except Exception as e:
            result = {'error': str(e)}

    return render_template('index.html', result=result, user_input=user_input, zip=zip)

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)