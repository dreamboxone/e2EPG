# e2EPG

این پلاگین متن EPG کانال‌های ماهواره‌ای را با Gemini از هر زبان به فارسی
ترجمه می‌کند. دیتابیس اصلی EPG تغییر نمی‌کند و تا آماده‌شدن ترجمه یا هنگام
خطا، متن اصلی نمایش داده می‌شود.

## کلید API

فایل زیر را روی رسیور بسازید:

```text
/root/apikey.txt
```

فقط API key جمینای را در یک خط داخل فایل قرار دهید و ذخیره کنید. permission
پیشنهادی:

```sh
chmod 600 /root/apikey.txt
```

کلید در URL، command line، cache یا log نوشته نمی‌شود. توجه کنید که با فعال
کردن پلاگین، متن EPG برای ترجمه به سرویس Gemini گوگل ارسال می‌شود.

## استفاده در Skin

```xml
<convert type="e2EPG">Name</convert>
<convert type="e2EPG">ShortDescription</convert>
<convert type="e2EPG">ExtendedDescription</convert>
<convert type="e2EPG">FullDescription</convert>
```

## گزارش خطا

در صورت نیاز گزینه «ثبت جزئیات عیب‌یابی» را فعال کنید. گزارش داخل رابط پلاگین
نمایش داده نمی‌شود و برای توسعه‌دهنده از طریق SSH در این فایل‌ها در دسترس است:

```text
/tmp/e2EPG.log
/tmp/e2EPG.log.1
```

متن EPG و API key داخل log ثبت نمی‌شوند.

## نصب و ارتقا

نسخه ۰.۵.۳ در دو قالب DEB و IPK با معماری `all` منتشر می‌شود. چون payload
کاملاً Python است، همان بسته روی دریم‌باکس‌های ARM64 و غیر ARM64 و همچنین
رسیورهای OE-A مانند Vu+ و Gigablue قابل نصب است. وابستگی SQLite به‌صورت جایگزین
`python3-sqlite3 | python-sqlite3` تعریف شده تا ایمیج‌های Python 3 جدید و
Python 2 قدیمی پوشش داده شوند. معماری `all` به معنی مستقل‌بودن از CPU است؛
Rendererهای اختصاصی بعضی اسکین‌ها همچنان ممکن است به adapter جدا نیاز داشته باشند.

فایل‌های نصب:

```sh
dpkg -i /tmp/enigma2-plugin-extensions-e2epg_0.5.3_all.deb
opkg install /tmp/enigma2-plugin-extensions-e2epg_0.5.3_all.ipk
```

لایه سازگاری در زمان عادی اجرای Enigma2 و هر ده دقیقه نوع ایمیج، معماری، نسخه
Python و XMLهای اصلی یا ماژولار اسکین را بررسی می‌کند. هنگام خاموش‌شدن هیچ اسکن
فایلی انجام نمی‌شود. اسکین جدید یا تازه انتخاب‌شده برای اجرای بعدی Enigma2
خودکار آماده می‌شود. مسیرهای استاندارد InfoBar، فهرست کانال‌ها،
پنل Channel Selection و جدول EPG Next پشتیبانی می‌شوند. Rendererهای اختصاصی
ناشناخته تغییر نمی‌کنند و در `/tmp/e2EPG.log` گزارش می‌شوند.

ویرایش اسکین اتمیک است؛ پشتیبان‌ها در `/etc/enigma2/e2EPG/skin-backups` و
وضعیت تشخیص در `/etc/enigma2/e2EPG/skin-compat.json` نگهداری می‌شود. پس از نصب
یا حذف موفق، Enigma2 خودکار restart می‌شود و `/root/apikey.txt` حفظ می‌شود.
