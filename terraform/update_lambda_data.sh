#!/bin/bash
cd lambda_functions/checkReports && pip install --target ./package -r requirements.txt
cd package && zip -r ../packages.zip . && cd ..
zip check-report.zip lambda_function.py
