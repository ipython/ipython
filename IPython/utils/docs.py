# encoding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import os

GENERATING_DOCUMENTATION = os.environ.get("IN_SPHINX_RUN", None) == "True"
