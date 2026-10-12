"""จุดเริ่มต้น Flask และ routes สำหรับฝึกตามใบงาน index.html."""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from io import StringIO
from pathlib import Path
import csv
import os
import secrets
import sqlite3

import click
from flask import (Flask, abort, flash, redirect, render_template, request,
                   Response, send_from_directory, session, url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event, func, or_, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db, User, RepairRequest, RepairImage, Comment
from services import next_request_no, save_image

PROBLEM_TYPES = {"electrical": "ไฟฟ้า", "furniture": "เฟอร์นิเจอร์",
                 "computer": "คอมพิวเตอร์", "aircon": "เครื่องปรับอากาศ", "other": "อื่น ๆ"}
URGENCIES = {"low": "ปกติ", "medium": "ปานกลาง", "high": "เร่งด่วน"}
STATUSES = {"pending": "รอรับเรื่อง", "accepted": "รับเรื่องแล้ว",
            "in_progress": "กำลังดำเนินการ", "completed": "ซ่อมเสร็จ"}


@event.listens_for(Engine, "connect")
def enable_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys = ON")


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def visible_repairs():
    """ขอบเขตข้อมูลเดียวกันสำหรับรายการ Dashboard และ CSV."""
    stmt = select(RepairRequest)
    if current_user.role == "teacher":
        stmt = stmt.where(RepairRequest.user_id == current_user.id)
    elif current_user.role == "technician":
        stmt = stmt.where(RepairRequest.assigned_to == current_user.id)
    return stmt


def accessible_repair(repair_id):
    repair = db.session.scalar(visible_repairs().where(RepairRequest.id == repair_id))
    if repair is None:
        abort(404)
    return repair


def filtered_repairs():
    stmt = visible_repairs()
    search = request.args.get("q", "").strip()[:100]
    status = request.args.get("status", "")
    if search:
        term = f"%{search}%"
        stmt = stmt.where(or_(RepairRequest.request_no.ilike(term),
                              RepairRequest.building.ilike(term),
                              RepairRequest.room.ilike(term),
                              RepairRequest.description.ilike(term)))
    if status in STATUSES:
        stmt = stmt.where(RepairRequest.status == status)
    return stmt.order_by(RepairRequest.created_at.desc(), RepairRequest.id.desc())


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    instance = Path(app.instance_path)
    instance.mkdir(parents=True, exist_ok=True)
    # เก็บ secret ลงไฟล์ครั้งแรก ทำให้ session ยังใช้ได้หลัง restart
    secret_file = instance / "secret.key"
    if not secret_file.exists():
        try:
            with secret_file.open("x") as handle:
                handle.write(secrets.token_hex(32))
            secret_file.chmod(0o600)
        except FileExistsError:
            pass
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secret_file.read_text().strip(),
        SQLALCHEMY_DATABASE_URI="sqlite:///repair.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(instance / "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    if test_config:
        app.config.update(test_config)
    if os.environ.get("APP_ENV") == "production" and not app.config.get("TESTING"):
        if len(os.environ.get("SECRET_KEY", "")) < 32:
            raise RuntimeError("Production requires SECRET_KEY with at least 32 characters")
        app.config["SESSION_COOKIE_SECURE"] = True
        # Gunicorn is only reachable through Caddy in the deployment network.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    CSRFProtect(app)
    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    login_manager.login_message = "กรุณาเข้าสู่ระบบก่อน"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    @app.context_processor
    def labels():
        return dict(problem_types=PROBLEM_TYPES, urgencies=URGENCIES, statuses=STATUSES)

    @app.cli.command("init-db")
    def init_db():
        """สร้างตารางและบัญชีฝึก 3 บทบาท ไม่ล้างข้อมูลเดิม."""
        db.create_all()
        for username, fullname, role in [
            ("admin", "ผู้ดูแลระบบ", "admin"),
            ("teacher", "ครูตัวอย่าง", "teacher"),
            ("technician", "เจ้าหน้าที่ซ่อม", "technician"),
        ]:
            if db.session.scalar(select(User).where(User.username == username)) is None:
                user = User(username=username, fullname=fullname, role=role)
                user.set_password("Practice123!")
                db.session.add(user)
        db.session.commit()
        click.echo("สร้างฐานข้อมูลแล้ว: admin / teacher / technician รหัสผ่าน Practice123!")

    @app.get("/")
    def home():
        return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))

    @app.get("/worksheet")
    def worksheet():
        return send_from_directory(app.root_path, "index.html")

    @app.get("/healthz")
    def healthz():
        db.session.execute(select(1)).scalar_one()
        return {"status": "ok"}

    @app.cli.command("init-production")
    def init_production():
        """Create tables and the first admin without adding practice accounts."""
        db.create_all()
        if db.session.scalar(select(User.id).where(User.role == "admin")) is not None:
            click.echo("Database ready; existing administrator retained.")
            return
        username = os.environ.get("ADMIN_USERNAME", "admin").strip()
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not username or len(username) > 80 or len(password) < 12 or password == "Practice123!":
            raise click.ClickException("Set ADMIN_USERNAME and ADMIN_PASSWORD (at least 12 characters).")
        if db.session.scalar(select(User.id).where(User.username == username)) is not None:
            raise click.ClickException("ADMIN_USERNAME is already used by a non-admin account.")
        user = User(username=username, fullname="ผู้ดูแลระบบ", role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Production administrator created.")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            user = db.session.scalar(select(User).where(User.username == username))
            if user and user.check_password(request.form.get("password", "")):
                session.clear()
                login_user(user, remember=False)
                session.permanent = True
                return redirect(url_for("dashboard"))
            flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        session.clear()
        return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        visible = visible_repairs().subquery()
        counts = dict(db.session.execute(
            select(visible.c.status, func.count()).group_by(visible.c.status)
        ).all())
        stats = {status: counts.get(status, 0) for status in STATUSES}
        return render_template("dashboard.html", stats=stats, total=sum(stats.values()))

    @app.get("/repairs")
    @login_required
    def list_repairs():
        repairs = db.session.scalars(filtered_repairs()).all()
        return render_template("repairs.html", repairs=repairs)

    @app.route("/repair/create", methods=["GET", "POST"])
    @login_required
    @roles_required("teacher")
    def create_repair():
        if request.method == "POST":
            data = {key: request.form.get(key, "").strip() for key in
                    ("building", "room", "problem_type", "description", "urgency")}
            filename = None
            try:
                if not all(data.values()):
                    raise ValueError("กรุณากรอกข้อมูลให้ครบทุกช่อง")
                if data["problem_type"] not in PROBLEM_TYPES or data["urgency"] not in URGENCIES:
                    raise ValueError("ประเภทปัญหาหรือความเร่งด่วนไม่ถูกต้อง")
                if len(data["building"]) > 100 or len(data["room"]) > 50 or len(data["description"]) > 5000:
                    raise ValueError("อาคาร/ห้อง/รายละเอียดเกินความยาวที่กำหนด")
                repair = RepairRequest(request_no=next_request_no(), user_id=current_user.id, **data)
                db.session.add(repair)
                db.session.flush()
                image = request.files.get("image")
                if image and image.filename:
                    filename = save_image(image)
                    db.session.add(RepairImage(repair_id=repair.id, image_type="before", image_path=filename))
                db.session.commit()
            except (ValueError, SQLAlchemyError) as exc:
                db.session.rollback()
                if filename:
                    (Path(app.config["UPLOAD_FOLDER"]) / filename).unlink(missing_ok=True)
                flash(str(exc) if isinstance(exc, ValueError) else "บันทึกข้อมูลไม่ได้ กรุณาลองอีกครั้ง", "error")
                return render_template("create_repair.html"), 400
            flash("แจ้งซ่อมสำเร็จ", "success")
            return redirect(url_for("repair_detail", repair_id=repair.id))
        return render_template("create_repair.html")

    @app.get("/repair/<int:repair_id>")
    @login_required
    def repair_detail(repair_id):
        repair = accessible_repair(repair_id)
        technicians = db.session.scalars(select(User).where(User.role == "technician")).all()
        return render_template("repair_detail.html", repair=repair, technicians=technicians,
                               today=date.today().isoformat())

    @app.post("/repair/<int:repair_id>/assign")
    @login_required
    @roles_required("admin")
    def assign_repair(repair_id):
        repair = accessible_repair(repair_id)
        try:
            technician = db.session.get(User, int(request.form.get("technician_id", "")))
            if technician is None:
                raise ValueError("ไม่พบเจ้าหน้าที่")
            due_date = date.fromisoformat(request.form.get("due_date", ""))
            repair.assign_to(technician, due_date)
            db.session.commit()
            flash("มอบหมายงานสำเร็จ", "success")
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
        return redirect(url_for("repair_detail", repair_id=repair_id))

    @app.post("/repair/<int:repair_id>/status")
    @login_required
    @roles_required("technician")
    def update_status(repair_id):
        repair = accessible_repair(repair_id)
        try:
            action = request.form.get("action")
            if action == "start":
                repair.start_repair()
            elif action == "complete":
                cost = Decimal(request.form.get("cost", "")).quantize(Decimal("0.01"))
                repair.complete_repair(cost, request.form.get("result", ""))
            else:
                raise ValueError("คำสั่งเปลี่ยนสถานะไม่ถูกต้อง")
            db.session.commit()
            flash("อัปเดตสถานะสำเร็จ", "success")
        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            flash(str(exc) if isinstance(exc, ValueError) else "ค่าใช้จ่ายต้องเป็นตัวเลข", "error")
        return redirect(url_for("repair_detail", repair_id=repair_id))

    @app.post("/repair/<int:repair_id>/comments")
    @login_required
    def add_comment(repair_id):
        accessible_repair(repair_id)
        text = request.form.get("comment", "").strip()
        if not text or len(text) > 2000:
            flash("ความคิดเห็นต้องมีความยาว 1–2,000 ตัวอักษร", "error")
        else:
            db.session.add(Comment(repair_id=repair_id, user_id=current_user.id, comment=text))
            db.session.commit()
            flash("เพิ่มความคิดเห็นแล้ว", "success")
        return redirect(url_for("repair_detail", repair_id=repair_id))

    @app.post("/repair/<int:repair_id>/images")
    @login_required
    def upload_image(repair_id):
        accessible_repair(repair_id)
        image_type = request.form.get("image_type")
        allowed = {"teacher": {"before"}, "technician": {"before", "after"},
                   "admin": {"before", "after"}}
        if image_type not in allowed[current_user.role]:
            abort(403)
        filename = None
        try:
            image = request.files.get("image")
            if not image or not image.filename:
                raise ValueError("กรุณาเลือกไฟล์รูปภาพ")
            filename = save_image(image)
            db.session.add(RepairImage(repair_id=repair_id, image_type=image_type, image_path=filename))
            db.session.commit()
            flash("อัปโหลดรูปภาพสำเร็จ", "success")
        except (ValueError, SQLAlchemyError) as exc:
            db.session.rollback()
            if filename:
                (Path(app.config["UPLOAD_FOLDER"]) / filename).unlink(missing_ok=True)
            flash(str(exc) if isinstance(exc, ValueError) else "บันทึกภาพไม่ได้", "error")
        return redirect(url_for("repair_detail", repair_id=repair_id))

    @app.get("/images/<int:image_id>")
    @login_required
    def image_file(image_id):
        image = db.get_or_404(RepairImage, image_id)
        accessible_repair(image.repair_id)
        return send_from_directory(app.config["UPLOAD_FOLDER"], image.image_path)

    @app.get("/export/csv")
    @login_required
    def export_csv():
        def safe_cell(value):
            text = "" if value is None else str(value)
            return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text
        stream = StringIO(newline="")
        writer = csv.writer(stream)
        writer.writerow(["เลขใบแจ้งซ่อม", "อาคาร", "ห้อง", "ปัญหา", "สถานะ", "ค่าใช้จ่าย", "รายละเอียด"])
        for r in db.session.scalars(filtered_repairs()):
            writer.writerow([safe_cell(value) for value in
                             (r.request_no, r.building, r.room, PROBLEM_TYPES[r.problem_type],
                              STATUSES[r.status], r.cost, r.description)])
        return Response("\ufeff" + stream.getvalue(), content_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": "attachment; filename=repairs.csv"})

    @app.get("/repair/<int:repair_id>/print")
    @login_required
    def print_repair(repair_id):
        return render_template("print_repair.html", repair=accessible_repair(repair_id))

    @app.get("/repair/<int:repair_id>/pdf")
    @login_required
    def export_pdf(repair_id):
        repair = accessible_repair(repair_id)
        try:
            from weasyprint import HTML
        except (ImportError, OSError):
            flash("ยังไม่ได้ติดตั้ง WeasyPrint/Pango ใช้ปุ่มพิมพ์และ Save as PDF ได้", "info")
            return redirect(url_for("print_repair", repair_id=repair_id))
        html = render_template("print_repair.html", repair=repair, pdf=True)
        # Template ไม่มี external assets จึงไม่ต้อง fetch URL จากข้อมูลผู้ใช้
        return Response(HTML(string=html).write_pdf(), mimetype="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={repair.request_no}.pdf"})

    @app.route("/admin/users", methods=["GET", "POST"])
    @login_required
    @roles_required("admin")
    def manage_users():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            fullname = request.form.get("fullname", "").strip()
            password = request.form.get("password", "")
            role = request.form.get("role", "")
            if (not username or not fullname or len(username) > 80 or len(fullname) > 120
                    or len(password) < 8 or role not in ("admin", "teacher", "technician")):
                flash("กรอกข้อมูลให้ครบ รหัสผ่านอย่างน้อย 8 ตัวอักษร และเลือกบทบาทให้ถูกต้อง", "error")
            elif db.session.scalar(select(User).where(User.username == username)):
                flash("ชื่อผู้ใช้นี้มีอยู่แล้ว", "error")
            else:
                user = User(username=username, fullname=fullname, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("เพิ่มผู้ใช้สำเร็จ", "success")
            return redirect(url_for("manage_users"))
        return render_template("users.html", users=db.session.scalars(select(User)).all())

    @app.errorhandler(413)
    def too_large(_):
        return render_template("error.html", message="ขนาดข้อมูลอัปโหลดรวมต้องไม่เกิน 5 MB"), 413

    @app.errorhandler(403)
    @app.errorhandler(404)
    def access_error(error):
        message = "คุณไม่มีสิทธิ์ทำรายการนี้" if error.code == 403 else "ไม่พบข้อมูลที่คุณเข้าถึงได้"
        return render_template("error.html", message=message), error.code

    return app


if __name__ == "__main__":
    create_app().run()
