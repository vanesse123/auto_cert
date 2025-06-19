from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone
from functools import wraps
from ..models import Application,Course,Department,User,db
from ..form import CourseForm
from . import courses
from flask_wtf.csrf import CSRFError
import pytz

def agency_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.name != 'agency':
            flash('您沒有權限執行此操作', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


'''
@courses.route('/')
def course_list():
    """課程列表頁面"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COURSES_PER_PAGE', 10)


    now = datetime.now(timezone.utc)
    
 
    query = Course.query.order_by(Course.signup_deadline.asc())
    
    pagination = query.paginate(page=page, per_page=per_page)
    courses = pagination.items
    
    return render_template(
        'courses/list2.html',
        courses=courses,
        pagination=pagination
    )

'''

@courses.route('/')
def course_list():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COURSES_PER_PAGE', 10)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'course_start')
    order = request.args.get('order', 'desc')
    department_id = request.args.get('department_id', type=int)  
    search_type = request.args.get('search_type')
    show_history = request.args.get('show_history', '0') == '1'
    
    # 獲取日期範圍參數
    course_start = request.args.get('course_start')
    course_end = request.args.get('course_end')
    
    now = datetime.now(timezone.utc).date()
    
    # 初始化基本查詢
    query = Course.query.join(Department)

    # 根據歷史/當前課程進行過濾
    if show_history:
        query = query.filter(Course.course_end < now)
        query = query.order_by(Course.course_end.desc())
    else:
        query = query.filter(Course.course_end >= now)

    # 開課單位過濾
    if department_id:
        query = query.filter(Course.department_id == department_id)

    # 搜尋條件
    if search and search_type == 'keyword':
        query = query.filter(Course.title.ilike(f'%{search}%'))
    elif search_type == 'course' and course_start and course_end:
        query = query.filter(
            Course.course_start >= course_start,
            Course.course_end <= course_end
        )
    elif search:  # 跨多個欄位的一般搜尋
        query = query.filter(
            db.or_(
                Course.title.ilike(f'%{search}%'),
                Department.section_name.ilike(f'%{search}%'),
                Department.subsection_name.ilike(f'%{search}%')
            )
        )
    
    # 獲取所有開課單位供下拉選單使用
    departments = Department.query.order_by(
        Department.section_name, 
        Department.subsection_name
    ).all()
    
    # 排序
    sort_options = {
        'course_number': Course.course_number,
        'title': Course.title,
        'course_start': Course.course_start,
        'create_at': Course.create_at
    }
    
    sort_column = sort_options.get(sort_by, Course.course_start)
    if order == 'desc':
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)
    
    # 分頁
    pagination = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'courses/list2.html',
        courses=pagination.items,
        pagination=pagination,
        departments=departments,
        department_id=department_id,
        search=search,
        sort_by=sort_by,
        order=order,
        course_start=course_start,
        course_end=course_end,
        search_type=search_type,
        show_history=show_history
    )



@courses.route('/manage')
@login_required
@agency_required
def manage_courses():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COURSES_PER_PAGE', 10)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'create_at')
    order = request.args.get('order', 'desc')
    
    # 日期區間搜尋參數
    signup_start = request.args.get('signup_start')
    signup_end = request.args.get('signup_end')
    course_start = request.args.get('course_start')
    course_end = request.args.get('course_end')
    search_type = request.args.get('search_type')
    
    query = Course.query.join(Department).filter(
        Course.department_id == current_user.department_id
    )
    
    # 根據搜尋類型應用過濾條件
    if search_type == 'keyword' and search:
        query = query.filter(
            db.or_(
                Course.title.ilike(f'%{search}%'),
                Department.section_name.ilike(f'%{search}%'),
                Department.subsection_name.ilike(f'%{search}%')
            )
        )
    elif search_type == 'signup' and signup_start and signup_end:
        query = query.filter(
            Course.signup_start >= signup_start,
            Course.signup_deadline <= signup_end
        )
    elif search_type == 'course' and course_start and course_end:
        query = query.filter(
            Course.course_start >= course_start,
            Course.course_end <= course_end
        )
    
    # 排序選項
    sort_options = {
        'course_number': Course.course_number,
        'title': Course.title,
        'enrollment_status': db.case(
            (Course.signup_start > db.func.now(), '1'),
            (Course.signup_deadline < db.func.now(), '3'),
            (Course.current_attendance >= Course.max_attendance, '4'),
            else_='2'
        ),
        'current_attendance': db.func.count(Application.application_number),
        'course_start': Course.course_start,
        'signup_start': Course.signup_start,
        'create_at': Course.create_at
    }
    
    if sort_by in ['current_attendance', 'enrollment_status']:
        query = query.outerjoin(Application).group_by(Course.course_number)
    
    sort_column = sort_options.get(sort_by, Course.create_at)
    if order == 'desc':
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'courses/manage2.html',
        courses=pagination.items,
        pagination=pagination,
        search=search,
        sort_by=sort_by,
        order=order,
        signup_start=signup_start,
        signup_end=signup_end,
        course_start=course_start,
        course_end=course_end,
        search_type=search_type
    )

@courses.route('/create', methods=['GET', 'POST'])
@login_required
@agency_required
def create_course():
    """創建新課程"""
    form = CourseForm()
    


    if form.validate_on_submit():

     
        signup_start = form.signup_start.data
        signup_deadline = form.signup_deadline.data
        # 存入資料庫前轉換為 UTC
        signup_start_utc = signup_start.astimezone(pytz.UTC)
        signup_deadline_utc = signup_deadline.astimezone(pytz.UTC)


        try:


            course = Course(
                signup_start=signup_start_utc,
                signup_deadline=signup_deadline_utc,
                max_attendance=form.max_attendance.data,
                course_start=form.course_start.data,
                course_end=form.course_end.data,
                hours=form.hours.data,
                location=form.location.data,
                title=form.title.data,
                intro=form.intro.data,
                description=form.description.data,
                department_id=current_user.department_id,
                create_at=datetime.now(timezone.utc),
                update_at=datetime.now(timezone.utc)
            )
            
            db.session.add(course)
            db.session.commit()
                 
            flash('課程創建成功！', 'success')
            return redirect(url_for('courses.view_course', course_number=course.course_number))
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"建立課程時發生錯誤: {str(e)}")
            raise
  
    
    return render_template('courses/create2.html', form=form)


@courses.route('/<int:course_number>')
def view_course(course_number):
    """查看課程詳情"""
    # 獲取課程資訊
    course = Course.query.get_or_404(course_number)
    
    # 當前時間
    

    now = datetime.now(timezone.utc)
    
    # 初始化變數
    application = None
    is_enrolled = False
    can_sign_in = False
    can_manage = False
    can_enroll = False
    enrolled_users = None
    total_users = None
    signed_in_users = None
    
    # 檢查用戶是否已登入
    if current_user.is_authenticated:
        # 檢查報名和簽到狀態
        application = Application.get_user_application(
            current_user.employee_number,
            course_number
        )
        
        # 檢查是否已報名
        is_enrolled = application is not None
        
        # 檢查是否可以簽到
        if application:
            can_sign_in = application.can_sign_in(now)
            
        # 檢查管理權限
        can_manage = course.can_manage(current_user)
        
        # 檢查是否可以報名
        signup_start = course.get_signup_start_utc()
        signup_deadline = course.get_signup_deadline_utc()
        can_enroll = (
            course.can_enroll() and 
            not is_enrolled and 
            signup_start <= now <= signup_deadline
        )
        
        # 如果是管理者，獲取報名學員列表
        if can_manage:
            enrolled_users = (
                Application.query
                .filter_by(course_number=course_number)
                .join(Application.user)
                .order_by(Application.create_at)
                .all()
            )
            
            # 計算簽到統計
            total_users = len(enrolled_users) if enrolled_users else 0
            signed_in_users = sum(1 for app in enrolled_users if app.sign_in_state) if enrolled_users else 0
            
    # 獲取相關課程推薦
    related_courses = (
        Course.query
        .filter(
            Course.department_id == course.department_id,
            Course.course_number != course.course_number,
            Course.signup_deadline >= now
        )
        .order_by(Course.signup_start)
        .limit(3)
        .all()
    )
    
    # 取得課程狀態
    course_status = course.get_status(now)
    
    return render_template(
        'courses/view2.html',
        course=course,
        application=application,
        is_enrolled=is_enrolled,
        can_sign_in=can_sign_in,
        can_manage=can_manage,
        can_enroll=can_enroll,
        enrolled_users=enrolled_users,
        related_courses=related_courses,
        course_status=course_status,
        total_users=total_users,
        signed_in_users=signed_in_users,
        now=now
    )



@courses.route('/<int:course_number>/edit', methods=['GET', 'POST'])
@login_required
@agency_required
def edit_course(course_number):
    """編輯課程"""
    course = Course.query.get_or_404(course_number)
    
    if not course.can_manage(current_user):
        flash('您沒有權限編輯此課程', 'error')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    form = CourseForm(obj=course)
    
    if form.validate_on_submit():
        try:
            # 檢查時間邏輯
            if form.signup_deadline.data <= form.signup_start.data:
                flash('報名截止時間必須晚於報名開始時間', 'error')
                return render_template('courses/edit.html', form=form, course=course)
            
            if form.course_end.data < form.course_start.data:
                flash('課程結束日期必須晚於或等於開始日期', 'error')
                return render_template('courses/edit.html', form=form, course=course)
            
            # 更新課程

            course.update_course(form)
            flash('課程更新成功！', 'success')
            return redirect(url_for('courses.view_course', course_number=course_number))
            
        except Exception as e:
            flash('課程更新失敗，請稍後再試。錯誤: {}'.format(str(e)), 'error')
            return render_template('courses/edit.html', form=form, course=course)
    
    # GET 請求或表單驗證失敗
    return render_template('courses/edit.html', form=form, course=course)



@courses.route('/<int:course_number>/sign_in', methods=['POST'])
@login_required
def course_sign_in(course_number):
    """課程簽到"""

    # 當前時間
    now = datetime.now(timezone.utc)

    application = Application.get_user_application(
        current_user.employee_number, 
        course_number
    )
    
    if not application:
        flash('您尚未報名此課程', 'error')
        return redirect(url_for('courses.view_course', course_number=course_number))
        
    if application.sign_in_state:
        flash('您已經完成簽到', 'info')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    current_date = datetime.now(timezone.utc)
    if not application.can_sign_in(current_date):
        flash('目前不在課程期間內，無法簽到', 'error')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    try:
        application.sign_in_state = True
        application.sign_in_time = now
        db.session.commit()
        flash('簽到成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash('簽到失敗，請稍後再試', 'error')
        current_app.logger.error(f'Sign in failed: {str(e)}')
    
    return redirect(url_for('courses.view_course', course_number=course_number))


@courses.route('/<int:course_number>/delete', methods=['POST'])
@login_required
@agency_required
def delete_course(course_number):
    """刪除課程"""
    course = Course.query.get_or_404(course_number)
    
    if not course.can_manage(current_user):
        flash('您沒有權限刪除此課程', 'error')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    # 檢查是否已有人報名
    if course.current_attendance > 0:
        flash('已有人報名的課程無法刪除', 'error')
        return redirect(url_for('courses.view_course', course_number=course_number))
    
    try:
        course.delete_course()
        flash('課程已成功刪除', 'success')
        return redirect(url_for('courses.manage_courses'))
    except Exception as e:
        current_app.logger.error(f'Course deletion failed: {str(e)}')
        flash('課程刪除失敗，請稍後再試', 'error')
        return redirect(url_for('courses.view_course', course_number=course_number))




@courses.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('表單已過期，請重新提交', 'error')
    return redirect(request.full_path)


@courses.route('/mycourses')  
@login_required
def mycourses():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('COURSES_PER_PAGE', 10)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'course_start')
    order = request.args.get('order', 'desc')
    department_id = request.args.get('department_id', type=int)  # 改用 department_id
    search_type = request.args.get('search_type')
    show_history = request.args.get('show_history', '0') == '1'  # 移除自動切換邏輯

    # 獲取所有開課單位
    departments = Department.query.order_by(
        Department.section_name, 
        Department.subsection_name
    ).all()

    # 日期區間搜尋參數
    course_start = request.args.get('course_start')
    course_end = request.args.get('course_end')
    
    now = datetime.now(timezone.utc).date()
    
    # 基礎查詢
    query = Course.query.join(Application)\
        .filter(Application.employee_number == current_user.employee_number)
    
    # 根據頁籤篩選
    if show_history:
        query = query.filter(Course.course_end < now)
        query = query.order_by(Course.course_end.desc())
    else:
        query = query.filter(Course.course_end >= now)

    # 開課單位篩選
    if department_id:
        query = query.filter(Course.department_id == department_id)

    # 搜尋條件
    if search_type == 'keyword' and search:
        query = query.filter(Course.title.ilike(f'%{search}%'))
    elif search_type == 'course' and course_start and course_end:
        query = query.filter(
            Course.course_start >= course_start,
            Course.course_end <= course_end
        )
    
    # 排序選項
    sort_options = {
        'course_number': Course.course_number,
        'title': Course.title,
        'course_start': Course.course_start,
        'create_at': Course.create_at
    }
    
    sort_column = sort_options.get(sort_by, Course.course_start)
    if order == 'desc':
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return render_template(
        'courses/mycourse.html',
        courses=pagination.items,
        pagination=pagination,
        departments=departments,  # 傳遞所有開課單位
        department_id=department_id,  
        search=search,
        sort_by=sort_by,
        order=order,
        course_start=course_start,
        course_end=course_end,
        search_type=search_type,
        show_history=show_history
    )