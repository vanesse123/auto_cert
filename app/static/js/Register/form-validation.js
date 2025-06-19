
/*

// input.(in)valid css
var inputs = document.querySelectorAll('input')
inputs.forEach( input => {
  input.addEventListener('input', function(){
      if(input.checkValidity()){
        input.classList.add('valid')
        input.classList.remove('invalid')
      }else{
        input.classList.remove('valid')
        input.classList.add('invalid')
      }
  })
})

*/








/*

//表單提交驗證

$(document).ready(function() {


  $('#registerForm').submit(function(e) {
      e.preventDefault(); // 阻止表單提交的默認行為

      var formData = $(this).serialize(); // 獲取表單數據

      $.ajax({
          url: '/register',
          method: 'POST',
          data: formData,
          success: function(response) {
              if (response.success) {
                  alert('註冊成功!');
              } else {
                  alert('註冊失敗: ' + response.error);
              }
          },
          error: function() {
              alert('發生錯誤，請稍後再試。');
          }
      });
    });
});

*/