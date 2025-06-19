from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_file,jsonify
from flask_login import login_required, current_user
from ..models  import db, Course, Application, Certification, User, Department
from ..form import VerificationForm
from datetime import datetime,timezone
from sqlalchemy import func
import pytz
from typing import List, Dict, Any
from werkzeug.exceptions import HTTPException
from .  import certificate
from flask_wtf import FlaskForm
from wtforms import HiddenField
import os
import subprocess
import io
import sys


class CertificateForm(FlaskForm):
    """證書發放表單"""
    pass

class CertificateError(Exception):
    """證書管理相關的自定義異常"""
    pass

@certificate.route('/certificates')
@login_required
def index():
    """證書管理首頁 - 顯示所有可管理的課程"""
    try:
        courses = Course.query.filter(
            Course.department_id == current_user.department_id,
            Course.course_end < func.current_date()
        ).order_by(Course.course_end.desc()).all()

        course_stats = {}
        for course in courses:
            stats = get_course_statistics(course.course_number)
            course_stats[course.course_number] = stats

        return render_template(
            'certificate/index.html',
            courses=courses,
            course_stats=course_stats
        )
    except Exception as e:
        current_app.logger.error(f"Error in certificate index: {str(e)}")
        flash('載入課程列表時發生錯誤', 'error')
        return redirect(url_for('main.index'))

@certificate.route('/certificates/<int:course_number>')
@login_required
def manage_certificates(course_number: int):
    """證書管理頁面"""
    try:
        course = get_course_or_404(course_number)
        verify_course_management_permission(course)

        filters = {
            'sign_in': request.args.get('sign_in', 'all'),
            'cert_status': request.args.get('cert_status', 'all'),
            'search': request.args.get('search', '').strip()
        }

        students = get_filtered_students(course_number, filters)
        stats = get_course_statistics(course_number)
        form = CertificateForm()  # 創建表單實例

        return render_template(
            'certificate/manage.html',
            course=course,
            students=students,
            stats=stats,
            filters=filters,
            form=form
        )
    except HTTPException:
        raise
    except Exception as e:
        current_app.logger.error(f"Error in manage_certificates: {str(e)}")
        flash('載入證書管理頁面時發生錯誤', 'error')
        return redirect(url_for('certificate.index'))

@certificate.route('/certificates/issue', methods=['POST'])
@login_required
def issue_certificates():
    """批量發放證書"""
    try:

        # 記錄接收到的表單資料
        current_app.logger.info(f"Received form data: {request.form}")
        current_app.logger.info(f"Employee numbers: {request.form.getlist('employee_numbers')}")

        course_number = request.form.get('course_number', type=int)
        employee_numbers = request.form.getlist('employee_numbers')


       
        course = get_course_or_404(course_number)
        current_app.logger.info(f"Course found: {course.course_number}")
       

        verify_course_management_permission(course)
        current_app.logger.info("Permission verified")


        if not employee_numbers:
            flash('請選擇要發放證書的學員', 'warning')
            return redirect(url_for('certificate.manage_certificates', course_number=course_number))

        results = process_certificate_issuance(course_number, employee_numbers)
        current_app.logger.info(f"Certificate issuance results: {results}")
        
        if results['success']:
            flash(f"成功發放 {results['success']} 張證書", 'success')
        if results['failed']:
            flash(f"有 {results['failed']} 位學員無法發放證書", 'warning')

        return redirect(url_for('certificate.manage_certificates', course_number=course_number))

    except Exception as e:
        current_app.logger.error(f"Error in issue_certificates: {str(e)}")
        flash('發放證書時發生錯誤', 'error')
        return redirect(url_for('+', course_number=course_number))

def get_course_or_404(course_number: int) -> Course:
    """獲取課程或返回 404"""
    course = Course.query.get(course_number)
    if not course:
        abort(404, description="課程不存在")
    return course

def verify_course_management_permission(course: Course) -> None:
    """驗證課程管理權限"""
    if not course.can_manage(current_user):
        abort(403, description="您沒有權限管理此課程的證書")

def get_course_statistics(course_number: int) -> Dict[str, int]:
    """獲取課程統計資料"""
    total_students = Application.query.filter_by(course_number=course_number).count()
    signed_in = Application.query.filter_by(
        course_number=course_number,
        sign_in_state=True
    ).count()
    certified = Certification.query.filter_by(course_number=course_number).count()

    return {
        'total_students': total_students,
        'signed_in': signed_in,
        'certified': certified,
    }

def get_filtered_students(course_number: int, filters: Dict[str, str]) -> List[Dict[str, Any]]:
    """根據篩選條件獲取學員列表"""
    query = db.session.query(
        Application, User, Certification
    ).join(
        User, Application.employee_number == User.employee_number  # 明確指定關聯條件
    ).outerjoin(
        Certification,
        db.and_(
            Certification.employee_number == Application.employee_number,
            Certification.course_number == Application.course_number
        )
    ).filter(Application.course_number == course_number)

    # 套用篩選條件
    if filters['sign_in'] != 'all':
        query = query.filter(Application.sign_in_state == (filters['sign_in'] == 'complete'))
    
    if filters['cert_status'] != 'all':
        if filters['cert_status'] == 'issued':
            query = query.filter(Certification.certification_code.isnot(None))
        else:
            query = query.filter(Certification.certification_code.is_(None))
    
    if filters['search']:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f"%{filters['search']}%"),
                User.employee_number.ilike(f"%{filters['search']}%")
            )
        )
    
    students = query.all()
    return [format_student_data(app, user, cert) for app, user, cert in students]

def format_student_data(application: Application, user: User, certification: Certification) -> Dict[str, Any]:
    """格式化學員資料"""
    return {
        'employee_number': user.employee_number,
        'full_name': user.full_name,
        'department': user.department.full_name if user.department else None,
        'sign_in_state': application.sign_in_state,
        'sign_in_time': application.sign_in_time,
        'certification_code': certification.certification_code if certification else None,
        'issue_date': certification.issue_date if certification else None
    }

def process_certificate_issuance(course_number: int, employee_numbers: List[str]) -> Dict[str, int]:
    """處理證書發放"""
    results = {'success': 0, 'failed': 0}
    
    try:
        for emp_number in employee_numbers:
            try:
                if issue_single_certificate(course_number, emp_number):
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except CertificateError:
                results['failed'] += 1
                continue
        
        db.session.commit()
        return results
    
    except Exception:
        db.session.rollback()
        raise

#發放單張證書
def issue_single_certificate(course_number: int, employee_number: str) -> bool:
    try:
        # 檢查簽到狀態
        application = Application.query.filter_by(
            course_number=course_number,
            employee_number=employee_number
        ).first()
        current_app.logger.info(f"Application found: {application}, Sign-in state: {application.sign_in_state if application else None}")

        if not application or not application.sign_in_state:
            raise CertificateError(f"學員 {employee_number} 未完成簽到")

        # 檢查現有證書
        existing_cert = Certification.query.filter_by(
            course_number=course_number,
            employee_number=employee_number
        ).first()
        current_app.logger.info(f"Existing certificate: {existing_cert}")

        if existing_cert:
            raise CertificateError(f"學員 {employee_number} 已有證書")

        # 建立新證書
        new_cert = Certification(
            certification_code=f"CERT-{course_number}-{employee_number}-{datetime.now(pytz.UTC).strftime('%Y%m%d')}",
            employee_number=employee_number,
            course_number=course_number,
            issue_date=datetime.now(pytz.UTC).date()
        )
        current_app.logger.info(f"New certificate created: {new_cert.certification_code}")
        
        db.session.add(new_cert)
        return True
        
    except CertificateError as e:
        current_app.logger.warning(str(e))
        raise
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        raise


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

    certificate = Certification.query.filter_by(course_number=course_number).first()
    course = Course.query.filter_by(course_number=certificate.course_number).first()
    department = Department.query.filter_by(department_id=course.department_id).first()
    
    if not course or not department or not certificate:
        abort(404, description="Course or Department or Certificate not found")

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
        'certification_code':certificate.certification_code
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
    data['certification_code'], #證號
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
    os.remove(cert_path)

    # 发送文件给用户
    return send_file(return_data, as_attachment=True, mimetype='application/pdf',
                     download_name=f'證書_{course_number}.pdf')



#證書驗證
@certificate.route('/certificates/verify', methods=['GET','POST'])
def verification():
    form = VerificationForm()
    if request.method=='POST':
        cert_code=request.form.get('cert_code')
        try:
            certificate = Certification.query.filter_by(certification_code=cert_code).first()
            if certificate:
                user=User.query.get(certificate.employee_number)
                course=Course.query.get(certificate.course_number)
                department = Department.query.get(course.department_id)
               
                return jsonify({
                'status': 'success',
                'data': {
                    'owner': user.full_name+'('+ user.employee_number +')',                    
                    'course_name': course.title,                
                    'issue_date': certificate.issue_date.strftime('%Y-%m-%d'),
                    'issuer': department.section_name +'-'+ department.subsection_name,  }
                })
              
            else:
                return jsonify({
                    'status': 'error',
                    'message': '驗證失敗'
                }) 
        
        except Exception as e:
                flash(f'資料庫匹配發生錯誤:{str(e)}', 'error')
                #紀錄證書取得錯誤
                current_app.logger.error(f'Certificate match error: {str(e)}')
    
    
    return render_template('certificate/verify.html',form=form) 



@certificate.errorhandler(Exception)
def handle_error(error):
    """全局錯誤處理"""
    if isinstance(error, HTTPException):
        return render_template('errors/error.html', error=error), error.code
    
    current_app.logger.error(f"Unhandled error: {str(error)}")
    return render_template('errors/500.html'), 500