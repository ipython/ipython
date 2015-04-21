@ECHO OFF
REM ~ Windows command line make file for Sphinx documentation

SETLOCAL

SET SPHINXOPTS=
SET SPHINXBUILD=sphinx-build
SET PAPER=
SET SRCDIR=source

IF "%PAPER%" == "" SET PAPER=a4
SET ALLSPHINXOPTS=-d build\doctrees -D latex_paper_size=%PAPER% %SPHINXOPTS% %SRCDIR%

FOR %%X IN (%SPHINXBUILD%.exe) DO SET P=%%~$PATH:X

FOR %%L IN (html pickle htmlhelp latex changes linkcheck) DO (
    IF "%1" == "%%L" (
        IF "%P%" == "" (
            ECHO.
            ECHO Error: Sphinx is not available. Please make sure it is correctly installed.
            GOTO END
        )
        MD build\doctrees 2>NUL
        MD build\%1 || GOTO DIR_EXIST
        %SPHINXBUILD% -b %1 %ALLSPHINXOPTS% build\%1
        IF NOT ERRORLEVEL 0 GOTO ERROR
        ECHO.
        ECHO Build finished. Results are in build\%1.
        IF "%1" == "pickle" (
            ECHO Now you can process the pickle files or run
            ECHO    sphinx-web build\pickle to start the sphinx-web server.
        )
        IF "%1" == "htmlhelp" (
            ECHO Now you can run HTML Help Workshop with the
            ECHO    .hhp project file in build/htmlhelp.
        )
        IF "%1" == "linkcheck" (
            ECHO Look for any errors in the above output
            ECHO    or in build\linkcheck\output.rst.
        )
        GOTO END
    )
)


IF "%1" == "clean" (
    RD /s /q build dist %SRCDIR%\api\generated 2>NUL
    IF ERRORLEVEL 0 ECHO Build environment cleaned!
    GOTO END
)

ECHO.
ECHO Please use "make [target]" where [target] is one of:
ECHO.
ECHO    html      to make standalone HTML files
ECHO    jsapi     to make standalone HTML files for the Javascript API
ECHO    pickle    to make pickle files (usable by e.g. sphinx-web)
ECHO    htmlhelp  to make HTML files and a HTML help project
ECHO    latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter
ECHO    changes   to make an overview over all changed/added/deprecated items
ECHO    linkcheck to check all external links for integrity
GOTO END

:DIR_EXIST
ECHO.
ECHO Info: Run "make clean" to clean build environment

:ERROR
ECHO.
ECHO Error: Build process failed!

:END
ENDLOCAL