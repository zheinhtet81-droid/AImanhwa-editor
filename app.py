import os
import io
import tempfile
import zipfile
from functools import wraps

from flask import (
    Flask,
    request,
    render_template_string,
    send_file,
    session,
    redirect,
    url_for,
    jsonify
)

import fitz
from PIL import Image

from modules.ocr import detect_text
from modules.renderer import replace_text


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


# =========================================================
# LOGIN PAGE
# =========================================================

LOGIN_HTML = r"""
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Manhwa Translator Login</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    background: #111827;
    color: white;
    font-family: Arial, sans-serif;

    display: flex;
    justify-content: center;
    align-items: center;

    padding: 20px;
}

.card {
    width: 100%;
    max-width: 420px;

    background: #1f2937;

    border-radius: 18px;

    padding: 25px;

    box-shadow:
        0 15px 40px rgba(0,0,0,.35);
}

h1 {
    margin-top: 0;
    text-align: center;
}

input {
    width: 100%;

    padding: 14px;

    margin-top: 12px;

    border-radius: 10px;

    border: 1px solid #374151;

    background: #111827;

    color: white;

    font-size: 16px;
}

button {
    width: 100%;

    margin-top: 18px;

    padding: 14px;

    border: 0;

    border-radius: 10px;

    background: #2563eb;

    color: white;

    font-size: 16px;

    font-weight: bold;
}

.error {
    margin-top: 15px;

    padding: 12px;

    border-radius: 10px;

    background: #7f1d1d;

    color: #fecaca;
}

</style>

</head>

<body>

<div class="card">

<h1>🔐 Manhwa Translator</h1>

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


# =========================================================
# MAIN PAGE
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Manhwa Translator</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    min-height: 100vh;

    background: #0f172a;

    color: white;

    font-family:
        Arial,
        "Noto Sans Myanmar",
        sans-serif;

    padding: 20px;
}

.container {

    width: 100%;

    max-width: 650px;

    margin: auto;
}

.card {

    background: #1e293b;

    border-radius: 18px;

    padding: 22px;

    box-shadow:
        0 15px 40px rgba(0,0,0,.3);
}

h1 {

    text-align: center;

    margin-top: 0;

    margin-bottom: 8px;
}

.subtitle {

    text-align: center;

    color: #94a3b8;

    margin-bottom: 25px;
}

label {

    display: block;

    margin-top: 18px;

    margin-bottom: 8px;

    font-weight: bold;
}

input[type="file"] {

    width: 100%;

    padding: 12px;

    border-radius: 10px;

    background: #0f172a;

    color: white;

    border: 1px solid #334155;
}

textarea {

    width: 100%;

    min-height: 160px;

    padding: 12px;

    border-radius: 10px;

    background: #0f172a;

    color: white;

    border: 1px solid #334155;

    resize: vertical;

    font-size: 15px;
}

button {

    width: 100%;

    padding: 15px;

    margin-top: 20px;

    border: 0;

    border-radius: 12px;

    background: #2563eb;

    color: white;

    font-size: 17px;

    font-weight: bold;
}

button:disabled {

    opacity: .55;
}

.logout {

    display: block;

    text-align: right;

    color: #fca5a5;

    text-decoration: none;

    margin-bottom: 15px;
}

#status {

    white-space: pre-wrap;

    margin-top: 20px;

    padding: 14px;

    border-radius: 10px;

    background: #0f172a;

    color: #cbd5e1;

    display: none;
}

.download {

    display: block;

    margin-top: 15px;

    padding: 14px;

    text-align: center;

    border-radius: 10px;

    background: #16a34a;

    color: white;

    text-decoration: none;

    font-weight: bold;
}

.hidden {

    display: none !important;
}

.info {

    margin-top: 15px;

    padding: 12px;

    border-radius: 10px;

    background: #172554;

    color: #bfdbfe;

    font-size: 14px;

    line-height: 1.5;
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


<div class="card">

<h1>📖 Manhwa Translator</h1>

<div class="subtitle">
    Myanmar Translation Tool
</div>


<form
    id="form"
    enctype="multipart/form-data"
>


<label>
    📚 Manhwa PDF / Image
</label>

<input
    type="file"
    name="file"
    accept=".pdf,.png,.jpg,.jpeg,.webp"
    required
>


<label>
    📝 Translation File
</label>

<input
    type="file"
    name="translation_file"
    accept=".txt,.docx"
>


<div class="info">

DOCX / TXT သုံးနိုင်ပါတယ်။<br>

DOCX ထဲမှာ translation စာကြောင်းတွေကို
တစ်ကြောင်းစီထားပါ။<br>

Translation file မတင်ချင်ရင်
အောက်က box ထဲ တိုက်ရိုက်ရေးနိုင်ပါတယ်။

</div>


<label>
    ✍️ Translation Text
</label>

<textarea
    name="translation"
    placeholder="မြန်မာဘာသာပြန်စာကို တစ်ကြောင်းစီရေးပါ..."
></textarea>


<button
    id="button"
    type="submit"
>
    🚀 Start Processing
</button>

</form>


<div id="status"></div>


<a
    id="download"
    class="download hidden"
>
    📥 Download Translated ZIP
</a>


</div>

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

        button.textContent =
            "⏳ Processing...";

        status.style.display =
            "block";

        status.textContent =
            "⏳ File processing လုပ်နေပါတယ်...";

        download.classList.add(
            "hidden"
        );


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


            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";


            if (
                !contentType.includes(
                    "application/json"
                )
            ) {

                const raw =
                    await response.text();

                throw new Error(
                    "Server HTTP " +
                    response.status +
                    "\n\n" +
                    raw.substring(
                        0,
                        3000
                    )
                );
            }


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.error ||
                    "Server Error"
                );
            }


            if (!result.success) {

                throw new Error(
                    result.error ||
                    "Processing failed"
                );
            }


            status.textContent =
                result.message ||
                "✅ Processing ပြီးပါပြီ";


            if (
                result.download_url
            ) {

                download.href =
                    result.download_url;

                download.classList.remove(
                    "hidden"
                );
            }

        }


        catch (error) {

            status.textContent =
                "❌ ERROR\n\n" +
                error.message;

        }


        finally {

            button.disabled = false;

            button.textContent =
                "🚀 Start Processing";

        }

    }
);

</script>

</body>

</html>
"""


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        if not session.get(
            "logged_in"
        ):

            if request.path == "/process":

                return jsonify({
                    "success": False,
                    "error":
                        "Login session expired. Please login again."
                }), 401

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return decorated


# =========================================================
# LOGIN
# =========================================================

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
            ).strip()

        password =
            request.form.get(
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


        error =
            "Username သို့မဟုတ် Password မှားနေပါတယ်"


    return render_template_string(
        LOGIN_HTML,
        error=error
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
@login_required
def home():

    return render_template_string(
        HTML
    )


# =========================================================
# PDF TO IMAGES
# =========================================================

def pdf_to_images(path):

    pages = []

    document = fitz.open(path)

    try:

        for page in document:

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(
                    1.5,
                    1.5
                ),
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

            pages.append(
                image
            )

    finally:

        document.close()

    return pages


# =========================================================
# IMAGE LOADER
# =========================================================

def load_input_images(path):

    lower = path.lower()


    if lower.endswith(".pdf"):

        return pdf_to_images(
            path
        )


    return [
        Image.open(path).convert(
            "RGB"
        )
    ]


# =========================================================
# TRANSLATION FILE READER
# =========================================================

def read_translation_file(path):

    if not path:

        return ""


    lower =
        path.lower()


    # TXT
    if lower.endswith(".txt"):

        with open(
            path,
            "r",
            encoding="utf-8-sig",
            errors="replace"
        ) as file:

            return file.read()


    # DOCX
    if lower.endswith(".docx"):

        try:

            from docx import Document

        except ImportError:

            raise RuntimeError(
                "python-docx မရှိပါ။ "
                "requirements.txt ထဲမှာ "
                "python-docx ထည့်ပြီး redeploy လုပ်ပါ။"
            )


        document =
            Document(path)


        lines = []


        for paragraph in document.paragraphs:

            text =
                paragraph.text.strip()

            if text:

                lines.append(
                    text
                )


        return "\n".join(
            lines
        )


    raise ValueError(
        "Translation file က TXT သို့မဟုတ် DOCX ဖြစ်ရပါမယ်။"
    )


# =========================================================
# TRANSLATION PARSER
# =========================================================

def parse_translations(text):

    if not text:

        return []


    return [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]


# =========================================================
# MATCH TRANSLATION
# =========================================================

def match_translations(
    boxes,
    translations
):

    result = []


    for index, box in enumerate(
        boxes
    ):

        item = dict(box)


        if index < len(
            translations
        ):

            item["myanmar"] =
                translations[index]

        else:

            item["myanmar"] = ""


        result.append(
            item
        )


    return result


# =========================================================
# ZIP CREATOR
# =========================================================

def create_zip(images):

    buffer =
        io.BytesIO()


    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as archive:


        for index, image in enumerate(
            images,
            start=1
        ):

            image_buffer =
                io.BytesIO()


            image.save(
                image_buffer,
                format="PNG"
            )


            archive.writestr(
                f"page_{index:04d}.png",
                image_buffer.getvalue()
            )


    buffer.seek(0)

    return buffer


# =========================================================
# PROCESS
# =========================================================

@app.route(
    "/process",
    methods=["POST"]
)
@login_required
def process():

    temp_dir = None


    try:

        uploaded =
            request.files.get(
                "file"
            )


        translation_upload =
            request.files.get(
                "translation_file"
            )


        translation_text =
            request.form.get(
                "translation",
                ""
            )


        if uploaded is None:

            return jsonify({
                "success": False,
                "error":
                    "Manhwa file မတွေ့ပါ"
            }), 400


        if not uploaded.filename:

            return jsonify({
                "success": False,
                "error":
                    "Manhwa file name မရှိပါ"
            }), 400


        filename =
            uploaded.filename.lower()


        allowed = (
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        )


        if not filename.endswith(
            allowed
        ):

            return jsonify({
                "success": False,
                "error":
                    "PDF/JPG/PNG/WEBP ပဲ တင်ပါ"
            }), 400


        temp_dir =
            tempfile.mkdtemp(
                prefix="manhwa_"
            )


        input_path =
            os.path.join(
                temp_dir,
                os.path.basename(
                    uploaded.filename
                )
            )


        uploaded.save(
            input_path
        )


        # -------------------------------------------------
        # Read translation file
        # -------------------------------------------------

        if (
            translation_upload
            and translation_upload.filename
        ):

            translation_filename =
                translation_upload.filename.lower()


            if not translation_filename.endswith(
                (".txt", ".docx")
            ):

                return jsonify({
                    "success": False,
                    "error":
                        "Translation file က TXT သို့မဟုတ် DOCX ပဲ ဖြစ်ရပါမယ်။"
                }), 400


            translation_path =
                os.path.join(
                    temp_dir,
                    os.path.basename(
                        translation_upload.filename
                    )
                )


            translation_upload.save(
                translation_path
            )


            translation_text =
                read_translation_file(
                    translation_path
                )


        translations =
            parse_translations(
                translation_text
            )


        if not translations:

            return jsonify({
                "success": False,
                "error":
                    "Translation စာ မတွေ့ပါ။ TXT/DOCX တင်ပါ သို့မဟုတ် စာကို box ထဲရေးပါ။"
            }), 400


        # -------------------------------------------------
        # Load pages
        # -------------------------------------------------

        pages =
            load_input_images(
                input_path
            )


        if not pages:

            raise ValueError(
                "Page မတွေ့ပါ"
            )


        output_pages = []

        total_boxes = 0


        # -------------------------------------------------
        # Process each page
        # -------------------------------------------------

        for page_index, page in enumerate(
            pages,
            start=1
        ):


            boxes =
                detect_text(
                    page
                )


            total_boxes += len(
                boxes
            )


            matched =
                match_translations(
                    boxes,
                    translations
                )

            # ========== ဒီနေရာကို ပြင်ထားတယ် ==========
            output =
                replace_text(
                    page,
                    matched   # ← translations ကို ဖယ်လိုက်တယ်
                )
            # ===========================================

            output_pages.append(
                output
            )


        # -------------------------------------------------
        # Create ZIP
        # -------------------------------------------------

        zip_buffer =
            create_zip(
                output_pages
            )


        output_path =
            os.path.join(
                temp_dir,
                "translated_manhwa.zip"
            )


        with open(
            output_path,
            "wb"
        ) as output_file:

            output_file.write(
                zip_buffer.getvalue()
            )


        # -------------------------------------------------
        # Save download path
        # -------------------------------------------------

        app.config.setdefault(
            "OUTPUTS",
            {}
        )


        token =
            os.path.basename(
                temp_dir
            )


        app.config["OUTPUTS"][token] =
            output_path


        return jsonify({

            "success": True,

            "message":
                (
                    "✅ Processing ပြီးပါပြီ!\n\n"
                    f"Pages: {len(output_pages)}\n"
                    f"Text boxes: {total_boxes}\n"
                    f"Translation lines: {len(translations)}\n\n"
                    "ZIP download လုပ်နိုင်ပါပြီ။"
                ),

            "download_url":
                f"/download/{token}"

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "error":
                f"{type(error).__name__}: {str(error)}"

        }), 500


# =========================================================
# DOWNLOAD
# =========================================================

@app.route(
    "/download/<token>"
)
@login_required
def download(token):

    outputs =
        app.config.get(
            "OUTPUTS",
            {}
        )


    path =
        outputs.get(
            token
        )


    if not path:

        return (
            "Download file မတွေ့ပါ",
            404
        )


    if not os.path.exists(
        path
    ):

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


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok"
    })


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    port =
        int(
            os.environ.get(
                "PORT",
                "8080"
            )
        )


    app.run(

        host="0.0.0.0",

        port=port
    )