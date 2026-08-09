import os
import tempfile
from functools import wraps

from flask import (
    Flask,
    request,
    render_template_string,
    send_file,
    session,
    redirect,
    url_for
)

import fitz
from PIL import Image

from modules.ocr import detect_text
from modules.translator import (
    load_translation,
    load_translation_file,
    match_translation
)
from modules.renderer import replace_text
from modules.exporter import create_zip


app = Flask(__name__)

app.secret_key = os.environ.get(
    "APP_SECRET",
    "change-this-secret"
)

USERNAME = os.environ.get(
    "APP_USERNAME",
    "admin"
)

PASSWORD = os.environ.get(
    "APP_PASSWORD",
    "change-this-password"
)


LOGIN_HTML = r"""
<!DOCTYPE html>
<html lang="my">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Private Login</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;

    min-height: 100vh;

    display: flex;
    align-items: center;
    justify-content: center;

    background: #0f172a;
    color: white;

    font-family: Arial, sans-serif;
}

.box {
    width: 100%;
    max-width: 420px;

    padding: 25px;

    background: #1e293b;

    border-radius: 16px;

    border: 1px solid #334155;
}

h1 {
    text-align: center;
    color: #38bdf8;
}

input {
    width: 100%;

    padding: 13px;

    margin-top: 10px;

    border-radius: 8px;

    border: 1px solid #475569;

    background: #0f172a;

    color: white;

    font-size: 16px;
}

button {
    width: 100%;

    padding: 13px;

    margin-top: 18px;

    border: 0;

    border-radius: 8px;

    background: #0284c7;

    color: white;

    font-size: 16px;

    font-weight: bold;
}

.error {
    margin-top: 15px;

    padding: 10px;

    background: #7f1d1d;

    border-radius: 8px;

    text-align: center;
}

</style>

</head>

<body>

<div class="box">

<h1>🔐 Private App</h1>

<form method="POST">

<input
    type="text"
    name="username"
    placeholder="Username"
    autocomplete="username"
    required
>

<input
    type="password"
    name="password"
    placeholder="Password"
    autocomplete="current-password"
    required
>

<button type="submit">
    Login
</button>

</form>

{% if error %}

<div class="error">
    {{ error }}
</div>

{% endif %}

</div>

</body>

</html>
"""


HTML = r"""
<!DOCTYPE html>
<html lang="my">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>AI Manhwa Myanmar Translator</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;

    background: #0f172a;

    color: #f8fafc;

    font-family: Arial, sans-serif;
}

.container {
    max-width: 850px;

    margin: auto;

    background: #1e293b;

    padding: 25px;

    border-radius: 16px;

    border: 1px solid #334155;
}

h1 {
    text-align: center;

    color: #38bdf8;
}

.logout {
    display: block;

    text-align: right;

    color: #f87171;

    text-decoration: none;

    margin-bottom: 15px;
}

label {
    display: block;

    margin-top: 18px;

    margin-bottom: 8px;

    font-weight: bold;
}

input,
textarea {
    width: 100%;

    padding: 12px;

    border-radius: 8px;

    border: 1px solid #475569;

    background: #0f172a;

    color: white;
}

textarea {
    min-height: 160px;

    resize: vertical;
}

button {
    width: 100%;

    padding: 14px;

    margin-top: 20px;

    border: 0;

    border-radius: 8px;

    background: #0284c7;

    color: white;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;
}

button:disabled {
    opacity: 0.5;

    cursor: not-allowed;
}

.help {
    margin-top: 8px;

    color: #94a3b8;

    font-size: 14px;
}

#status {
    margin-top: 20px;

    padding: 15px;

    background: #020617;

    border-radius: 8px;

    white-space: pre-wrap;

    min-height: 80px;
}

.download {
    display: block;

    margin-top: 20px;

    padding: 14px;

    text-align: center;

    background: #16a34a;

    color: white;

    text-decoration: none;

    border-radius: 8px;

    font-weight: bold;
}

.hidden {
    display: none;
}

</style>

</head>

<body>

<div class="container">

<a
    class="logout"
    href="/logout"
>
    Logout
</a>

<h1>
🎨 AI Manhwa Myanmar Translator
</h1>


<form
    id="form"
    enctype="multipart/form-data"
>


<label>
📕 Manhwa PDF / Image
</label>

<input
    type="file"
    name="file"
    accept=".pdf,.png,.jpg,.jpeg,.webp"
    required
>


<label>
📄 Translation File
</label>

<input
    type="file"
    name="translation_file"
    accept=".txt,.docx,.srt,.vtt,.csv"
>

<div class="help">
TXT / DOCX / SRT / VTT / CSV support.
</div>


<label>
🇲🇲 Or paste translation text
</label>

<textarea
    name="translation"
    placeholder="Translation file မသုံးရင် ဒီနေရာမှာ စာကြောင်းတစ်ကြောင်းစီ ထည့်နိုင်ပါတယ်..."
></textarea>


<button
    id="button"
    type="submit"
>
🚀 Start Processing
</button>

</form>


<div id="status">
Ready...
</div>


<a
    id="download"
    class="download hidden"
>
📥 Download Translated ZIP
</a>


</div>


<script>

const form =
    document.getElementById("form");

const button =
    document.getElementById("button");

const status =
    document.getElementById("status");

const download =
    document.getElementById("download");


form.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        button.disabled = true;

        download.classList.add(
            "hidden"
        );

        status.textContent =
            "⏳ Processing...";

        try {

            const formData =
                new FormData(form);

            const response =
                await fetch(
                    "/process",
                    {
                        method: "POST",
                        body: formData
                    }
                );

            const result =
                await response.json();

            if (!response.ok) {

    const raw =
        await response.text();

    throw new Error(
        "HTTP " +
        response.status +
        "\n\n" +
        raw.substring(0, 3000)
    );
}

            if (!result.success) {

                throw new Error(
                    result.error ||
                    "Processing failed"
                );
            }

            status.textContent =
                result.message;

            download.href =
                result.download_url;

            download.classList.remove(
                "hidden"
            );

        }

        catch (error) {

            status.textContent =
                "❌ Error:\n" +
                error.message;

        }

        finally {

            button.disabled = false;

        }

    }
);

</script>

</body>

</html>
"""


def login_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        if not session.get(
            "logged_in"
        ):

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return decorated


@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == USERNAME
            and password == PASSWORD
        ):

            session["logged_in"] = True

            return redirect(
                url_for("home")
            )

        error = (
            "Username သို့မဟုတ် "
            "Password မှားနေပါတယ်"
        )

    return render_template_string(
        LOGIN_HTML,
        error=error
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


@app.route("/")
@login_required
def home():

    return render_template_string(
        HTML
    )


def pdf_to_images(path):

    document = fitz.open(path)

    try:

        for page in document:

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(1.5, 1.5),
                alpha=False
            )

            image = Image.frombytes(
                "RGB",
                (
                    pixmap.width,
                    pixmap.height
                ),
                pixmap.samples
            )

            yield image

    finally:

        document.close()

def load_input_images(path):

    lower = path.lower()

    if lower.endswith(".pdf"):

        return pdf_to_images(path)

    return [
        Image.open(path).convert("RGB")
    ]


@app.route(
    "/process",
    methods=["POST"]
)
@login_required
def process():

    uploaded = request.files.get(
        "file"
    )

    translation_upload = request.files.get(
        "translation_file"
    )

    translation_text = request.form.get(
        "translation",
        ""
    )


    if uploaded is None:

        return {
            "success": False,
            "error": "Manhwa file မတွေ့ပါ"
        }, 400


    if not uploaded.filename:

        return {
            "success": False,
            "error": "Manhwa file name မရှိပါ"
        }, 400


    filename = uploaded.filename.lower()

    allowed_images = (
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    )


    if not filename.endswith(
        allowed_images
    ):

        return {
            "success": False,
            "error": (
                "PDF/JPG/PNG/WEBP ပဲ "
                "တင်ပါ"
            )
        }, 400


    temp_dir = tempfile.mkdtemp(
        prefix="manhwa_"
    )


    input_path = os.path.join(
        temp_dir,
        os.path.basename(
            uploaded.filename
        )
    )


    try:

        uploaded.save(
            input_path
        )


        pages = load_input_images(
            input_path
        )


        if not pages:

            raise ValueError(
                "Page မတွေ့ပါ"
            )


        translations = []


        # Translation file has priority.
        if (
            translation_upload is not None
            and translation_upload.filename
        ):

            translation_filename = (
                translation_upload.filename
            )

            translation_path = os.path.join(
                temp_dir,
                os.path.basename(
                    translation_filename
                )
            )


            translation_upload.save(
                translation_path
            )


            translations = (
                load_translation_file(
                    translation_path
                )
            )


        # If no translation file,
        # use pasted text.
        if not translations:

            translations = (
                load_translation(
                    translation_text
                )
            )


        if not translations:

            raise ValueError(
                "Translation file သို့မဟုတ် "
                "translation text ထည့်ပါ"
            )


        output_pages = []

        total_boxes = 0


        for page in pages:

            boxes = detect_text(
                page
            )

            total_boxes += len(
                boxes
            )


            matched = match_translation(
                boxes,
                translations
            )


            output = replace_text(
                page,
                matched,
                translations
            )


            output_pages.append(
                output
            )


        zip_buffer = create_zip(
            output_pages
        )


        output_path = os.path.join(
            temp_dir,
            "translated_manhwa.zip"
        )


        with open(
            output_path,
            "wb"
        ) as output_file:

            output_file.write(
                zip_buffer.read()
            )


        app.config.setdefault(
            "OUTPUTS",
            {}
        )


        token = os.path.basename(
            temp_dir
        )


        app.config["OUTPUTS"][token] = (
            output_path
        )


        return {

            "success": True,

            "message": (
                "✅ Processing ပြီးပါပြီ!\n\n"
                f"Pages: {len(output_pages)}\n"
                f"Text boxes: {total_boxes}\n"
                f"Translation lines: "
                f"{len(translations)}\n\n"
                "ZIP download လုပ်နိုင်ပါပြီ။"
            ),

            "download_url":
                f"/download/{token}"
        }


    except Exception as error:

        return {

            "success": False,

            "error": str(error)

        }, 500


@app.route(
    "/download/<token>"
)
@login_required
def download(token):

    outputs = app.config.get(
        "OUTPUTS",
        {}
    )


    path = outputs.get(
        token
    )


    if not path:

        return (
            "Download file မတွေ့ပါ",
            404
        )


    if not os.path.exists(path):

        return (
            "Download file မရှိတော့ပါ",
            404
        )


    return send_file(

        path,

        as_attachment=True,

        download_name=
            "translated_manhwa.zip",

        mimetype=
            "application/zip"
    )


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )


    app.run(
        host="0.0.0.0",
        port=port
    )