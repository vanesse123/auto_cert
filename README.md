## 基本設定
### .env & config.py
  資料庫設定記得設定(user、password、host、port、DBname)
### migrations
  'flask db upgrade'直接更改資料庫結構
  
  **如果有更改app/models.py的話**
  
  'flask db migrate -m "your message"'記得產生新的mifrations
  'flask db upgrade'並更新資料庫結構
## 登入網站後注意事項
  記得先註冊，有分為使用者跟管理者
  
  登入及註冊
  > (1)網站右上可進行登入。
  > (2)第一次使用請先註冊帳號，點擊下方的“立即註冊”即可註冊。

  **注意:管理者記得選擇正確的單位(部門、子部門)**
  
  如何登出?
  > 點擊右上方“您的帳號名稱”，即可看到登出按鈕
  #### 一、使用者操作指南
  1.想要查看目前有哪些課程可以報名?
  > 點擊上方的“課程總覽”，即可查看當前課程，點擊課程右方的“查看”可看到更詳細的資訊及報名按鈕。

  2.想要查看目前報名那些課程?
  > 點擊上方的“我的課程”即可查看，點擊課程右方的“查看”可看到更詳細的資訊及簽到按鈕。
  
  3.想要查目前有哪些證書?
  > 點擊上方的“我的證書”即可查看。

  4.如何下載證書?
  > 在“我的證書”中，點擊你要下載的證書右方的“檢視”按鈕，即可下載。
  #### 二、管理者操作指南
  1.如何建立課程?
  > 點擊上方的活動管理-建立課程，即可建立。

  2.如何管理自己建立的課程?
  > 點擊上方的活動管理-課程管理，即可看到您建立的各項課程，點擊各項課程右方的“編輯”按鈕，可修改課程的各項資訊;點擊“查看”按鈕，即可看到課程內容和報名者的簽到資訊。

  3.如何核發證書?
  > 點擊上方的活動管理-核發證書，即可看到可核發的證書，確認過後，點擊核發即可送出證書。
  
