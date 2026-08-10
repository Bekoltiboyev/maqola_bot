# 📚 Maqola qabul qilish Telegram boti

Ilmiy jurnal uchun maqolalarni qabul qiluvchi, ro'yxatdan o'tkazuvchi va
adminga xabar beruvchi to'liq funksional Telegram bot.

## ⚙️ Imkoniyatlari

- `/start` bosilganda tanishtiruv videosi + ro'yxatdan o'tish (Ism-familiya, telefon, tg_id avtomatik)
- Asosiy menyu: **Maqola yuborish**, **Men yuborgan maqolalar**, **Jurnallar soni**, **Axborot xati**, **Maqola namunasi**
- Faqat `.doc` / `.docx` / `.pdf` fayllar qabul qilinadi — boshqa format, matn, raqam yoki rasm yuborilsa ogohlantiradi
- Har bir foydalanuvchi **bitta jurnal uchun faqat bitta maqola** yubora oladi
- Admin "Yangi jurnal ochish" tugmasini bosganda:
  - yangi jurnal yaratiladi
  - **hammaga** avtomatik xabarnoma yuboriladi
  - barcha foydalanuvchilar yana bitta maqola yuborish huquqiga ega bo'ladi
- Kelgan har bir maqola avtomatik ravishda barcha adminlarga (fayl + yuboruvchi ma'lumotlari bilan) yuboriladi
- Admin panel (`/admin`) — faqat adminlarga ko'rinadi:
  - Yangi jurnal ochish va xabar tarqatish
  - Axborot xati / Maqola namunasi fayllarini yuklash (istalgan vaqt yangilanadi)
  - Statistika (foydalanuvchilar, jurnallar, maqolalar soni)

## 🔐 Xavfsizlik choralari

- `.env` orqali maxfiy token va admin ID'lar (repo'ga tushmaydi, `.gitignore`da)
- Fayl kengaytmasi **va** fayl sarlavhasi (magic bytes) tekshiriladi — buzilgan yoki qayta nomlangan fayllar rad etiladi
- Fayl hajmi cheklovi (standart: 20MB)
- SQLite so'rovlari parametrlashtirilgan (SQL Injection'dan himoya)
- Har bir yuklangan fayl noyob (`uuid`) nom bilan saqlanadi — fayllar bir-birini bosib yozmaydi
- Docker konteyner **root bo'lmagan** foydalanuvchi ostida ishlaydi
- Admin funksiyalari faqat `ADMIN_IDS` ro'yxatidagi Telegram ID'larga ochiq
- Ro'yxatdan o'tmagan foydalanuvchilar menyudan foydalana olmaydi

## 📁 Loyiha strukturasi

```
maqola_bot/
├── bot.py                  # Ishga tushirish nuqtasi
├── config.py                # Sozlamalar (.env o'qiydi)
├── database.py               # SQLite bilan ishlash
├── states.py                 # FSM holatlari
├── keyboards.py               # Tugmalar
├── handlers/
│   ├── registration.py        # /start, ro'yxatdan o'tish
│   ├── user.py                 # Asosiy menyu, maqola qabul qilish
│   └── admin.py                 # Admin panel
├── media/
│   └── intro.mp4               # (o'zingiz qo'shasiz) tanishtiruv video
├── storage/
│   ├── database.db              # avtomatik yaratiladi
│   └── articles/                # yuborilgan maqolalar shu yerda saqlanadi
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## 🚀 Serverga o'rnatish (Docker bilan)

1. Loyihani serverga yuklang va papkaga kiring:
   ```bash
   cd maqola_bot
   ```

2. `.env` faylini yarating:
   ```bash
   cp .env.example .env
   nano .env
   ```
   - `BOT_TOKEN` — @BotFather dan olingan token
   - `ADMIN_IDS` — admin(lar)ning Telegram ID raqami(lari), vergul bilan

3. (Ixtiyoriy) `media/intro.mp4` fayliga tanishtiruv videongizni joylang.

4. Botni ishga tushiring:
   ```bash
   docker compose up -d --build
   ```

5. Loglarni kuzatish:
   ```bash
   docker compose logs -f
   ```

6. To'xtatish:
   ```bash
   docker compose down
   ```

Ma'lumotlar bazasi va yuborilgan maqolalar `./storage` papkasida (host mashinada)
saqlanadi — konteyner qayta qurilsa ham ma'lumotlar yo'qolmaydi.

## 👨‍💻 Admin bilan ishlash

1. Botga `/admin` buyrug'ini yuboring (faqat `ADMIN_IDS` da bo'lsangiz ishlaydi).
2. **"✉️ Axborot xatini yuklash"** / **"📑 Maqola namunasini yuklash"** tugmasini bosib, mos faylni yuboring — bu fayllar shundan keyin barcha foydalanuvchilarga tegishli tugma bosilganda yuboriladi (istalgancha marta qayta yuklab, yangilashingiz mumkin).
3. **"🆕 Yangi jurnal ochish"** tugmasi bosilganda:
   - yangi jurnal raqami yaratiladi,
   - barcha ro'yxatdan o'tgan foydalanuvchilarga avtomatik xabar boradi,
   - hamma yana bitta maqola yubora oladi.
4. Har bir kelgan maqola avtomatik ravishda sizga (barcha adminlarga) fayl + yuboruvchi ma'lumotlari bilan yetib boradi — alohida tekshirish shart emas.

## 🧪 Lokal test (Docker'siz, ixtiyoriy)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # va tahrirlang
python bot.py
```

## 📝 Eslatma

- Bot **polling** rejimida ishlaydi (webhook shart emas), shu sabab alohida domen/SSL kerak emas.
- Bitta jurnal ichida user faylni noto'g'ri formatda yuborsa, u qayta urinib ko'rishi mumkin — cheklov faqat **muvaffaqiyatli qabul qilingan** maqoladan keyin ishga tushadi.
