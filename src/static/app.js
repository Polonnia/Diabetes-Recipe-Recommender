$(document).ready(function () {
    // 默认健康信息
    let userData = {
        height: 165,
        weight: 120,
        age: 25,
        gender: "female",
        pre_meal_glucose: 5,
        pre_meal_insulin: 0,
        activity_level: "moderately_active",
        TDEE: 1600
    };

    // 历史记录数组
    let history = [];

    // 显示/隐藏加载动画
    function toggleLoading(show) {
        if (show) {
            $("#loading").fadeIn();
        } else {
            $("#loading").fadeOut();
        }
    }

    // 添加历史记录
    function addHistoryItem(data) {
        const now = new Date();
        const timeString = now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });

        const historyItem = {
            time: timeString,
            mealType: data.meal_type,
            recipes: data.recommendations,
            stats: {
                healthScore: data.health_score,
                predictedGlucose: data.PBG,
                carb: data.carb,
                protein: data.protein,
                fat: data.fat,
                fiber: data.fiber
            }
        };

        history.unshift(historyItem);
        updateHistoryDisplay();
    }

    // 更新历史记录显示
    function updateHistoryDisplay() {
        const historyList = $("#history-list");
        historyList.empty();

        history.forEach((item, index) => {
            const mealTypeClass = {
                'breakfast': 'breakfast',
                'lunch': 'lunch',
                'dinner': 'dinner'
            }[item.mealType] || '';

            const historyItem = $(`
                <div class="history-item" data-index="${index}">
                    <div class="history-time">${item.time}</div>
                    <div class="history-meal-type ${mealTypeClass}">
                        ${item.mealType === 'breakfast' ? '早餐' : 
                          item.mealType === 'lunch' ? '午餐' : '晚餐'}
                    </div>
                    <div class="history-recipes">
                        ${item.recipes.map(recipe => `
                            <div class="history-recipe">
                                <span class="history-recipe-name">${recipe}</span>
                                <span class="history-recipe-rating" data-recipe="${recipe}">
                                    <i class="far fa-star"></i>
                                </span>
                            </div>
                        `).join('')}
                    </div>
                    <div class="history-stats">
                        <div class="history-stat">
                            <span class="history-stat-label">健康评分</span>
                            <span class="history-stat-value">${item.stats.healthScore.toFixed(2)}</span>
                        </div>
                        <div class="history-stat">
                            <span class="history-stat-label">预测血糖</span>
                            <span class="history-stat-value">${item.stats.predictedGlucose.toFixed(1)}</span>
                        </div>
                        <div class="history-stat">
                            <span class="history-stat-label">碳水</span>
                            <span class="history-stat-value">${item.stats.carb.toFixed(1)}g</span>
                        </div>
                        <div class="history-stat">
                            <span class="history-stat-label">蛋白质</span>
                            <span class="history-stat-value">${item.stats.protein.toFixed(1)}g</span>
                        </div>
                        <div class="history-stat">
                            <span class="history-stat-label">脂肪</span>
                            <span class="history-stat-value">${item.stats.fat.toFixed(1)}g</span>
                        </div>
                        <div class="history-stat">
                            <span class="history-stat-label">纤维</span>
                            <span class="history-stat-value">${item.stats.fiber.toFixed(1)}g</span>
                        </div>
                    </div>
                </div>
            `);

            historyList.append(historyItem);
        });

        // 绑定评分点击事件
        $(".history-recipe-rating").click(function() {
            const recipeName = $(this).data("recipe");
            showRatingModal(recipeName);
        });
    }

    // 显示评分模态框
    function showRatingModal(recipeName) {
        $("#recipe-name").text(recipeName);
        $("#rating-stars").rateYo({
            rating: 0,
            starWidth: "30px",
            fullStar: true
        });
        $("#ratingModal").modal("show");
    }

    // 提交评分
    $("#submit-rating").click(function() {
        const recipeName = $("#recipe-name").text();
        const rating = $("#rating-stars").rateYo("rating");
        
        // 发送评分到后端
        $.ajax({
            url: "/update_pref",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                recipe: recipeName,
                rating: rating
            }),
            success: function(response) {
                $("#ratingModal").modal("hide");
                // 更新星星显示
                $(`.history-recipe-rating[data-recipe="${recipeName}"]`).html(
                    `<i class="fas fa-star"></i>`
                );
            },
            error: function(error) {
                console.error("评分提交失败：", error);
                alert("评分提交失败，请重试");
            }
        });
    });

    // 发送消息
    $("#send-message").on("click", function () {
        const message = $("#chat-input").val();
        if (!message) return;

        // 显示用户消息
        appendMessage("user", message);
        $("#chat-input").val("");

        // 显示加载动画
        toggleLoading(true);

        // 发送到后端
        $.ajax({
            url: "https://dominant-bunny-feasible.ngrok-free.app/chat",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                message: message,
                user_data: userData
            }),
            success: function (response) {
                // 使用 marked 渲染 markdown
                const renderedMessage = marked.parse(response.message);
                appendMessage("bot", renderedMessage);

                // 如果是食谱推荐，添加到历史记录
                if (response.recommendations && response.meal_type) {
                    addHistoryItem(response);
                }
            },
            error: function (error) {
                console.error("请求失败：", error);
                appendMessage("bot", "请求失败，请稍后重试。");
            },
            complete: function() {
                // 隐藏加载动画
                toggleLoading(false);
            }
        });
    });

    // 添加消息到聊天框
    function appendMessage(role, message) {
        const bubbleClass = role === "user" ? "user-bubble" : "bot-bubble";
        const bubble = `<div class="chat-bubble ${bubbleClass}">${message}</div>`;
        $("#chat-container").append(bubble);
        $("#chat-container").scrollTop($("#chat-container")[0].scrollHeight);
    }

    // 按回车发送消息
    $("#chat-input").on("keypress", function (e) {
        if (e.which === 13) {
            $("#send-message").click();
        }
    });

    // 输入框获得焦点时显示提示
    $("#chat-input").on("focus", function() {
        $(this).attr("placeholder", "例如：请推荐一些适合糖尿病患者的早餐食谱");
    }).on("blur", function() {
        $(this).attr("placeholder", "请输入您的问题...");
    });

    // 添加输入建议
    const suggestions = [
        "请推荐一些适合糖尿病患者的早餐食谱",
        "糖尿病患者可以吃水果吗？",
        "如何控制血糖？",
        "推荐一些低糖的零食",
        "运动对糖尿病有什么好处？"
    ];

    let currentSuggestion = 0;
    setInterval(function() {
        $("#chat-input").attr("placeholder", suggestions[currentSuggestion]);
        currentSuggestion = (currentSuggestion + 1) % suggestions.length;
    }, 3000);
});