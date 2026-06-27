# ตั้งค่าอัปรูปขึ้น Google Drive ด้วยบัญชีคุณเอง (OAuth) — ทำครั้งเดียว

> ทำไม: **Service Account ไม่มีพื้นที่เก็บไฟล์ (quota=0)** จึงอัปไฟล์ลง "My Drive" ส่วนตัวไม่ได้ (error 403 storageQuotaExceeded)
> วิธีแก้: ให้ระบบอัปรูป **ในนามบัญชี Gmail ของคุณ (15GB)** แทน — Sheet ยังใช้ Service Account เหมือนเดิม

## 0) ลบโฟลเดอร์รูปว่างเปล่าทิ้งก่อน (สำคัญ)
ในโฟลเดอร์ `Photo` ตอนนี้มีโฟลเดอร์ย่อยว่างเปล่า (เช่น `G003`, `H001`, `N001`, `P001`, `R001`) ที่ Service Account สร้างไว้ → **ลบทิ้งให้หมด** (มันว่าง ไม่มีข้อมูล) เพื่อให้รอบใหม่สร้างโฟลเดอร์ใหม่ในนามคุณ (ไม่ติดสิทธิ์)

## 1) Google Cloud Console (ครั้งเดียว)
1. ไป https://console.cloud.google.com → สร้าง/เลือก project
2. **APIs & Services → Library →** เปิดใช้ **"Google Drive API"**
3. **APIs & Services → OAuth consent screen →** เลือก **External** → กรอกชื่อแอป + อีเมลคุณ → ในหน้า **Test users** เพิ่มอีเมล Gmail ของคุณ (บัญชีเดียวกับที่เป็นเจ้าของโฟลเดอร์ `Photo`)
4. **APIs & Services → Credentials → Create credentials → OAuth client ID →** เลือกชนิด **Desktop app** → **Download JSON** → เซฟชื่อ `client_secret.json` ไว้ในโฟลเดอร์โปรเจกต์

## 2) ขอ refresh token (รันในเครื่อง)
```bash
# ในโฟลเดอร์โปรเจกต์ ด้วย venv ของโปรเจกต์
.venv\Scripts\python.exe -m pip install google-auth-oauthlib
.venv\Scripts\python.exe -m kobo_sync.get_oauth_token client_secret.json
```
- เบราว์เซอร์จะเด้งให้ล็อกอิน + กดอนุญาต (เลือกบัญชีเจ้าของโฟลเดอร์ `Photo`)
- ถ้าขึ้นเตือน "Google hasn't verified this app" → Advanced → Go to ... (เพราะเป็นแอปส่วนตัวของคุณเอง)
- เสร็จแล้วสคริปต์จะพิมพ์ค่า 3 ตัวออกมา

## 3) ใส่ Secret ใน GitHub (repo `kobo_sync`)
**Settings → Secrets and variables → Actions → New repository secret** เพิ่ม 3 ตัว:

| Secret | ค่า |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | จากผลลัพธ์สคริปต์ |
| `GOOGLE_OAUTH_CLIENT_SECRET` | จากผลลัพธ์สคริปต์ |
| `GOOGLE_OAUTH_REFRESH_TOKEN` | จากผลลัพธ์สคริปต์ |

> `GOOGLE_SA_JSON`, `SHEET_ID`, `DRIVE_FOLDER_ID`, `KOBO_TOKEN`, `KOBO_ASSET_UID` ที่มีอยู่แล้ว — **เก็บไว้เหมือนเดิม**

## 4) รัน + ตรวจ
- **Actions → Kobo sync → Run workflow**
- เปิดโฟลเดอร์ `Photo` → จะเห็นโฟลเดอร์ตาม Store ID มี **รูปจริง** (front.jpg / qr.jpg)
- ในชีตแท็บ `data` ช่องรูปจะเปลี่ยนจาก `ລໍຖ້າອັບໂຫລດ` เป็นลิงก์ `ເບິ່ງຮູບ`
- ใน log จะไม่มี error 403 storageQuotaExceeded อีก

## หมายเหตุ
- ปลอดภัย: ตราบใดที่รูปยังไม่ขึ้นครบ Kobo จะ**ไม่ถูกลบ** (ARCHIVE_MODE=off + กันด้วย photo_complete)
- ความจุ: 15GB ของ Gmail — รูปถูกตั้ง max-pixels ให้เล็ก (~0.3–1MB/ใบ) ถ้าเก็บหลายพันร้านควรเฝ้าดูพื้นที่
- โค้ดจะใช้ OAuth อัตโนมัติเมื่อมี secret ทั้ง 3; ถ้าไม่มีจะกลับไปใช้ Service Account (สำหรับ Shared Drive)
