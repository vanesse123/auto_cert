/*
$(document).ready(function() {
 
    $('#section_name').change(function() {
        var sectionName = $(this).val();  
        console.log("Selected section_name: " + sectionName);  // 調試用
        // 發送 AJAX 請求
        $.ajax({
            url: '/subsections/' + sectionName,
            method: 'GET',
            success: function(data) {
                console.log("Received subsections: ", data);  // 調試用
            },
            error: function(xhr, status, error) {
                console.log("AJAX error: ", error);  // 調試用
            }
            });
        });
});
*/
/*
$(document).ready(function() {
    // 監聽 section_name 的選擇變化
    $('#section_name').change(function() {
        var sectionName = $(this).val();  // 取得 section_name 的值

        // 發送 AJAX 請求以獲取對應的 subsection_name
        $.ajax({
            url: '/subsections/' + sectionName,
            method: 'GET',
            success: function(data) {
                var subsectionSelect = $('#subsection_name');
                subsectionSelect.empty();  // 清空現有的選項

                // 動態添加新的 subsection_name 選項
                $.each(data, function(index, value) {
                    subsectionSelect.append('<option value="' + value[0] + '">' + value[1] + '</option>');
                });
            }
        });
    });
});

*/
$(document).ready(function() {
    // 初始化部門欄位顯示
    toggleFieldDisplay();

    // 監聽部門選擇變化
    $('#section_name').change(function() {
        if ($('input[name="role"]:checked').val() === 'agency') {
            updateSubsections($(this).val());
        }
    });
});

const form = document.getElementById('registerForm');
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const jsonData = {};

    // 轉換 FormData 為普通對象
    formData.forEach((value, key) => {
        if (form.elements[key].type === 'checkbox' || form.elements[key].type === 'radio') {
            if (form.elements[key].checked) {
                jsonData[key] = value;
            }
        } else {
            jsonData[key] = value;
        }
    });

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify(jsonData)
        });

        const data = await response.json();

        if (data.status === 'success') {
            const modal = new bootstrap.Modal(document.getElementById('resultModal'));
            document.querySelector('.modal-title').textContent = data.title;
            document.querySelector('.modal-message').textContent = data.message;
            modal.show();

            document.getElementById('confirmRedirect').onclick = () => {
                window.location.href = '/login';
            };
        } else {
            const modal = new bootstrap.Modal(document.getElementById('resultModal'));
            document.querySelector('.modal-title').textContent = data.title || '錯誤';
            document.querySelector('.modal-message').textContent = data.message;
            document.getElementById('confirmRedirect').onclick = () => modal.hide();
            modal.show();
        }
    } catch (error) {
        console.error('Error:', error);
        const modal = new bootstrap.Modal(document.getElementById('resultModal'));
        document.querySelector('.modal-title').textContent = '錯誤';
        document.querySelector('.modal-message').textContent = '發生錯誤，請稍後重試';
        document.getElementById('confirmRedirect').onclick = () => modal.hide();
        modal.show();
    }
});

function toggleFieldDisplay() {
    const role = document.querySelector('input[name="role"]:checked').value;
    const agencyFields = document.getElementById('agencyFields');
    agencyFields.style.display = (role === 'agency') ? 'block' : 'none';
}

function updateSubsections(sectionName) {
    $.ajax({
        url: '/subsections/' + sectionName,
        method: 'GET',
        beforeSend: function() {
            // 顯示加載指示器
            $('#loadingIndicator').show();
        },
        success: function(data) {
            const subsectionSelect = $('#subsection_name');
            subsectionSelect.empty();

            data.forEach(([value, text]) => {
                subsectionSelect.append(
                    $('<option>', { value: value }).text(text)
                );
            });
        },
        error: function(xhr, status, error) {
            console.log("AJAX error: ", error);
            toastr.error('無法獲取子部門資料，請稍後再試。');
        },
        complete: function() {
            // 隱藏加載指示器
            $('#loadingIndicator').hide();
        }
    });
}