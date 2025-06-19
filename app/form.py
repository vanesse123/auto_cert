from flask_wtf import FlaskForm
from .models import Department,User
from app import db
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    BooleanField,
    SubmitField,
    RadioField,
    TextAreaField,
    DateTimeField,
    DateField,
    IntegerField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    Regexp,
    ValidationError,
    EqualTo,
    Optional,
    NumberRange
)
import re
from datetime import datetime, timezone


class LoginForm(FlaskForm):

    account = StringField(
        "帳號",
        validators=[
            DataRequired(message="請輸入帳號"),
            Length(3,30),
        ],
    )

    password = PasswordField(
        "密碼",
        validators=[
            DataRequired(message="請輸入密碼"),
        ],
    )

    remember_me = BooleanField("記住我")
    submit = SubmitField("登入")


class ChineseNameValidator:
    def __call__(self, form, field):
        if not re.match(r"^[\u4e00-\u9fa5]{2,50}$", field.data):
            raise ValidationError("請輸入有效的中文姓名")


class PasswordAdditionalValidator:
    def __call__(self, form, field):
        password = field.data

        if not re.search(r"[A-Za-z]", password):
            raise ValidationError("密碼必須包含至少一個字母")
        if not re.search(r"\d", password):
            raise ValidationError("密碼必須包含至少一個數字")
        if password[0].isdigit():
            raise ValidationError("密碼不能以數字開頭")


class RegistrationForm(FlaskForm):

    role = RadioField(
        '角色',
        choices=[('user', '教師'), ('agency', '管理者')],
        validators=[DataRequired()],
        default='user'  # 設置默認值為教師
    )

    employee_number = StringField(
        "職號",
        validators=[
            DataRequired(message="請輸入職號"),
            Length(min=1, max=16),
            Regexp(r"^[a-zA-Z0-9]{1,16}$", message="職號只能包含字母和數字"),
        ],
    )

    account = StringField(
        "帳號",
        validators=[
            DataRequired(message="請輸入帳號"),
            Length(min=5, max=30, message="帳號長度必須在5到30個字符之間"),
            Regexp(r"^[a-zA-Z\d_-]{5,30}$", message="帳號只能包含字母、數字、_、-"),
        ],
    )

    password = PasswordField(
        "密碼",
        validators=[
            DataRequired(message="請輸入密碼"),
            Length(min=8, max=20, message="密碼長度必須在8到20個字符之間"),
            Regexp(
                r"^[A-Za-z][A-Za-z\d@$!%*#?&]*$",
                message="密碼必須以字母開頭，只能包含字母、數字和特殊字符（@$!%*#?&）",
            ),
            PasswordAdditionalValidator(),
        ],
    )

    password2 = PasswordField(
        "確認密碼",
        validators=[
            DataRequired(message="請再次輸入密碼"),
            EqualTo("password", message="密碼需一致"),
        ],
    )

    full_name = StringField(
        "全名",
        validators=[
            DataRequired(message="請輸入姓名"),
            Length(max=50, message="全名最多50個字"),
            Regexp(r"^[\u4e00-\u9fa5]{2,50}$", message="請輸入有效中文名"),
        ],
    )

    id_card = StringField(
        "身份證號碼",
        validators=[
            DataRequired(message="請輸入身分證"),
            Regexp(r"^[A-Z][12]\d{8}$", message="身份證號碼格式不正確"),
        ],
    )

    gender = RadioField(
        "性別",
        choices=[("男", "男"), ("女", "女")],
        validators=[DataRequired(message="請選擇性別")],
    )

    email = StringField(
        "電子郵件",
        validators=[
            DataRequired(message="請輸入電子郵件"),
            Email(message="請輸入有效的電子郵件地址"),
            Length(max=100),
        ],
    )

    phone = StringField(
        "電話號碼",
        validators=[
            DataRequired(message="請輸入電話號碼"),
            Regexp(r"^09\d{8}$", message="電話號碼必須為10位數字，並以09開頭"),
        ],
    )

    # 修改部門字段的定義，設置默認選項
    section_name = SelectField("主部門", choices=[('', '')], validators=[Optional()])
    subsection_name = SelectField("副部門", choices=[('', '')], validators=[Optional()])
    

    def validate_employee_number(self, field):
        if User.query.filter_by(employee_number=field.data).first():
            raise ValidationError('職號已被使用')
        
    def validate_account(self, field):
        if User.query.filter_by(account=field.data).first():
            raise ValidationError('帳號已被註冊')
        
    def validate_phone(self, field):
        if User.query.filter_by(phone=field.data).first():
            raise ValidationError('號碼已被使用')

    def validate_id_card(self, field):
        if User.query.filter_by(id_card=field.data).first():
            raise ValidationError('身分證已被使用')



    # 修改 validate 方法定義，添加 extra_validators 參數
    def validate(self, extra_validators=None):
        # 檢查基本驗證是否通過
        if not super(RegistrationForm, self).validate():
            return False
        
        # 獲取角色值
        role_type = self.role.data
        
        # 如果是普通用戶，跳過部門驗證
        if role_type == 'user':
            # 清除可能的錯誤
            if 'section_name' in self.errors:
                del self.errors['section_name']
            if 'subsection_name' in self.errors:
                del self.subsection_name.errors
            return True
            
        # 如果是管理者，執行部門驗證
        if role_type == 'agency':
            if not self.section_name.data:
                self.section_name.errors.append('請選擇主部門')
                return False
            
            valid_subsections = db.session.query(Department.subsection_name).\
                filter_by(section_name=self.section_name.data).all()
            valid_subsections = [sub[0] for sub in valid_subsections]
            
            if not self.subsection_name.data or self.subsection_name.data not in valid_subsections:
                self.subsection_name.errors.append('請選擇副部門')
                return False
        
        return True
    
    submit = SubmitField("註冊")





class CourseForm(FlaskForm):
 
    max_attendance = IntegerField(
        '最大人數',
        validators=[
            DataRequired(message='請輸入最大人數'),
            NumberRange(min=1, max=255, message='人數必須在 1-255 之間')
        ]
    )
    
    signup_start = DateTimeField(
        '報名開始時間',
        validators=[DataRequired(message='請輸入報名開始時間')],
        format='%Y-%m-%dT%H:%M' 
    )
    signup_deadline = DateTimeField(
        '報名截止時間',
        validators=[DataRequired(message='請輸入報名截止時間')],
        format='%Y-%m-%dT%H:%M'  
    )
    
    course_start = DateField(
        '課程開始日期',
        validators=[DataRequired(message='請輸入課程開始日期')],
        format='%Y-%m-%d'
    )
    
    course_end = DateField(
        '課程結束日期',
        validators=[DataRequired(message='請輸入課程結束日期')],
        format='%Y-%m-%d'
    )
    
    hours = IntegerField(
        '課程時數',
        validators=[
            DataRequired(message='請輸入課程時數'),
            NumberRange(min=1, max=255, message='時數必須在 1-255 之間')
        ]
    )
    
    location = StringField(
        '上課地點',
        validators=[
            DataRequired(message='請輸入上課地點'),
            Length(max=100, message='地點不可超過 100 字')
        ]
    )
    
    title = StringField(
        '課程標題',
        validators=[
            DataRequired(message='請輸入課程標題'),
            Length(max=100, message='標題不可超過 100 字')
        ]
    )
    
    intro = TextAreaField(
        '課程簡介',
        validators=[DataRequired(message='請輸入課程簡介')]
    )
    
    description = TextAreaField(
        '課程描述',
        validators=[DataRequired(message='請輸入課程描述')]
    )

    submit = SubmitField("提交")
    
    def validate_signup_deadline(self, field):
        if field.data <= self.signup_start.data:
            raise ValidationError('報名截止時間必須晚於報名開始時間')
    
    def validate_course_end(self, field):
        if field.data < self.course_start.data:
            raise ValidationError('課程結束日期必須晚於或等於開始日期')
    
    def validate_signup_start(self, field):
        if field.data < datetime.now(timezone.utc):
            raise ValidationError('報名開始時間不能早於現在')
        
    def validate_signup_deadline(self, field):
        if not field.data or not self.signup_start.data:
            return
        
        # 確保兩個時間都有時區信息
        start_time = self.signup_start.data
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
            
        end_time = field.data
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
            
        if end_time <= start_time:
            raise ValidationError('報名截止時間必須晚於報名開始時間')
    
    def validate_signup_start(self, field):
        if not field.data:
            return
            
        # 確保有時區信息
        start_time = field.data
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        if start_time < now:
            raise ValidationError('報名開始時間不能早於現在')
            
    def validate_course_end(self, field):
        if not field.data or not self.course_start.data:
            return
            
        if field.data < self.course_start.data:
            raise ValidationError('課程結束日期必須晚於或等於開始日期')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
            
        # 在這裡為所有時間欄位添加時區信息
        if self.signup_start.data:
            if self.signup_start.data.tzinfo is None:
                self.signup_start.data = self.signup_start.data.replace(tzinfo=timezone.utc)
                
        if self.signup_deadline.data:
            if self.signup_deadline.data.tzinfo is None:
                self.signup_deadline.data = self.signup_deadline.data.replace(tzinfo=timezone.utc)
                
        return True
    
class VerificationForm(FlaskForm):
    cert_code = StringField('證書編號', validators=[DataRequired()])
