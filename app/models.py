from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func
from typing import Optional, List
from sqlalchemy import (
    Integer,
    Boolean,
    String,
    CHAR,
    Date,
    DateTime,
    Enum,
    Unicode,
    UnicodeText,
    ForeignKey,
)
from sqlalchemy.dialects.mysql import TINYINT
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from .extensions import login_manager
from flask import current_app
import pytz

db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    users = relationship("User", back_populates="role")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    employee_number: Mapped[str] = mapped_column(String(16), primary_key=True)
    account: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str] = mapped_column(Unicode(50), nullable=False)
    id_card: Mapped[str] = mapped_column(CHAR(10), nullable=False, unique=True)
    sex: Mapped[str] = mapped_column(Enum('男', '女',encoding='utf8mb4'), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(CHAR(10), nullable=False, unique=True)
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.role_id"))
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id"), nullable=True
    )

    applications = relationship("Application", back_populates="user")
    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    certifications = relationship("Certification", back_populates="user")

    # 密碼保護
    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

#login
    def get_id(self):
        # 這裡仍然返回 employee_number，因為這是主鍵
        return str(self.employee_number)
    
    @classmethod
    def get_by_account(cls, account):
        return cls.query.filter_by(account=account).first()

    @login_manager.user_loader
    def load_user(employee_number):
        return User.query.get(str(employee_number))

class Course(db.Model):
    __tablename__ = "courses"

    course_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(Unicode(50), nullable=True)
    max_attendance: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    signup_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signup_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    course_start: Mapped[Date] = mapped_column(Date, nullable=False)
    course_end: Mapped[Date] = mapped_column(Date, nullable=False)
    hours: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    location: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    title: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    intro: Mapped[str] = mapped_column(UnicodeText)
    description: Mapped[str] = mapped_column(UnicodeText)
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.department_id")
    )

    applications = relationship("Application", back_populates="course")
    department = relationship("Department", back_populates="courses")
    certifications = relationship("Certification", back_populates="course")

    def __repr__(self):
        return f"<Course {self.title}>"

    @property
    def current_attendance(self):
        return Application.query.filter_by(course_number=self.course_number).count()

    @property
    def available_slots(self):
        return max(0, self.max_attendance - self.current_attendance)

    def can_enroll(self):
        # 確保 signup_start 和 signup_deadline 也是 timezone-aware
       
        
        now = datetime.now(timezone.utc)
        
        # 將台灣時區的 naive datetime 轉成 UTC
        signup_start = self.signup_start
        if signup_start.tzinfo is None:
            tw_tz = pytz.timezone('Asia/Taipei') # 台灣時區
            signup_start = signup_start.replace(tzinfo=tw_tz)
            signup_start = signup_start.astimezone(timezone.utc)

        signup_deadline = self.signup_deadline 
        if signup_deadline.tzinfo is None:
            tw_tz = pytz.timezone('Asia/Taipei')
            signup_deadline = signup_deadline.replace(tzinfo=tw_tz)
            signup_deadline = signup_deadline.astimezone(timezone.utc)

        return (
            self.current_attendance < self.max_attendance
            and signup_start <= now <= signup_deadline
        )
    
    def can_manage(self, user):
        """檢查用戶是否有管理此課程的權限"""
        # 檢查用戶是否已登入
        if not user.is_authenticated:
            return False
            
        # 檢查用戶角色是否為管理者
        if user.role.name != 'agency':
            return False
            
        # 檢查用戶是否為該部門的管理者
        return user.department_id == self.department_id

##utc
    def get_signup_start_utc(self):
        """獲取帶 UTC 時區的報名截止時間"""
        if self.signup_deadline.tzinfo is None:
            tw_tz = pytz.timezone('Asia/Taipei')
            return tw_tz.localize(self.signup_start).astimezone(pytz.UTC)
        return self.signup_start
    
    
    def get_signup_deadline_utc(self):
        """獲取帶 UTC 時區的報名截止時間"""
        if self.signup_deadline.tzinfo is None:
            tw_tz = pytz.timezone('Asia/Taipei')
            return tw_tz.localize(self.signup_deadline).astimezone(pytz.UTC)
        return self.signup_deadline
    
  
    def get_status(self, current_time=None):
        """獲取課程狀態"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        signup_start = self.get_signup_start_utc()
        signup_deadline = self.get_signup_deadline_utc()

        return {
            'is_upcoming': signup_start > current_time,
            'is_enrolling': signup_start <= current_time <= signup_deadline,
            'is_closed': signup_deadline < current_time,
            'is_in_progress': self.course_start <= current_time.date() <= self.course_end,
            'is_finished': self.course_end < current_time.date()
        }
    
    def is_upcoming(self, current_time=None):
        """檢查是否尚未開始報名"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        return self.get_signup_start_utc() > current_time
        
    def is_enrolling(self, current_time=None):
        """檢查是否在報名期間"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        return (self.get_signup_start_utc() <= current_time <= 
                self.get_signup_deadline_utc())
        
    def is_closed(self, current_time=None):
        """檢查是否已截止報名"""
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        return self.get_signup_deadline_utc() < current_time

    def update_course(self, form):
        """更新課程信息"""
        try:
            # 基本信息
            self.title = form.title.data
            self.max_attendance = form.max_attendance.data
            
            # 時間設定（確保時區正確）
            if form.signup_start.data and form.signup_start.data.tzinfo is None:
                self.signup_start = form.signup_start.data.replace(tzinfo=timezone.utc)
            else:
                self.signup_start = form.signup_start.data

            if form.signup_deadline.data and form.signup_deadline.data.tzinfo is None:
                self.signup_deadline = form.signup_deadline.data.replace(tzinfo=timezone.utc)
            else:
                self.signup_deadline = form.signup_deadline.data
            
            # 課程時間
            self.course_start = form.course_start.data
            self.course_end = form.course_end.data
            
            # 詳細信息
            self.hours = form.hours.data
            self.location = form.location.data
            self.intro = form.intro.data
            self.description = form.description.data
            
            # 更新時間
            self.update_at = datetime.now(timezone.utc)
            
            # 提交更改
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新課程時發生錯誤: {str(e)}")

            raise

    def delete_course(self):
        """刪除課程"""
        try:
            # 先刪除相關的報名記錄
            Application.query.filter_by(course_number=self.course_number).delete()
            # 再刪除課程
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"刪除課程時發生錯誤: {str(e)}")
            raise

class Application(db.Model):
    __tablename__ = "applications"

    application_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_number: Mapped[str] = mapped_column(
        String(16), ForeignKey("users.employee_number")
    )
    course_number: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.course_number")
    )
    sign_in_state: Mapped[bool] = mapped_column(Boolean, default=False)
    sign_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=True)
    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    user = relationship("User", back_populates="applications")
    course = relationship("Course", back_populates="applications")

    __table_args__ = (
        UniqueConstraint("employee_number", "course_number", name="unique_user_course"),
    )

    @classmethod
    def get_user_application(cls, employee_number, course_number):
        """獲取使用者的課程報名記錄"""
        return cls.query.filter_by(
            employee_number=employee_number,
            course_number=course_number
        ).first()
    
    def can_sign_in(self, current_date=None):
        """檢查是否可以簽到"""
        if current_date is None:
            current_date = datetime.now(timezone.utc)
            
        return (
            not self.sign_in_state and
            self.course.course_start <= current_date.date() <= self.course.course_end
        )




class Certification(db.Model):
    __tablename__ = "certifications"

    certification_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    certification_code: Mapped[str] = mapped_column(String(50),nullable=True)
    employee_number: Mapped[str] = mapped_column(
        String(16), ForeignKey("users.employee_number")
    )
    course_number: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.course_number")
    )
    issue_date: Mapped[Date] = mapped_column(
        Date, nullable=False, default=func.current_date()
    )
    hash_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    course = relationship("Course", back_populates="certifications")
    user = relationship("User", back_populates="certifications")


class Department(db.Model):
    __tablename__ = "departments"

    department_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    subsection_name: Mapped[Optional[str]] = mapped_column(Unicode(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(10), nullable=False)
    extension: Mapped[str] = mapped_column(String(4), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)

    courses = relationship("Course", back_populates="department")
    users = relationship("User", back_populates="department")

    __table_args__ = (
        UniqueConstraint(
            "section_name", "subsection_name", name="unique_section_subsection"
        ),
        UniqueConstraint("phone", "extension", name="unique_phone_extension"),
    )

    def __repr__(self):
        return f"<Department {self.full_name}>"

    @property
    def full_name(self) -> str:
        if self.subsection_name:
            return f"{self.section_name} - {self.subsection_name}"
        return self.section_name

    @classmethod
    def get_main_departments(cls) -> List[str]:
        return db.session.query(cls.section_name).distinct().all()

    @classmethod
    def get_sub_departments(cls, section_name: str) -> List["Department"]:
        return (
            cls.query.filter_by(section_name=section_name)
            .filter(cls.subsection_name != None)
            .all()
        )

    @classmethod
    def get_department_choices(cls) -> List[tuple]:
        departments = cls.query.order_by(cls.section_name, cls.subsection_name).all()
        return [(dept.department_id, dept.full_name) for dept in departments]




