import io
import zipfile


def create_zip(images):

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as z:

        for index, image in enumerate(images, start=1):

            image_buffer = io.BytesIO()

            image.save(
                image_buffer,
                format="PNG"
            )

            z.writestr(
                f"translated_page_{index:03d}.png",
                image_buffer.getvalue()
            )

    buffer.seek(0)

    return buffer
