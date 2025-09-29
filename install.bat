@echo off
echo Installing requirements...
pip install -r requirements.txt
echo.
echo Installation complete!
echo.
echo To run the processor:
echo python BatchPdfConv_Enhanced.py
echo.
echo To check status:
echo python BatchPdfConv_Enhanced.py --status
echo.
echo To process a single file:
echo python BatchPdfConv_Enhanced.py --single-file "filename.pdf"
pause
