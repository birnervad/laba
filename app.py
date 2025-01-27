from flask import Flask, request, render_template, send_file, session
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')  # Добавьте эту строку
import matplotlib.pyplot as plt  # Добавьте эту строку
import random
import string
from io import BytesIO
import numpy as np
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-12345'  # Измените на свой секретный ключ

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)


# Генерация капчи
def generate_captcha():
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    session['captcha'] = captcha_text

    img = Image.new('RGB', (200, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('arial.ttf', 36)
    except:
        font = ImageFont.load_default()

    # Рисуем искаженный текст
    for i, char in enumerate(captcha_text):
        draw.text((10 + i * 30 + random.randint(-5, 5),
                   20 + random.randint(-5, 5)),
                  char, font=font,
                  fill=(random.randint(0, 150),
                        random.randint(0, 150),
                        random.randint(0, 150)))

    # Добавляем шум
    for _ in range(200):
        x = random.randint(0, 200)
        y = random.randint(0, 80)
        draw.point((x, y), fill=(random.randint(0, 255),
                                 random.randint(0, 255),
                                 random.randint(0, 255)))

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io


# Основная логика обработки изображений
def generate_chessboard(image, cell_size_percent, color):
    width, height = image.size
    cell_width = int(width * cell_size_percent / 100)
    cell_height = int(height * cell_size_percent / 100)
    color_rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))

    draw = ImageDraw.Draw(image)
    for y in range(0, height, cell_height):
        for x in range(0, width, cell_width):
            if (x // cell_width + y // cell_height) % 2 == 0:
                draw.rectangle([(x, y), (x + cell_width, y + cell_height)], fill=color_rgb)
    return image


def plot_color_distribution(image, filename, title_suffix=""):
    array = np.array(image)
    colors = ["Red", "Green", "Blue"]
    channel_stats = []

    plt.figure(figsize=(12, 6), dpi=150)  # Увеличиваем DPI для лучшего качества
    for i, color in enumerate(colors):
        channel_data = array[..., i].flatten()
        mean_val = np.mean(channel_data)
        std_val = np.std(channel_data)
        channel_stats.append((mean_val, std_val))

        plt.hist(channel_data, bins=256, range=(0, 255),
                 alpha=0.7, color=color.lower(),  # Увеличиваем прозрачность
                 label=f'{color} (μ={mean_val:.1f}, σ={std_val:.1f})')

    plt.title(f'Color Distribution {title_suffix}'.strip(), fontsize=16)  # Увеличиваем размер шрифта
    plt.xlabel("Color Value (0-255)", fontsize=14)  # Увеличиваем размер шрифта
    plt.ylabel("Pixel Count", fontsize=14)  # Увеличиваем размер шрифта
    plt.grid(True, linestyle='--', alpha=0.6)  # Увеличиваем прозрачность сетки
    plt.xlim(0, 255)
    plt.legend(facecolor='white', edgecolor='black', framealpha=1, fontsize=12)  # Улучшаем легенду
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', dpi=150)  # Увеличиваем DPI для лучшего качества
    plt.close()


# Маршруты
@app.route('/captcha')
def captcha():
    img_io = generate_captcha()
    return send_file(img_io, mimetype='image/png')


@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        # Проверка капчи
        user_captcha = request.form.get('captcha', '').upper().replace(' ', '')
        if 'captcha' not in session or user_captcha != session['captcha']:
            error = "Неверный код проверки"
        else:
            # Обработка изображения
            file = request.files.get('image')
            cell_size = float(request.form.get('cell_size', 0))
            color = request.form.get('color', '#ffffff')

            if file and cell_size > 0:
                # Сохранение и обработка файла
                filename = file.filename
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

                image = Image.open(filepath).convert('RGB')
                processed_image = generate_chessboard(image.copy(), cell_size, color)
                processed_path = os.path.join(RESULT_FOLDER, f"processed_{filename}")
                processed_image.save(processed_path)

                # Генерация графиков
                original_plot = os.path.join(RESULT_FOLDER, "original_colors.png")
                processed_plot = os.path.join(RESULT_FOLDER, "processed_colors.png")
                plot_color_distribution(image, original_plot, "(Original)")
                plot_color_distribution(processed_image, processed_plot, "(Processed)")

                return render_template('result.html',
                                       original_image=filename,
                                       processed_image=f"processed_{filename}",
                                       original_plot="original_colors.png",
                                       processed_plot="processed_colors.png")

        # Очистка капчи после проверки
        session.pop('captcha', None)

    return render_template('index.html',
                           error=error,
                           captcha_url=f'/captcha?{random.random()}')


@app.route('/uploads/<filename>')
def upload_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))


@app.route('/results/<filename>')
def result_file(filename):
    return send_file(os.path.join(RESULT_FOLDER, filename))


if __name__ == '__main__':
    app.run(debug=True)