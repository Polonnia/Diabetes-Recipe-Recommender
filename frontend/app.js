$(document).ready(function () {
    // 处理用户健康信息提交
    $("#user-data-form").submit(function (e) {
        e.preventDefault();

        // 获取用户健康数据
        const userData = {
            height: $("#height").val(),
            weight: $("#weight").val(),
            age: $("#age").val(),
            gender: $("#gender").val(),
            pre_meal_glucose: $("#pre-meal-glucose").val(),
            pre_meal_insulin: $("#pre-meal-insulin").val(),
        };

        // 发送到后端（模拟）
        $.ajax({
            url: "/get_recipe_recommendation", // 后端处理接口
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(userData),
            success: function (response) {
                // 显示推荐食谱
                displayRecipes(response.recipes);
                $("#recipe-recommendation").show();
            },
            error: function () {
                alert("提交失败，请稍后再试。");
            }
        });
    });

    // 处理用户食谱评分和餐后血糖反馈
    $("#submit-feedback").click(function () {
        const rating = $("#rating").val();
        const postMealGlucose = $("#post-meal-glucose").val().split(',').map(item => item.trim());

        // 获取用户健康数据及推荐的食谱营养成分（模拟）
        const preMealGlucose = $("#pre-meal-glucose").val();
        const recipeNutrition = {
            carb: 30,
            protein: 15,
            fat: 10,
            fiber: 5,
        };

        // 将数据发送给后端进行存储（模拟）
        $.ajax({
            url: "/store_feedback", // 后端处理接口
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                rating: rating,
                pre_meal_glucose: preMealGlucose,
                recipe_nutrition: recipeNutrition,
                post_meal_glucose_60: postMealGlucose[0],
                post_meal_glucose_120: postMealGlucose[1],
                post_meal_glucose_180: postMealGlucose[2],
            }),
            success: function () {
                alert("感谢您的反馈！");
            },
            error: function () {
                alert("反馈提交失败，请稍后再试。");
            }
        });
    });
});

// 显示推荐食谱
function displayRecipes(recipes) {
    const recipeList = $("#recommended-recipes");
    recipeList.empty();

    recipes.forEach(function (recipe) {
        recipeList.append(`
            <div class="card mt-3">
                <div class="card-body">
                    <h5 class="card-title">${recipe.name}</h5>
                    <p class="card-text">${recipe.description}</p>
                </div>
            </div>
        `);
    });
}
