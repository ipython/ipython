"""
This module regroup a number of useful mmimetype handler for terminal IPython. 

This can be used depending on your system configuration to do things like
displaying inline images, or opening HTML representation in your web browse

"""

from typing import Dict
from base64 import encodebytes


def browser(data, metadata) -> None:
    """
    Handler for html representation and opening them in a web browser. 

    Currently this will simply put the html in body tag without any css and
    might not look identical to Jupyter Notebook/ JupyterLab. 

    This _does_ create a temporary file which is not removed, so may contain
    sensitive data.

    Not tested on all platform and browser, so may not work in all  case
    """
    import webbrowser
    from tempfile import NamedTemporaryFile

    f = NamedTemporaryFile(suffix=".html", delete=False)
    f.write(
        (
            """
        <html>
        <body>
        {data}
        </body>
        </html>
    """.format(
                data=data
            )
        ).encode()
    )
    f.close()
    webbrowser.open("file://" + f.name)


ITERM2_IMAGE_CODE = "\033]1337;File=name={name};size={size};inline=true;:{data}\a"


def inline_image_iterm2_mac(data, metadata, ext='png') -> None:
    """
    Inline image handler for iterm2 on mac. 

    Need to be registered with image/png, image/jpg, in order to be displayed
    inline

    """
    if isinstance(data, bytes):
        b64data = encodebytes(data).decode()
    elif isinstance(data, str):
        b64data = data
    else:
        raise TypeError(
            f" inline_image_iterm2_mac got unexpected type {type(data)} was expeting str, or bytes."
        )

    print(
        ITERM2_IMAGE_CODE.format(
            name=encodebytes(f"inline_ipython_image.{ext}".encode()).decode(),
            data=b64data,
            size=len(data),  # length is incorrect for already base64 data
        )
    )
