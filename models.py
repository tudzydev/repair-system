"""โมเดล SQLAlchemy: โครงสร้างตารางและกฎการเปลี่ยนสถานะ."""
from datetime import date, datetime
from enum import Enum

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class RequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    fullname = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    __table_args__ = (db.CheckConstraint("role IN ('admin','teacher','technician')"),)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class RequestCounter(db.Model):
    """ตัวนับรายเดือน อัปเดตแบบ atomic เพื่อป้องกันเลขซ้ำ."""
    __tablename__ = "request_counters"
    month = db.Column(db.String(6), primary_key=True)
    sequence = db.Column(db.Integer, nullable=False)


class RepairRequest(db.Model):
    __tablename__ = "repair_requests"
    id = db.Column(db.Integer, primary_key=True)
    request_no = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    building = db.Column(db.String(100), nullable=False)
    room = db.Column(db.String(50), nullable=False)
    problem_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(10), default="medium", nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"))
    due_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    cost = db.Column(db.Numeric(12, 2))
    result = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    requester = db.relationship("User", foreign_keys=[user_id])
    technician = db.relationship("User", foreign_keys=[assigned_to])
    images = db.relationship("RepairImage", backref="repair", cascade="all, delete-orphan")
    comments = db.relationship("Comment", backref="repair", cascade="all, delete-orphan",
                               order_by="Comment.created_at")
    __table_args__ = (
        db.CheckConstraint("problem_type IN ('electrical','furniture','computer','aircon','other')"),
        db.CheckConstraint("urgency IN ('low','medium','high')"),
        db.CheckConstraint("status IN ('pending','accepted','in_progress','completed')"),
        db.CheckConstraint("cost IS NULL OR cost >= 0"),
    )

    def assign_to(self, technician, due_date):
        if self.status != RequestStatus.PENDING.value:
            raise ValueError("มอบหมายได้เฉพาะงานที่รอรับเรื่อง")
        if technician.role != "technician":
            raise ValueError("ผู้รับงานต้องเป็นเจ้าหน้าที่ซ่อม")
        if due_date < date.today():
            raise ValueError("วันกำหนดเสร็จต้องไม่อยู่ในอดีต")
        self.assigned_to = technician.id
        self.due_date = due_date
        self.status = RequestStatus.ACCEPTED.value

    def start_repair(self):
        if self.status != RequestStatus.ACCEPTED.value or self.assigned_to is None:
            raise ValueError("ต้องรับเรื่องและมอบหมายเจ้าหน้าที่ก่อนเริ่มซ่อม")
        self.status = RequestStatus.IN_PROGRESS.value

    def complete_repair(self, cost, result):
        if self.status != RequestStatus.IN_PROGRESS.value:
            raise ValueError("ต้องเริ่มดำเนินการก่อนบันทึกผลซ่อม")
        if not cost.is_finite() or cost < 0 or cost > 9999999999.99:
            raise ValueError("ค่าใช้จ่ายต้องเป็นตัวเลขตั้งแต่ 0 ถึง 9,999,999,999.99")
        if not result.strip():
            raise ValueError("กรุณาระบุผลการซ่อม")
        self.cost = cost
        self.result = result.strip()
        self.completion_date = date.today()
        self.status = RequestStatus.COMPLETED.value


class RepairImage(db.Model):
    __tablename__ = "repair_images"
    id = db.Column(db.Integer, primary_key=True)
    repair_id = db.Column(db.Integer, db.ForeignKey("repair_requests.id"), nullable=False)
    image_type = db.Column(db.String(10), nullable=False)
    image_path = db.Column(db.String(100), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    __table_args__ = (db.CheckConstraint("image_type IN ('before','after')"),)


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    repair_id = db.Column(db.Integer, db.ForeignKey("repair_requests.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    author = db.relationship("User")
