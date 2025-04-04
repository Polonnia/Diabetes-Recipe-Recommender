$(document).ready(function () {
    // 提交健康信息
    $("#user-data-form").on("submit", function (e) {
        e.preventDefault();
        
        const userData = {
            height: $("#height").val(),
            weight: $("#weight").val(),
            age: $("#age").val(),
            gender: $("#gender").val(),
            pre_meal_glucose: $("#pre-meal-glucose").val(),
            pre_meal_insulin: $("#pre-meal-insulin").val(),
            activity_level: $("#activity-level").val(),
        };

        // 发送到后端
        $.ajax({
            url: "/api/user-data",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(userData),
            success: function (response) {
                // 显示成功消息
                const alertHtml = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        ${response.message}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
                $("#user-data-form").prepend(alertHtml);
                
                // 3秒后自动移除提示
                setTimeout(() => {
                    $(".alert").alert('close');
                }, 3000);
            },
            error: function (error) {
                // 显示错误消息
                const alertHtml = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        保存失败，请稍后重试
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                `;
                $("#user-data-form").prepend(alertHtml);
            }
        });
    });
}); 