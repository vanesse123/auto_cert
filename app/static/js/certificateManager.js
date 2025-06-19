// 1. 類別定義和建構子
class CertificateManager {
    // 當創建類別實例時，會執行建構子
    constructor() {
        // 初始化時執行兩個主要設置方法
        this.initializeElements();  // 先獲取所有需要的 DOM 元素
        this.setupEventListeners(); // 再設置事件監聽器
    }

    // 2. 初始化所有需要的 DOM 元素
    initializeElements() {
        // 使用 document.getElementById 和 querySelectorAll 獲取頁面上的元素
        // 並將它們存為類別的屬性，方便後續使用
        this.filterForm = document.getElementById('filterForm');           // 篩選表單
        this.selectAllCheckbox = document.getElementById('selectAll');     // 全選核取方塊
        this.issueForm = document.getElementById('issueForm');            // 發放證書表單
        this.studentCheckboxes = document.querySelectorAll('.student-checkbox'); // 所有學員的核取方塊
        this.selectedCount = document.getElementById('selectedCount');     // 顯示已選擇數量的元素
        this.alertContainer = document.getElementById('alertContainer');   // 提示訊息容器
    }

    // 3. 設置所有需要的事件監聽器
    setupEventListeners() {
        // 為發放證書表單添加提交事件監聽
        if (this.issueForm) {
            this.issueForm.addEventListener('submit', (e) => this.handleIssueSubmit(e));
        }

        // 為全選核取方塊添加變更事件監聽
        if (this.selectAllCheckbox) {
            // 監聽全選核取方塊的變更
            this.selectAllCheckbox.addEventListener('change', () => this.handleSelectAll());
            
            // 為每個學員的核取方塊添加變更事件監聽
            this.studentCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', () => this.updateSelectedCount());
            });
        }

        // 為篩選表單添加提交事件監聽
        if (this.filterForm) {
            this.filterForm.addEventListener('submit', (e) => this.handleFilterSubmit(e));
        }
    }

    // 4. 處理發放證書表單提交
    handleIssueSubmit(e) {
        // 獲取所有已選擇的學員核取方塊
        const selectedStudents = document.querySelectorAll('.student-checkbox:checked');
        
        // 如果沒有選擇任何學員
        if (selectedStudents.length === 0) {
            e.preventDefault();  // 阻止表單提交
            this.showMessage('請選擇至少一位學員', 'warning');  // 顯示警告訊息
            return;
        }

        // 顯示確認對話框
        if (!confirm('確定要發放所選學員的證書嗎？')) {
            e.preventDefault();  // 如果用戶選擇取消，阻止表單提交
        }
        // 如果用戶確認，表單會正常提交
    }

    handleSelectAll() {
        // 修正：只選擇未禁用的核取方塊
        const availableCheckboxes = Array.from(this.studentCheckboxes).filter(checkbox => !checkbox.disabled);
        availableCheckboxes.forEach(checkbox => {
            checkbox.checked = this.selectAllCheckbox.checked;
        });
        this.updateSelectedCount();
    }
    
    updateSelectedCount() {
        // 更新選取計數
        const selectedCount = document.querySelectorAll('.student-checkbox:checked').length;
        if (this.selectedCount) {
            this.selectedCount.textContent = `已選擇 ${selectedCount} 位學員`;
        }
    
        // 更新全選核取方塊狀態
        const availableCheckboxes = Array.from(this.studentCheckboxes).filter(checkbox => !checkbox.disabled);
        this.selectAllCheckbox.checked = selectedCount === availableCheckboxes.length && availableCheckboxes.length > 0;
    }

    showMessage(message, type = 'info') {
        if (!this.alertContainer) return;

        const alert = document.createElement('div');
        const alertClasses = {
            success: 'bg-green-100 text-green-800',
            error: 'bg-red-100 text-red-800',
            warning: 'bg-yellow-100 text-yellow-800',
            info: 'bg-blue-100 text-blue-800'
        };

        alert.className = `p-4 rounded-lg shadow-lg mb-4 ${alertClasses[type] || alertClasses.info}`;
        alert.textContent = message;

        this.alertContainer.appendChild(alert);
        setTimeout(() => alert.remove(), 3000);
    }
}

// 初始化

document.addEventListener('DOMContentLoaded', () => {
    window.certificateManager = new CertificateManager();
});