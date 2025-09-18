@echo off
chcp 65001 >nul
echo.
echo ===============================================
echo   🌐 نظام البحث في القوانين البحرينية
echo   تطبيق ويب باستخدام FastAPI
echo ===============================================
echo.
echo جاري تشغيل الخادم...
echo.
echo 🔗 الروابط المهمة:
echo    الموقع الرئيسي: http://localhost:8000
echo    واجهة برمجة التطبيقات: http://localhost:8000/api/docs
echo    الإحصائيات: http://localhost:8000/api/stats
echo.
echo 💡 للإيقاف: اضغط Ctrl+C
echo.
echo ===============================================
echo.
python web_app.py
echo.
echo تم إيقاف الخادم.
pause
