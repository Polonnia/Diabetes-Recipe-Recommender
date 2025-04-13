$(document).ready(function () {
    // 从 localStorage 加载数据
    let userData = JSON.parse(localStorage.getItem('userData')) || {
        height: 165.0,
        weight: 55.0,
        age: 25,
        gender: "female",
        pre_meal_glucose: 5.0,
        pre_meal_insulin: 0,
        activity_level: "moderately_active",
        TDEE: 1600
    };

    // 填充表单数据
    $("#height").val(userData.height);
    $("#weight").val(userData.weight);
    $("#age").val(userData.age);
    $("#gender").val(userData.gender);
    $("#pre-meal-glucose").val(userData.pre_meal_glucose);
    $("#pre-meal-insulin").val(userData.pre_meal_insulin);
    $("#activity-level").val(userData.activity_level);

    // 计算TDEE
    function calculateTDEE(userData) {
        // 基础代谢率(BMR)计算 - 使用Harris-Benedict公式
        let bmr;
        if (userData.gender === "male") {
            bmr = 88.362 + (13.397 * userData.weight) + (4.799 * userData.height) - (5.677 * userData.age);
        } else {
            bmr = 447.593 + (9.247 * userData.weight) + (3.098 * userData.height) - (4.330 * userData.age);
        }

        // 根据活动水平计算TDEE
        const activityFactors = {
            sedentary: 1.2,         // 久坐少动
            lightly_active: 1.375,   // 轻度活动
            moderately_active: 1.55, // 中度活动
            very_active: 1.725,      // 高度活动
            extra_active: 1.9        // 极度活动
        };

        return Math.round(bmr * activityFactors[userData.activity_level]);
    }

    // 计算每餐营养素需求量
    function calculateNutrientNeeds(TDEE) {
        // 营养比例
        const carb_ratio = 0.5;  // 碳水50%
        const protein_ratio = 0.2;  // 蛋白质20%
        const fat_ratio = 0.3;  // 脂肪30%

        // 每克营养素的卡路里
        const carb_calories_per_gram = 4;
        const protein_calories_per_gram = 4;
        const fat_calories_per_gram = 9;

        // 三餐能量分配比例
        const meal_ratios = {
            breakfast: 0.3,
            lunch: 0.4,
            dinner: 0.3
        };

        // 计算每餐的营养素需求量（克）
        const nutrient_needs = {};
        for (const [meal, ratio] of Object.entries(meal_ratios)) {
            const meal_energy = TDEE * ratio;
            nutrient_needs[meal] = {
                carb: Math.round(meal_energy * carb_ratio / carb_calories_per_gram),
                protein: Math.round(meal_energy * protein_ratio / protein_calories_per_gram),
                fat: Math.round(meal_energy * fat_ratio / fat_calories_per_gram)
            };
        }

        return nutrient_needs;
    }

    // 提交健康信息
    $("#user-data-form").on("submit", function (e) {
        e.preventDefault();
        
        const formData = {
            height: parseFloat($("#height").val()),
            weight: parseFloat($("#weight").val()),
            age: parseInt($("#age").val()),
            gender: $("#gender").val(),
            pre_meal_glucose: parseFloat($("#pre-meal-glucose").val()),
            pre_meal_insulin: parseInt($("#pre-meal-insulin").val()),
            activity_level: $("#activity-level").val(),
        };

        // 验证输入
        if (isNaN(formData.height) || formData.height <= 0) {
            alert("请输入有效的身高值");
            return;
        }
        if (isNaN(formData.weight) || formData.weight <= 0) {
            alert("请输入有效的体重值");
            return;
        }
        if (isNaN(formData.pre_meal_glucose) || formData.pre_meal_glucose <= 0) {
            alert("请输入有效的餐前血糖值");
            return;
        }

        // 计算并添加TDEE和营养素需求
        const TDEE = calculateTDEE(formData);
        const nutrient_needs = calculateNutrientNeeds(TDEE);
        const userData = {
            ...formData,
            TDEE: TDEE,
            nutrient_needs: nutrient_needs
        };

        // 保存到 localStorage
        localStorage.setItem('userData', JSON.stringify(userData));

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