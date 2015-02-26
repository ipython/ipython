* add ``NotebookApp.ssl_options`` config value.
  This is passed through to tornado HTTPServer,
  and allows SSL configuration beyong specifying a cert and key,
  such as disabling SSLv3.
