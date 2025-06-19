from flask import render_template, request, jsonify, redirect, url_for, flash
from . import auth
from ..models import User,Department,Role,db
from ..form import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import ImmutableMultiDict


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(account=form.account.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('帳號或密碼錯誤')
    return render_template("auth/r-login.html", form=form)

'''
@auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()  # 創建表單實例

# 只在需要時設置部門選項
    if request.method == 'GET' or form.role.data == 'agency':
        
        # 查詢所有的 section_name 並去除重複內容
        sections = db.session.query(Department.section_name).distinct().all()

        # 動態設置 section_name 的選項
        form.section_name.choices = [(section.section_name, section.section_name) for section in sections]


    # 如果是 POST 請求且是管理者角色
    if request.method == 'POST' and form.role.data == 'agency':
        # 設置副部門選項
        subsections = Department.query.filter_by(section_name=form.section_name.data).all()
        form.subsection_name.choices = [(sub.subsection_name, sub.subsection_name) 
                                      for sub in subsections if sub.subsection_name]


    print("Method:", request.method)  

    if request.method == 'POST':
        # 如果是一般用戶，移除部門欄位的驗證
        if form.role.data == 'user':
            form.section_name.data = None
            form.subsection_name.data = None
            # 清除驗證器
            form.section_name.validators = []
            form.subsection_name.validators = []

        print("表單資料:", request.form)
        print("是否有效?", form.validate())
        print("錯誤:", form.errors)


    if form.validate_on_submit():
        

        # 查找對應的角色
        role = Role.query.filter_by(name=form.role.data).first()
        if not role:
            flash('無效的角色類型', 'danger')
            return render_template("r-register.html", form=form)


       # 如果是管理者，查找對應的部門 ID
        department_id = None
        if form.role.data == 'agency':
           department = Department.query.filter_by(
               section_name=form.section_name.data,
               subsection_name=form.subsection_name.data
           ).first()
           if department:
               department_id = department.department_id
           else:
               flash('找不到指定的部門', 'danger')
               return render_template("r-register.html", form=form)
       



        user = User(
            full_name=form.full_name.data,
            id_card=form.id_card.data,
            employee_number=form.employee_number.data,
            account=form.account.data,
            password=form.password.data,
            email=form.email.data,
            phone=form.phone.data,
            sex=form.gender.data,
            role_id=role.role_id,  # 直接使用 role_id
            department_id=department_id  # 使用查找到的部門 ID
        )
       
        try:
            db.session.add(user)
            db.session.commit()
            return jsonify({
                'status': 'success',
                'title': '成功！',
                'message': '註冊成功！',
                'redirect_url': url_for('auth.login')
            })
            
        except IntegrityError:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'title': '註冊失敗',
                'message': '帳號、身分證號或電子郵件已被使用',
                'redirect_url': url_for('auth.register')
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'title': '註冊失敗',
                'message': '未知錯誤',
                'redirect_url': url_for('auth.register')
            })

    return render_template("r-register.html", form=form)
'''
@auth.route("/register", methods=["GET", "POST"])
def register():
  
    form = RegistrationForm()
  
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        role_type = data.get('role')
  


        # 設置表單數據
        for field in form:
            if field.name in data:
                field.data = data[field.name]


        # 如果是普通用戶，重置部門相關字段
        if role_type == 'user':
            form.section_name.choices = [('', '')]
            form.subsection_name.choices = [('', '')]
            # 使用空字符串而不是 None
            form.section_name.data = ''
            form.subsection_name.data = ''
        else:
            # 管理員角色，設置部門選項
            sections = db.session.query(Department.section_name).distinct().all()
            form.section_name.choices = [('', '請選擇部門')] + [(section[0], section[0]) for section in sections]
            
            if form.section_name.data:
                subsections = Department.query.filter_by(section_name=form.section_name.data).all()
                form.subsection_name.choices = [('', '請選擇子部門')] + [
                    (sub.subsection_name, sub.subsection_name) 
                    for sub in subsections 
                    if sub.subsection_name
                ]
            else:
                form.subsection_name.choices = [('', '請選擇子部門')]

        print("表單資料:", request.form)
        print("是否有效?", form.validate())
        print("錯誤:", form.errors)

        if form.validate():
            role = Role.query.filter_by(name=form.role.data).first()
            if not role:
                return jsonify({
                    'status': 'error',
                    'title': '錯誤',
                    'message': '無效的角色類型'
                })

            department_id = None
            if role_type == 'agency':
                department = Department.query.filter_by(
                    section_name=form.section_name.data,
                    subsection_name=form.subsection_name.data
                ).first()
                if department:
                    department_id = department.department_id

            user = User(
                full_name=form.full_name.data,
                id_card=form.id_card.data,
                employee_number=form.employee_number.data,
                account=form.account.data,
                password=form.password.data,
                email=form.email.data,
                phone=form.phone.data,
                sex=form.gender.data,
                role_id=role.role_id,
                department_id=department_id
            )

            try:
                db.session.add(user)
                db.session.commit()
                return jsonify({
                    'status': 'success',
                    'title': '成功！',
                    'message': '註冊成功！',
                    'redirect_url': '/login'
                })
            except IntegrityError:
                db.session.rollback()
                return jsonify({
                    'status': 'error',
                    'title': '註冊失敗',
                    'message': '帳號、身分證號或電子郵件已被使用'
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    'status': 'error',
                    'title': '註冊失敗',
                    'message': str(e)
                })
        else:
            return jsonify({
                'status': 'error',
                'title': '驗證失敗',
                'message': '請檢查輸入資料是否正確，帳號、身分證號或電子郵件已被使用'
            })

    # GET請求處理
    sections = db.session.query(Department.section_name).distinct().all()
    form.section_name.choices = [('', '請選擇部門')] + [(section[0], section[0]) for section in sections]
    form.subsection_name.choices = [('', '請選擇子部門')]
    return render_template("auth/r-register.html", form=form)



@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已經登出')
    return redirect(url_for('main.index'))
















    



@auth.route('/subsections/<section_name>', methods=['GET'])
def subsections(section_name):
    # 根據 section_name 查詢對應的 subsection_name 列表
    subsections = Department.query.filter_by(section_name=section_name).all()
    
    print(f"Received section_name: {section_name}")





 









    # 根據 section_name 查詢對應的 subsection_name 列表
    subsections = Department.query.filter_by(section_name=section_name).all()
    
    # 確保有查詢到結果
    if not subsections:
        return jsonify([])  # 如果沒有結果，返回空列表


    # 返回 subsection_name 選項的列表
    subsection_list = [(sub.subsection_name, sub.subsection_name) for sub in subsections if sub.subsection_name]

    print(f"Subsections: {subsection_list}")  # 測試用，打印返回的 subsection 資料

    return jsonify(subsection_list)






