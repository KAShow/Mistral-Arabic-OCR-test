@echo off
chcp 65001 >nul
echo.
echo ===============================================
echo    نظام البحث المحسن في القوانين البحرينية
echo   تطبيق ويب مع عرض الصفحات الكاملة
echo ===============================================
echo.
echo جاري تشغيل الخادم المحسن...
echo.
echo  الروابط المهمة:
echo    الموقع الرئيسي: http://localhost:8000
echo    واجهة برمجة التطبيقات: http://localhost:8000/api/docs
echo    الإحصائيات: http://localhost:8000/api/stats
echo    عرض صفحة مثال: http://localhost:8000/page/قانون العمل في القطاع الأهلي/3
echo.
echo  للإيقاف: اضغط Ctrl+C
echo.
echo ===============================================
echo.
python enhanced_web_app.py
echo.
echo تم إيقاف الخادم المحسن.
pause
