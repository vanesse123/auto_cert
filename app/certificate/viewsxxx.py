from flask_login import login_required, current_user
from ..models import db, Course, Application, Certification, User,Department
from . import certificate
from flask_wtf import FlaskForm
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file
from datetime import datetime, timezone
from functools import wraps
from . import certificate
from flask_wtf.csrf import CSRFError
import os
import subprocess
import io
import sys

@certificate.route('/certificates/manage')
@login_required
def manage_certificates():
    form = FlaskForm()
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    issue_start = request.args.get('issue_start')
    issue_end = request.args.get('issue_end')
    search_type = request.args.get('search_type')
    
    # 基礎查詢
    query = db.session.query(
        Application, Course, User
    ).join(
        Course, Application.course_number == Course.course_number
    ).join(
        User, Application.employee_number == User.employee_number
    ).filter(
        Application.sign_in_state == True,  # 確認有簽到
        Course.department_id == current_user.department_id
    ).outerjoin(  # 左連接證書表來確認是否已發證
        Certification,
        db.and_(
            Certification.employee_number == Application.employee_number,
            Certification.course_number == Application.course_number
        )
    )
    
    # 根據搜尋類型應用過濾條件
    if search_type == 'keyword' and search:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{search}%'),
                Course.title.ilike(f'%{search}%'),
                User.employee_number.ilike(f'%{search}%')
            )
        )
    elif search_type == 'date' and issue_start and issue_end:
        query = query.filter(
            Certification.issue_date.between(issue_start, issue_end)
        )
    
    # 分頁
    pagination = query.paginate(page=page, per_page=10)
    
    return render_template('/certificate/manage.html',
                          entries=pagination.items,
                          pagination=pagination,
                          search=search,
                          form=form,
                          issue_start=issue_start,
                          issue_end=issue_end)

@certificate.route('/certificates/issue', methods=['POST'])
@login_required
def issue_certificates():
    form = FlaskForm()
   
       
    if request.is_json:
        data = request.get_json()
        selected_ids = data.get('selected_ids', [])
    else:
        selected_ids = request.form.getlist('selected_ids[]')
    
    try:
        for id_string in selected_ids:
            employee_number, course_number = id_string.split('-')
            
            # 檢查是否已有證書
            existing_cert = Certification.query.filter_by(
                employee_number=employee_number,
                course_number=course_number
            ).first()
            
            if existing_cert:
                continue
                
            # 檢查是否有簽到
            application = Application.query.filter_by(
                employee_number=employee_number,
                course_number=course_number,
                sign_in_state=True
            ).first()
            
            if not application:
                continue
            
            # 生成證書編號
            cert_code = f"CERT-{course_number}-{employee_number}-{datetime.now().strftime('%Y%m')}"
            
            # 建立新證書
            new_cert = Certification(
                certification_code=cert_code,
                employee_number=employee_number,
                course_number=course_number,
                issue_date=datetime.now().date()
            )
            
            db.session.add(new_cert)
        
        db.session.commit()
        if request.is_json:
            return ({'status': 'success'})
        flash('證書核發成功', 'success')
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return ({'status': 'error', 'message': str(e)}), 500
        flash('核發證書時發生錯誤', 'error')
    
    return redirect(url_for('certificate.manage_certificates'))

@certificate.route('/certificates/view/<int:cert_id>')
@login_required
def view_certificate(cert_id):
    cert = Certification.query.get_or_404(cert_id)
    
    # 檢查權限
    if cert.course.department_id != current_user.department_id:
        flash('您沒有權限查看此證書', 'error')
        return redirect(url_for('certificates.manage_certificates'))
        
    # 在這裡實現證書查看的邏輯
    return render_template('certificate/mycertificate.html', cert=cert)




@certificate.route('/certificates/mycertificate')  
@login_required
def mycertificate():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COURSES_PER_PAGE', 10)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'issue_date')
    order = request.args.get('order', 'desc')
    department_id = request.args.get('department_id', type=int)  # 改用 department_id
    search_type = request.args.get('search_type')

    # 獲取所有開課單位
    departments = Department.query.order_by(
        Department.section_name, 
        Department.subsection_name
    ).all()

    # 日期區間搜尋參數
    issue_date = request.args.get('issue_date')
    
    now = datetime.now(timezone.utc).date()
    
    # 基礎查詢
    query = Certification.query.join(Course).join(Department)\
        .filter(Certification.employee_number == current_user.employee_number)
        

    # 開課單位篩選
    if department_id:
        query = query.filter(Course.department_id == department_id)

    # 搜尋條件
    if search_type == 'keyword' and search:
        query = query.filter(Course.title.ilike(f'%{search}%'))
    elif search_type == 'certificate' and issue_date :
        query = query.filter(
            Certification.issue_date == issue_date,
        )
    
    # 排序選項
    sort_options = {
        'course_number': Course.course_number,
        'title': Course.title,
        'hours': Course.hours,
        'issue_date': Certification.issue_date
    }
    
    sort_column = sort_options.get(sort_by, Certification.issue_date)
    if order == 'desc':
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'certificate/mycertificate.html',
        certification=pagination.items,
        pagination=pagination,
        departments=departments,  # 傳遞所有開課單位
        department_id=department_id,  
        search=search,
        sort_by=sort_by,
        order=order,
        issue_date=issue_date,
        search_type=search_type,
    )

@certificate.route('/download/<course_number>')
@login_required
def download_pdf(course_number):
    course = Course.query.filter_by(course_number=course_number).first()
    department = Department.query.filter_by(department_id=course.department_id).first()

    if not course or not department:
        abort(404, description="Course or Department not found")

    # 定义外部python文件的路径
    script_path = os.path.join(os.path.dirname(__file__), 'Certificate_pdf.py')  
    cert_path = os.path.join(".", "app", "static", "cert", f'certificate_{course_number}.pdf')

    
    # 将数据序列化为 JSON 格式，传递给外部脚本
    course_start_year = course.course_start.strftime('%Y') if course.course_start else None
    course_start_month = course.course_start.strftime('%m') if course.course_start else None
    course_start_day = course.course_start.strftime('%d') if course.course_start else None

    data = {
        'name': current_user.full_name, 
        'course_title': course.title,
        'department_name': department.section_name,
        'hour': course.hours,
        'year': course_start_year,
        'month': course_start_month,
        'day': course_start_day,
    }
    
    python_path = sys.executable
    # 构建命令行
    command = [
    python_path,  # Python 執行檔路徑
    script_path,  # 外部腳本的路徑
    data['name'],  # 使用者名稱
    data['course_title'],  # 課程名稱
    data['department_name'],  # 部門名稱
    str(data['hour']),  # 課程時數
    data['year'],  # 年
    data['month'],  # 月
    data['day'],  # 日
    cert_path  # 證書存儲路徑
    ]
    
    # 使用外部Python生成PDF
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print("Error in PDF generation:", e.stderr)
        else:
            print("Error in PDF generation, but no stderr output:", e)  # 输出错误


    # 读取PDF文件并返回给用户
    return_data = io.BytesIO()
    with open(cert_path, 'rb') as fo:
        return_data.write(fo.read())
    return_data.seek(0)

    # 删除生成的PDF文件
    #os.remove(cert_path)

    # 发送文件给用户
    return send_file(return_data, as_attachment=True, mimetype='application/pdf',
                     download_name=f'證書_{course_number}.pdf')