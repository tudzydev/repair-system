# โปรเจ็กต์ฝึกเขียนระบบแจ้งซ่อมโรงเรียน

โปรเจ็กต์นี้ใช้ Flask + SQLite + SQLAlchemy + Jinja2 ตามใบงาน `index.html` มีซอร์สโค้ดให้เปิดอ่าน แก้ไข และรันบนเครื่องของคุณ คำตอบแต่ละข้ออยู่ใน `index.html` และเชื่อมโยงกับไฟล์โค้ดจริง

## 1. เตรียมเครื่องและสร้างโปรเจ็กต์

ติดตั้ง Python 3.10 ขึ้นไป (แนะนำ 3.11 หรือ 3.12) และโปรแกรมแก้โค้ด เช่น VS Code จากนั้นเปิด Terminal ในโฟลเดอร์นี้

ถ้าจะเริ่มเขียนใหม่เอง ให้สร้างโฟลเดอร์แล้วค่อยคัดลอกหรือพิมพ์ไฟล์ตามโครงสร้างด้านล่าง:

```sh
mkdir school-repair
cd school-repair
```

ถ้าใช้ซอร์สโค้ดที่เตรียมไว้ในโฟลเดอร์ `repair-system` ให้ใช้โฟลเดอร์เดิมได้เลย ไม่ต้องสร้างซ้ำ

ตรวจสอบ Python และ SQLite:

```sh
python3 --version
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
```

SQLite ต้องเป็นเวอร์ชัน 3.35 ขึ้นไป เพราะตัวนับเลขใบแจ้งซ่อมใช้ `RETURNING` หากต่ำกว่านั้นให้ติดตั้ง Python รุ่นใหม่ที่มาพร้อม SQLite รุ่นใหม่

## 2. สร้าง virtual environment และติดตั้งไลบรารี

macOS / Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

ถ้า PowerShell ไม่อนุญาตให้ activate สามารถใช้ `.\.venv\Scripts\python.exe` แทน `python` ในคำสั่งถัดไป หรือเปิด Command Prompt แล้วใช้ `.venv\Scripts\activate.bat`

หน้าที่ของไลบรารี:

| ไลบรารี | ใช้ทำอะไร |
| --- | --- |
| Flask | รับ HTTP request และจัดการ routes |
| Flask-SQLAlchemy | อ่านและเขียนฐานข้อมูลด้วยโมเดล Python |
| Flask-Login | จัดการผู้ใช้ที่เข้าสู่ระบบและ session |
| Flask-WTF | ตรวจ CSRF token ในฟอร์ม POST |
| Pillow | ตรวจว่าไฟล์ที่อัปโหลดเป็นภาพจริง |
| WeasyPrint (เสริม) | สร้าง PDF จาก HTML |

## 3. สร้างฐานข้อมูลและเปิดเว็บ

บน macOS ใช้ `./start.command` เพื่อสร้าง environment `.venv-app` ติดตั้งแพ็กเกจที่จำเป็น สร้างฐานข้อมูลและบัญชีฝึก แล้วเปิด Flask บนพอร์ต 5001 จากนั้นเปิด `http://127.0.0.1:5001/login` ค้าง Terminal ไว้ระหว่างใช้งาน และกด Ctrl+C เมื่อต้องการหยุดระบบ การติดตั้งครั้งแรกต้องเชื่อมต่ออินเทอร์เน็ต

Live Server พอร์ต 5500 ใช้ดูหน้าตัวอย่างเท่านั้น ไม่สามารถเข้าสู่ระบบหรือบันทึกข้อมูลได้

```sh
python -m flask --app app:create_app init-db
python -m flask --app app:create_app run --debug
```

เปิด `http://127.0.0.1:5000` ในเบราว์เซอร์ ถ้าพอร์ตถูกใช้อยู่ ให้เพิ่ม `--port 5001` ในคำสั่ง run แล้วเปิดพอร์ต 5001

คำสั่ง `init-db` สร้างตารางและเพิ่มบัญชีฝึกที่ยังไม่มี โดยไม่ล้างข้อมูลเดิม ฐานข้อมูลอยู่ที่ `instance/repair.db` รูปที่อัปโหลดอยู่ใน `instance/uploads/` และ secret สำหรับ session อยู่ที่ `instance/secret.key`

| ชื่อผู้ใช้ | รหัสผ่านสำหรับฝึก | บทบาท |
| --- | --- | --- |
| `admin` | `Practice123!` | ผู้ดูแล: ดูทุกงาน มอบหมายงาน เพิ่มผู้ใช้ |
| `teacher` | `Practice123!` | ครู: สร้างใบแจ้งซ่อม ดูงานของตัวเอง |
| `technician` | `Practice123!` | เจ้าหน้าที่: ดูและอัปเดตงานที่ได้รับมอบหมาย |

ใช้บัญชีเหล่านี้ในเครื่องสำหรับฝึก ก่อนนำไปใช้งานจริงให้เปลี่ยนรหัสผ่าน ปิด debug และกำหนดค่า session cookie ให้เหมาะกับ HTTPS

## 4. โครงสร้างไฟล์และลำดับอ่านโค้ด

```text
repair-system/
├── index.html                 คำถามและคำตอบใบงาน
├── README.md                  คู่มือฝึก
├── requirements.txt           ไลบรารีหลัก
├── requirements-pdf.txt       ไลบรารีเสริมสำหรับ PDF
├── models.py                  ตารางและกฎเปลี่ยนสถานะ
├── services.py                สร้างเลขใบแจ้งซ่อม / ตรวจไฟล์ภาพ
├── app.py                     สร้างแอป / routes / สิทธิ์
├── schema.sql                 SQL สำหรับศึกษาตารางเดียวกับโมเดล
├── templates/
│   ├── base.html              เมนูหลักและข้อความแจ้งผล
│   ├── login.html             เข้าสู่ระบบ
│   ├── dashboard.html         สถิติ
│   ├── create_repair.html     ฟอร์มแจ้งซ่อม
│   ├── repairs.html           ค้นหาและกรองงาน
│   ├── repair_detail.html     มอบหมาย / ซ่อม / รูป / ความคิดเห็น
│   ├── users.html             รายการและเพิ่มผู้ใช้
│   ├── print_repair.html      เอกสาร A4 และ PDF
│   └── error.html             หน้าข้อผิดพลาด
├── static/
│   ├── style.css
│   ├── ui.js                  แสดงรหัสผ่าน / ตัวอย่างภาพแนบ
│   └── alerts.js              ตัวอย่าง SweetAlert2 เดิม (ไม่ได้โหลดในหน้าปัจจุบัน)
├── tests/test_workflow.py     ทดสอบ workflow และสิทธิ์
└── instance/                  สร้างอัตโนมัติเมื่อรัน
```

เริ่มอ่าน `models.py` → `services.py` → `app.py` → `templates/` หน้าปัจจุบันใช้ CSS ภายในโปรเจ็กต์ รองรับหน้าจอมือถือ พร้อมเมนูแสดงหน้าที่กำลังเปิด ตัวกรองค้นหา ป้ายสถานะ และข้อความแจ้งผลที่อ่านได้โดยไม่ต้องปิด popup

โค้ด `RepairRequest` ในแอปเป็น SQLAlchemy Model จึงไม่ใช่ dataclass แบบตัวอย่างในใบงาน แต่ทำหน้าที่แทนใบแจ้งซ่อมเหมือนกัน

การทำงานของหนึ่งคำขอ:

```text
Browser ส่งฟอร์ม
  → Flask route ตรวจ login / role / CSRF / ข้อมูล
  → Model และ Service ทำงาน
  → db.session.commit() บันทึก SQLite
  → redirect ไปหน้ารายละเอียด
  → Jinja2 แสดงข้อมูลและ ข้อความแจ้งผลบนหน้าเว็บ
```

ตัวอย่างโค้ดที่ควรลองแก้เป็นข้อแรกใน `services.py`:

```python
def generate_request_no(sequence_number: int, now=None) -> str:
    now = now or datetime.now()
    if not 1 <= sequence_number <= 999:
        raise ValueError("รูปแบบเลข 3 หลักรองรับสูงสุด 999 ใบต่อเดือน")
    return f"RP-{now:%Y%m}-{str(sequence_number).zfill(3)}"
```

ลองเปลี่ยน prefix `RP` เป็น `FIX` แล้วรันทดสอบ คุณจะเห็นว่าทดสอบรูปแบบเลขไม่ผ่าน จากนั้นเปลี่ยนกลับ นี่เป็นตัวอย่างการใช้ test ตรวจผลจากการแก้โค้ด

## 5. ฝึกใช้งานครบหนึ่งวงจร

1. เข้าสู่ระบบด้วย `teacher` เปิด **แจ้งซ่อมใหม่** กรอกอาคาร 3 ห้อง 301 ประเภทแอร์ และรายละเอียด “แอร์ไม่เย็น” แนบภาพ JPG หรือ PNG แล้วส่ง
2. จดเลขใบแจ้งซ่อม เช่น `RP-202610-001` เลขส่วนกลางขึ้นกับเดือนที่รันจริง
3. ออกจากระบบ แล้วเข้า `admin` เปิดรายการและใบแจ้งซ่อมดังกล่าว มอบหมายให้ `technician` พร้อมกำหนดวันเสร็จ
4. เข้า `technician` เปิดงานที่ได้รับมอบหมาย กด **เริ่มซ่อม** สถานะจะเปลี่ยนเป็นกำลังดำเนินการ
5. อัปโหลดภาพหลังซ่อม กรอกค่าใช้จ่ายและผลการซ่อม แล้วกด **บันทึกซ่อมเสร็จ**
6. เข้า `teacher` อีกครั้ง ตรวจสถานะ เพิ่มความคิดเห็น และเปิดหน้าพิมพ์
7. ทดลองค้นหา กรองสถานะ และส่งออก CSV ไฟล์จะมีข้อมูลตามสิทธิ์และตัวกรองเดียวกับหน้ารายการ

Dashboard แยก “รอรับเรื่อง” และ “รับเรื่องแล้ว” เพื่อให้ผลรวมทั้งสี่สถานะตรงกับจำนวนงานทั้งหมด

## 6. วิธีฝึกเขียนทีละส่วน

ทำทีละข้อแล้วตรวจผลบนหน้าเว็บ อย่าคัดลอกทั้งระบบในครั้งเดียวถ้าต้องการฝึกความเข้าใจ

| ขั้น | ไฟล์ที่ศึกษา | งานฝึก | ผลที่ควรเห็น |
| --- | --- | --- | --- |
| 1 | `app.py` | เพิ่ม route `/hello` คืนข้อความ `Hello Flask` | เปิด URL แล้วเห็นข้อความ |
| 2 | `models.py` | อ่านตาราง User แล้วลอง query ผู้ใช้ใน Flask shell | ได้ผู้ใช้ฝึก 3 คน |
| 3 | `login.html`, route `login` | ลองรหัสผ่านผิดและลองเปิด `/dashboard` ก่อน login | ได้ข้อความผิดพลาดหรือถูกส่งไป login |
| 4 | `create_repair.html`, route `create_repair` | เพิ่มข้อความแนะนำใต้ช่องรายละเอียด | เห็นข้อความและสร้างงานได้ |
| 5 | เมธอด `assign_to`, `start_repair`, `complete_repair` | ไล่เงื่อนไขเปลี่ยนสถานะและลองข้ามขั้นตอน | ระบบปฏิเสธการเปลี่ยนสถานะผิดลำดับ |
| 6 | `save_image`, route `image_file` | ลองอัปโหลดไฟล์ข้อความเปลี่ยนชื่อเป็น `.jpg` | ระบบปฏิเสธไฟล์ปลอม |
| 7 | route `dashboard`, `dashboard.html` | เพิ่มสถิติจำนวนงานเร่งด่วน โดยคงขอบเขตสิทธิ์เดิม | ครูเห็นเฉพาะงานตัวเอง |
| 8 | `base.html`, route `export_csv` | แก้ข้อความแจ้งผลและเพิ่มคอลัมน์ CSV | ข้อความและไฟล์ส่งออกเปลี่ยนตามโค้ด |

ทดลอง query ใน shell:

```sh
python -m flask --app app:create_app shell
```

```python
from models import db, User, RepairRequest
from sqlalchemy import select
users = db.session.scalars(select(User)).all()
[(user.username, user.role) for user in users]
repairs = db.session.scalars(select(RepairRequest)).all()
[(repair.request_no, repair.status) for repair in repairs]
```

แบบฝึกต่อยอด: เพิ่ม pagination, หน้าแก้ไขข้อมูลผู้ใช้, การปิดใช้งานบัญชีแทนการลบประวัติ, ประวัติการเปลี่ยนสถานะ และฟังก์ชันรีเซ็ตรหัสผ่าน โปรเจ็กต์ตัวอย่างนี้มีหน้ารายการและเพิ่มผู้ใช้ ส่วนการแก้ไข/ลบผู้ใช้เป็นงานต่อยอด

ถ้าเพิ่มคอลัมน์ในโมเดลภายหลัง `db.create_all()` จะไม่แก้ตารางเดิม ต้องเขียน migration หรือใช้ฐานข้อมูลใหม่สำหรับการฝึก และเก็บสำรองข้อมูลก่อนเปลี่ยนโครงสร้าง

## 7. PDF

เริ่มจากปุ่ม **พิมพ์ / Save as PDF** ซึ่งใช้การพิมพ์ของเบราว์เซอร์และ CSS ขนาด A4 ได้ทันที

ถ้าต้องการปุ่มดาวน์โหลด PDF จากเซิร์ฟเวอร์:

```sh
python -m pip install -r requirements-pdf.txt
python -m weasyprint --info
```

WeasyPrint ต้องมี Pango และฟอนต์ไทย เช่น Noto Sans Thai หรือ Sarabun ติดตั้งในระบบด้วย ดูขั้นตอนตามระบบปฏิบัติการที่ [คู่มือติดตั้ง WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html) หากยังติดตั้งไม่ครบ แอปจะพาไปหน้าพิมพ์ พร้อมข้อความแจ้ง

## 8. ทดสอบและแก้ปัญหา

```sh
python -m unittest discover -s tests -v
```

ทดสอบนี้ใช้ฐานข้อมูลในหน่วยความจำและโฟลเดอร์ภาพชั่วคราว ตรวจ workflow, การห้ามข้ามสถานะ, สิทธิ์ครูคนอื่น, CSRF, ไฟล์ภาพปลอม, เลขใบแจ้งซ่อมไม่ซ้ำ และ CSV โดยไม่แก้ฐานข้อมูลสำหรับฝึก

| อาการ | วิธีตรวจ |
| --- | --- |
| `No module named flask` | activate `.venv` และติดตั้ง requirements ด้วย Python ตัวเดียวกับที่รัน |
| `no such table: users` | รันคำสั่ง `init-db` ก่อนเปิดเว็บ |
| `CSRF token is missing` | ใส่ hidden input `csrf_token` ในทุกฟอร์ม POST |
| เปิดรายละเอียดแล้ว 404 | ตรวจว่าครูเป็นผู้แจ้ง หรือเจ้าหน้าที่ได้รับมอบหมายงานนั้น |
| รูปอัปโหลดไม่ได้ | ใช้ JPG/PNG/GIF จริง และข้อมูลรวมต่อ request ไม่เกิน 5 MB |
| ไม่เห็นข้อความแจ้งผล | ตรวจส่วนบนของหน้าเว็บ ข้อความแสดงในหน้าโดยไม่มี popup |
| PDF ภาษาไทยเป็นสี่เหลี่ยม | ติดตั้งฟอนต์ไทยบนเครื่องที่สร้าง PDF |
| `pip` เชื่อมต่อไม่ได้ | ตรวจอินเทอร์เน็ตหรือการตั้งค่า proxy แล้วติดตั้งใหม่ |

หน้าปัจจุบันโหลด `static/style.css` และ `static/ui.js` จากแอปโดยตรง ไม่ต้องเชื่อมต่อ CDN เพื่อแสดงหน้าตาหรือข้อความแจ้งผล ฟอร์มหลักยังใช้งานได้แม้ปิด JavaScript

ตรวจล่าสุดวันที่ 12 ตุลาคม 2026: ติดตั้งไลบรารีใน `.venv-app` ด้วย Python 3.14.5 และรัน integration tests ทั้ง 3 รายการผ่านแล้ว รวมถึงตรวจการตั้งค่า Docker Compose ผ่าน PDF ยังต้องตรวจบนเครื่องที่ติดตั้ง WeasyPrint/Pango และยังไม่ได้ทดสอบขึ้นเซิร์ฟเวอร์จริง

## 9. ตั้งค่าเซิร์ฟเวอร์ด้วย Docker

ไฟล์ที่ใช้คือ `Dockerfile`, `compose.yaml`, `requirements-production.txt` และไฟล์ใน `deploy/` ต้องติดตั้ง Docker พร้อม Compose และมีโดเมนที่ชี้มายังเซิร์ฟเวอร์ โดยเปิดพอร์ต 80 และ 443

หากยังไม่มีไฟล์ตั้งค่าจริง ให้สร้างจากตัวอย่าง:

```sh
cp deploy/server.env.example deploy/server.env
chmod 600 deploy/server.env
```

แก้ `deploy/server.env` โดยใส่ `DOMAIN` เป็นโดเมนจริง, `SECRET_KEY` ยาวอย่างน้อย 32 ตัวอักษร และ `ADMIN_PASSWORD` ยาวอย่างน้อย 12 ตัวอักษร หากไฟล์นี้ถูกเตรียมพร้อมค่าที่สุ่มไว้แล้ว ให้เก็บค่าเหล่านั้นและเปลี่ยนเฉพาะโดเมนตามต้องการ ไฟล์นี้เก็บรหัสผ่าน จึงถูกยกเว้นจาก Git, Docker build context และ ZIP ซอร์สโค้ด

ตรวจค่าตั้งค่าและเริ่มเซิร์ฟเวอร์:

```sh
docker compose --env-file deploy/server.env config --quiet
docker compose --env-file deploy/server.env up -d --build
```

เปิด `https://<โดเมนจริง>/login` และใช้บัญชีในไฟล์ตั้งค่า ระบบจะสร้างฐานข้อมูลและผู้ดูแลครั้งแรกโดยไม่เพิ่มบัญชีฝึก ข้อมูลเก็บใน Docker volume `repair-data` การเปลี่ยน `ADMIN_PASSWORD` ในไฟล์ตั้งค่าจะไม่เปลี่ยนรหัสผ่านบัญชีที่สร้างแล้ว

## 10. เผยแพร่ด้วย GitHub Pages

Workflow `.github/workflows/deploy.yml` ใช้ GitHub-hosted runner (`ubuntu-latest`) สร้างเว็บด้วย `scripts/build_pages.py` และเผยแพร่ GitHub Pages เมื่อ push เข้า `main` หรือกด **Actions → Deploy GitHub Pages → Run workflow** ไม่ต้องติดตั้ง self-hosted runner, Docker หรือกำหนด secret เพื่อเผยแพร่ใบงาน

1. เปิด **Settings → Pages → Build and deployment → Source** แล้วเลือก **GitHub Actions**
2. Commit และ push การเปลี่ยนแปลงเข้า `main`
3. ยกเลิก workflow เก่า **Deploy self-hosted** ที่ยัง Queued/Pending แล้วติดตาม workflow ใหม่ **Deploy GitHub Pages** ในแท็บ Actions
4. เมื่อสำเร็จ เปิด https://tudzydev.github.io/repair-system/

GitHub Pages แสดงใบงาน, CSS/JavaScript, ตัวอย่างหน้าเข้าสู่ระบบ และซอร์สโค้ดสำหรับศึกษา หน้าเข้าสู่ระบบตัวอย่างปิดช่องกรอกและปุ่มส่งไว้อย่างชัดเจน เพราะ GitHub Pages ไม่รัน Python/Flask และไม่สามารถใช้ฐานข้อมูล SQLite สำหรับระบบจริงได้ หากต้องการเข้าสู่ระบบและบันทึกข้อมูล ให้ดาวน์โหลด ZIP แล้วรัน Flask ตามคู่มือ หรือใช้ Docker บนเซิร์ฟเวอร์ตามข้อ 9

เว็บที่เผยแพร่มีเฉพาะไฟล์สาธารณะที่ระบุในสคริปต์ build ไม่รวม `instance/`, `.env`, `deploy/server.env` หรือ virtual environment ตรวจ build บนเครื่องได้ด้วย `python3 scripts/build_pages.py` ผลลัพธ์อยู่ใน `_site/` ซึ่งถูกยกเว้นจาก Git

ไฟล์ `deploy/deploy.sh` ยังใช้สำหรับ deploy Docker บน Linux ด้วยตนเองได้ แต่ไม่ได้ถูกเรียกจาก GitHub Actions อีกต่อไป

ดู [การตั้งค่า publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) และ [workflow สำหรับ GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

## เอกสารที่ใช้ประกอบ

- [Flask: การอัปโหลดไฟล์](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/)
- [Flask-Login: session และ login_required](https://flask-login.readthedocs.io/en/latest/)
- [SQLAlchemy: SELECT ด้วย ORM](https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html)
- [Flask-WTF: CSRF Protection](https://flask-wtf.readthedocs.io/en/1.2.x/csrf/)
- [SweetAlert2](https://sweetalert2.github.io/)
