# متجر الشميري المستقل

تطبيق Flask مستقل عن Whacka، بواجهة عربية RTL وقاعدة SQLite وملفات على قرص Render دائم، وإدارة للمنتجات والطلبات والتحويل اليدوي.

## تشغيل محلي

    cd server
    python -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
    export SECRET_KEY='غيّر هذه القيمة إلى سر عشوائي طويل'
    export ADMIN_USERNAME='admin'
    export ADMIN_PASSWORD='كلمة مرور قوية لا تقل عن 12 حرفاً'
    export PAYMENT_ACCOUNT='رقم حساب الاستلام'
    export PAYMENT_HOLDER='اسم المستفيد'
    python app.py

افتح http://127.0.0.1:5000 ولوحة الإدارة /admin/login. لا يتم إنشاء حساب الإدارة ما لم تكن ADMIN_PASSWORD موجودة وطولها 12 حرفاً على الأقل.

## النشر على Render

1. أنشئ Web Service من هذا المستودع وحدد Root Directory باسم server.
2. Build: pip install -r requirements.txt. Start: gunicorn app:app --workers 1 --threads 4.
3. أضف قرصاً دائماً إلى /var/data واضبط DATA_DIR=/var/data.
4. اضبط ADMIN_USERNAME وADMIN_PASSWORD وPAYMENT_ACCOUNT وPAYMENT_HOLDER وSUPPORT_PHONE من إعدادات Environment، ولا تضعها في ملفات Git.
5. القرص الدائم والخدمة المدفوعة مطلوبان للاحتفاظ بقاعدة البيانات والملفات بعد إعادة التشغيل. لا تستخدم الخطة المجانية لتخزين بيانات المتجر الدائمة.

## سير العمل

العميل يطلب منتجاً، يرسل رقم العملية أو إيصال التحويل، ويبقى الطلب pending. الإدارة وحدها تستطيع تحويل الحالة إلى paid. رابط التنزيل يتحقق من حالة الدفع قبل إرسال الملف. لا توجد بوابة دفع إلكترونية مدمجة.

## ملاحظات قبل الإطلاق

- أدخل بيانات الاستلام الحقيقية بنفسك في إعدادات Render؛ لا تضع بيانات الدخول البنكية أو أسراراً في الواجهة.
- النسخة الحالية تستخدم SQLite على قرص دائم وعاملاً واحداً. عند التوسع إلى عدة نسخ أو حركة كبيرة، انقل قاعدة البيانات إلى PostgreSQL والتخزين إلى خدمة ملفات خاصة.
- أضف منتجاتك من لوحة الإدارة بعد إعداد حساب المدير.
